from django.urls import path, include
from . import views

urlpatterns = [
    path('logentries/', views.LogEntryCreateView.as_view(), name='logentry-create'),
    path('test/', views.test_view, name='test_view'),
    path('sqs_consumer/', views.SQSConsumerView.as_view(), name='sqs_consumer'),
]


