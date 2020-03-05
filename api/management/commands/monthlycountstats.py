import collections
from datetime import datetime

from django.core.management.base import BaseCommand

from api import models


class Command(BaseCommand):
    help = "Calculate monthly deal count."

    def add_arguments(self, parser):
        parser.add_argument('--year', default=datetime.today().year)
        parser.add_argument('--month', default=datetime.today().month)

    def handle(self, *args, **options):
        deals_qs = models.Deal.objects.filter(created_at__year=options.get('year'),
                                              created_at__month=options.get('month'))
        deals_bymonth_dict = collections.defaultdict(int)
        monthly_count_store, created = models.DataStore.objects.get_or_create(key='monthly-counts')

        for deal in deals_qs:
            deal_date = deal.created_at.date()
            deal_year = deal_date.year
            deal_month = deal_date.month

            key = datetime(deal_year, deal_month, 1).strftime('%Y-%m')
            deals_bymonth_dict[key] += 1

        print(monthly_count_store.data)
        monthly_count_store.data.update(deals_bymonth_dict)
        monthly_count_store.save()
