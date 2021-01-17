from rest_framework import serializers


class GroupMinimalSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    abbreviation = serializers.CharField()
    url = serializers.CharField(source='get_absolute_url')


class GroupTypeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    group_set = GroupMinimalSerializer(many=True)
