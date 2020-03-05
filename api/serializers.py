from rest_framework.serializers import ModelSerializer

from api import models


class DealSerializer(ModelSerializer):
    class Meta:
        model = models.Deal
        fields = ['id', 'created_at', 'title']
