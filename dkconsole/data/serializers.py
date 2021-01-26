from rest_framework import serializers
from .models import Tub


class TubImageSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=512)
    width = serializers.IntegerField()
    height = serializers.IntegerField()


class TubSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    path = serializers.CharField(max_length=512)
    created_at = serializers.DateTimeField()
    no_of_images = serializers.IntegerField()
    thumbnail = TubImageSerializer()
    size = serializers.FloatField()
    rating = serializers.FloatField()
    previews = serializers.ListField(
        child=serializers.CharField())


class MetaSerializer(serializers.Serializer):
    no_of_images = serializers.IntegerField()
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    remark = serializers.CharField()
    rating = serializers.FloatField()