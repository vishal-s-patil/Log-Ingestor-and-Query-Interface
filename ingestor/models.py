from django.db import models


class LogEntry(models.Model):
    level = models.CharField(max_length=255)
    message = models.TextField()
    resourceId = models.CharField(max_length=255)
    timestamp = models.DateTimeField()
    traceId = models.CharField(max_length=255)
    spanId = models.CharField(max_length=255)
    commit = models.CharField(max_length=255)
    parentResourceId = models.CharField(max_length=255, blank=True, null=True)
    metadata = models.JSONField()

    def __str__(self):
        return f"Level: {self.level} \n Message: {self.message} \n Timestamp: {self.timestamp} \n TraceID: {self.traceId} \n Metadata: {self.metadata}"
