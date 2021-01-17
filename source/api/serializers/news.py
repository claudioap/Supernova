from rest_framework import serializers


class NewsMinimalSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    summary = serializers.CharField()
    datetime = serializers.DateTimeField()
    url = serializers.CharField(source='get_absolute_url')


class NewsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    summary = serializers.CharField()
    content = serializers.CharField()
    datetime = serializers.DateTimeField()
    # author = TODO
    url = serializers.CharField(source='get_absolute_url')
