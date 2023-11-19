import json
import requests
from django.utils import timezone
from django.shortcuts import render, HttpResponse
from django.views import View
from rest_framework import generics
from .models import LogEntry
from .serializers import LogEntrySerializer
from dotenv import load_dotenv
import os
import psycopg2
import boto3
import threading
import time
from elasticsearch import Elasticsearch
from datetime import datetime


load_dotenv()

access_key = os.getenv('AWS_ACCESS_KEY')
secret_access_key = os.getenv('AWS_SECRET_KEY')
elasticsearch_url = "http://elasticsearch:9200/logs/_doc"

db_params = {
    'dbname': 'logingestor',
    'user': 'admin',
    'password': 'patil9922',
    'host': 'localhost',
    'port': '5432',
}

def test_view(request):
    # s3 = boto3.resource('s3')
    # for bucket in s3.buckets.all():
    #     print('bucket.name', bucket.name)
    print('keys', access_key, secret_access_key)
    return HttpResponse("Hello, this is the 'test' view!")


class LogEntryCreateView(generics.ListCreateAPIView):
    queryset = LogEntry.objects.all()
    serializer_class = LogEntrySerializer

    class_data = []

    def perform_create(self, serializer):
        instance = serializer.save()
        timestamp_str = timezone.localtime(instance.timestamp).isoformat()
        message_data = {
            "level": instance.level,
            "message": instance.message,
            "resourceId": instance.resourceId,
            "timestamp": timestamp_str,
            "traceId": instance.traceId,
            "spanId": instance.spanId,
            "commit": instance.commit,
            "metadata-parentResourceId": instance.metadata['parentResourceId']
        }
        # print('instance', instance)
        # print('message_data', message_data)
        # access_key = os.getenv('AWS_ACCESS_KEY')
        # secret_key = os.getenv('AWS_SECRET_KEY')
        # console_password = os.getenv('CONSOLE_PASSWORD')
        sqs_queue_url = os.getenv('SQS_URL')
        # print('secret_key', secret_key)
        client = boto3.client('sqs', aws_access_key_id=access_key, aws_secret_access_key=secret_access_key, region_name="eu-north-1")

        response = client.send_message(
            QueueUrl=sqs_queue_url,
            MessageBody=json.dumps(message_data)
        )

        print("Message sent to SQS. Response:", response)

        self.__class__.class_data.append(instance)


class SQSConsumerView(View):
    def get(self, request, *args, **kwargs):
        # Start a background thread to consume messages
        background_thread = threading.Thread(target=self.consume_messages)
        background_thread.start()

        return HttpResponse("Background thread started for SQS consumer.")

    def consume_messages(self):
        try:
            while True:
                print("Fetching and processing SQS messages...")

                client = boto3.client('sqs', aws_access_key_id=access_key, aws_secret_access_key=secret_access_key, region_name="eu-north-1")
                sqs_queue_url = os.getenv('SQS_URL')
                response = client.receive_message(
                    QueueUrl=sqs_queue_url,
                    AttributeNames=['All'],
                    MessageAttributeNames=['All'],
                    MaxNumberOfMessages=10,
                    VisibilityTimeout=0,
                    WaitTimeSeconds=5
                )

                messages = response.get('Messages', [])
                if messages:
                    for message in messages:
                        # Process the message
                        json_data = json.loads(message["Body"])
                        self.process_message(json_data)
                        print("message from sqs : ", json_data)
                        # Delete the processed message
                        receipt_handle = message['ReceiptHandle']
                        client.delete_message(
                            QueueUrl=sqs_queue_url,
                            ReceiptHandle=receipt_handle
                        )
                time.sleep(15)
        except Exception as e:
            print(f"Error processing messages: {e}")

    def process_message(self, message):
        # push to elastic search

        json_data = json.dumps(message)

        headers = {
            "Content-Type": "application/json",
        }

        response = requests.post(elasticsearch_url, data=json_data, headers=headers)

        if response.status_code == 201:
            print("Data successfully indexed in Elasticsearch.")
        else:
            print(f"Failed to index data. Status code: {response.status_code}, Response: {response.text}")

        # push to postgres

        connection = psycopg2.connect(**db_params)
        cursor = connection.cursor()

        insert_query = """
        INSERT INTO logs (level, message, resourceId, created_at, traceId, spanId, commit, metadata_parentResourceId)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """

        cursor.execute(insert_query, (message["level"], message["message"], message["resourceId"], message["timestamp"], message["traceId"], message["spanId"], message["commit"], message["metadata-parentResourceId"]))
        connection.commit()

        cursor.close()
        connection.close()


def search_logs(request):
    if request.method == 'GET':
        return render(request, 'index.html')
    else:
        level = request.POST.get('level')
        message = request.POST.get('message')
        resourceId = request.POST.get('resourceId')
        timestamp_start = request.POST.get('timestamp_start')
        timestamp_end = request.POST.get('timestamp_end')
        traceId = request.POST.get('traceId')
        spanId = request.POST.get('spanId')
        commit = request.POST.get('commit')
        metadata_parentResourceId = request.POST.get('metadata_parentResourceId')

        must = []

        if level != '':
            must.append({"match": {"level": level}})
        if resourceId != '':
            must.append({"match": {"resourceId": resourceId}})
        if traceId != '':
            must.append({"match": {"traceId": traceId}})
        if spanId != '':
            must.append({"match": {"spanId": spanId}})
        if commit != '':
            must.append({"match": {"commit": commit}})
        if metadata_parentResourceId != '':
            must.append({"match": {"metadata_parentResourceId": metadata_parentResourceId}})

        # print('must', must)
        # print(type(must[0]))

        if len(level) + len(resourceId) + len(traceId) + len(spanId) + len(commit) + len(metadata_parentResourceId) > 0:
            search_query = {
                "query": {
                    "bool": {
                        "must": must
                    }
                }
            }
        elif message != '':
            search_query = {
                "query": {
                    "match": {
                        "message": {
                            "query": message,
                            "operator": "and"  # or "phrase"
                        }
                    }
                }
            }
        elif len(timestamp_start) + len(timestamp_end) > 0:
            timestamp_start += ":00"
            timestamp_end += ":00"

            # Convert to ISO 8601 format
            iso_format1 = datetime.fromisoformat(timestamp_start).isoformat()
            iso_format2 = datetime.fromisoformat(timestamp_end).isoformat()
            # return render(request, 'index.html')
            search_query = {
                "query": {
                    "range": {
                        "timestamp": {
                            "gte": iso_format1,
                            "lte": iso_format2,
                            "format": "strict_date_optional_time"
                        }
                    }
                }
            }

        es = Elasticsearch(['http://elasticsearch:9200'])
        result = es.search(index='logs', body=search_query)
        # print('result', result)
        hits = result['hits']['hits']
        logs = []
        for hit in hits:
            source_data = hit['_source']
            logs.append(source_data)
            # print('source_data', source_data)
        print('logs', logs)
        context = {
            'logs': logs,
        }

        return render(request, 'index.html', context)

