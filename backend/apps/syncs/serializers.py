from rest_framework import serializers
from .models import SyncJob


class SyncJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = SyncJob
        fields = '__all__'
