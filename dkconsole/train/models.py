from django.utils.translation import gettext_lazy as _
from django.db import models
from enum import Enum
from datetime import datetime
from django.utils import timezone
# Create your models here.


class JobStatus():   # A subclass of Enum
    SCHEDULED = "SCHEDULED"
    TRAINING = "TRAINING"
    COMPLETED = "COMPLETED"
    NO_CAPACITY = "NO_CAPACITY"
    NO_QUOTA = "NO_QUOTA"
    SPOT_REQUEST_FAILED = "SPOT_REQUEST_FAILED"
    TIMEOUT = "TIMEOUT"

    OS_STATUSES = [SCHEDULED, TRAINING]


# Create your models here.
class Job(models.Model):
    tub_paths = models.CharField(max_length=2000)
    status = models.CharField(
        max_length=20,
        #   choices=[(tag, tag.value) for tag in JobStatus]  # Choices is a list of Tuple
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    model_size = models.FloatField(null=True, blank=True)
    model_url = models.CharField(max_length=2000, null = True)
    model_accuracy_url = models.CharField(max_length=2000, null = True)
    model_movie_url = models.CharField(max_length=2000, null = True)
    uuid = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

