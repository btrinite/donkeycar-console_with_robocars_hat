from rest_framework import serializers


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
    uuid = serializers.CharField(max_length=1024, required=False)


class MetaSerializer(serializers.Serializer):
    no_of_images = serializers.IntegerField()
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    remark = serializers.CharField()
    rating = serializers.FloatField()


class UploadTubSerializer(serializers.Serializer):
    """
    used by upload_tubs endpoint
    """
    # tub_paths = serializers.CharField(required=True, max_length=1000)
    tub_names = serializers.ListField(
        child=serializers.CharField(required=True, max_length=100), allow_empty=False)
