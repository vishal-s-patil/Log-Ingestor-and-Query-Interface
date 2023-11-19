from django.urls import path, include
from . import views

app_name = 'ingestor'

urlpatterns = [
    path('logentries/', views.LogEntryCreateView.as_view(), name='logentry_create'),
    path('test/', views.test_view, name='test_view'),
    path('sqs_consumer/', views.SQSConsumerView.as_view(), name='sqs_consumer'),
    path('search_logs/', views.search_logs, name='search_logs'),
]


