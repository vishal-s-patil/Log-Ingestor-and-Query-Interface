import json
from django.utils import timezone
from django.shortcuts import render, HttpResponse
from django.views import View
from rest_framework import generics
from .models import LogEntry
from .serializers import LogEntrySerializer
from dotenv import load_dotenv
import os
import boto3
import threading
import time


load_dotenv()


def test_view(request):
    s3 = boto3.resource('s3')
    for bucket in s3.buckets.all():
        print('bucket.name', bucket.name)
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
        client = boto3.client('sqs', region_name="eu-north-1")

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

                client = boto3.client('sqs', region_name="eu-north-1")
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
                        # process_message(message)
                        print("message from sqs : ", message)
                        # Delete the processed message
                        receipt_handle = message['ReceiptHandle']
                        client.delete_message(
                            QueueUrl=sqs_queue_url,
                            ReceiptHandle=receipt_handle
                        )
                time.sleep(15)
        except Exception as e:
            print(f"Error processing messages: {e}")

