from rest_framework import serializers


class MLModelSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    path = serializers.CharField(max_length=512)
    created = serializers.DateTimeField()
    rating = serializers.FloatField()