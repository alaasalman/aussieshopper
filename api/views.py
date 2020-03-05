import logging

from django.shortcuts import get_object_or_404

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny

from api import models
from api import tasks
from api import serializers

logger = logging.getLogger(__name__)


class HandleChatMessage(APIView):
    http_method_names = ['post']
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        json_msg = request.data

        logger.info(json_msg)

        lcmessage = models.LogChatMessage()
        lcmessage.original_msg = request.data
        lcmessage.save()

        tasks.handle_message.delay(json_msg, lcmessage.id)

        return Response()


class StatsViewSet(viewsets.GenericViewSet):
    queryset = models.Deal.objects.all()

    def get_queryset(self):
        return models.DataStore.objects.all()

    def get_object(self):
        qs = self.get_queryset()

        return get_object_or_404(qs, key='monthly-counts')

    @action(detail=False, url_path='deal-data-monthly')
    def chart_data_monthly(self, request):

        monthly_deal_count_store = self.get_object()
        monthly_deal_count = monthly_deal_count_store.data
        deal_keys_sorted_list = sorted(monthly_deal_count.keys())

        return Response({
            'label': 'Deals By Month',
            'labels': deal_keys_sorted_list,
            'data': [monthly_deal_count[deals_key] for deals_key in deal_keys_sorted_list]
        })
