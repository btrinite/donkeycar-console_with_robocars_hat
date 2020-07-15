from rest_framework import serializers
from .models import Job, JobStatus
from django.conf import settings


class JobSerializer(serializers.ModelSerializer):

    name = serializers.SerializerMethodField()
    train_duration = serializers.SerializerMethodField()
    model_path = serializers.SerializerMethodField()
    model_movie_path = serializers.SerializerMethodField()

    def get_name(self, job):
        return f"Job #{job.id}"

    def get_train_duration(self, job):
        return "10 mins"

    def get_model_path(self, job):
        if job.model_url is not None:
            return settings.MODEL_DIR + f"/job_{job.id}.h5"
        else:
            return None

    def get_model_movie_path(self, job):
        if job.model_url is not None:
            return settings.MOVIE_DIR + f"/job_{job.id}.mp4"
        else:
            return None

    class Meta:
        model = Job

        fields = ['id', 'name', 'uuid', 'tub_paths', 'status',  'created_at',
                  'model_url', 'model_accuracy_url', 'model_path', 'model_movie_path', 'train_duration']

        ordering = ['-created']


class SubmitJobSerializer(serializers.Serializer):
    # tub_paths = serializers.CharField(required=True, max_length=1000)
    tub_paths = serializers.ListField(
        child=serializers.CharField(required=True, max_length=100), allow_empty=False)