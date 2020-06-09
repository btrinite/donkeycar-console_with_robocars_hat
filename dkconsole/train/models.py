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
    model_size = models.FloatField(null=True, blank=True)
    model_url = models.CharField(max_length=2000, null = True)
    model_accuracy_url = models.CharField(max_length=2000, null = True)
    uuid = models.UUIDField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


# class JobRemark(models.Model):
#     content = models.CharField(max_length=500)

    # state = models.CharField(max_length=50)
    # job_number = models.IntegerField(default=0)
    # date = models.DateTimeField(default=datetime.now, blank=True)
    # size = models.CharField(max_length=20, default="N/A")
    # instance_max = models.IntegerField(default=15)
    # request_time = models.IntegerField(default=2)
    # request_state = models.CharField(max_length=200, default="Pending")
    # availability_zone = models.CharField(max_length=200, default="...")
    # tarfile_size = models.CharField(max_length=20, default="N/A")
    # log_url = models.CharField(max_length=20, default="N/A")
    # commands_log_url = models.CharField(max_length=20, default="N/A")
    # duration = models.CharField(max_length=20, default="N/A")
    # instance = models.CharField(max_length=200, default="...")
    # Comments = models.ManyToManyField(remarks)
    # request_id = models.CharField(max_length=200, default="0")
    # instance_id = models.CharField(max_length=200, default="0")
    # price = models.CharField(max_length=30, default="N/A")
