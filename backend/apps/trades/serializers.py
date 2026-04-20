from rest_framework import serializers
from django.db import connection
from .models import RawIBKRExecution, TradeFill, TradeGroup, TradeLotSnapshot
from apps.journal.models import DailyReview


def _daily_review_has_strategy_column():
    table_name = DailyReview._meta.db_table
    with connection.cursor() as cursor:
        columns = {
            item.name
            for item in connection.introspection.get_table_description(cursor, table_name)
        }
    return 'strategy' in columns


class RawIBKRExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawIBKRExecution
        fields = '__all__'


class TradeFillSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeFill
        fields = '__all__'


class TradeLotSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeLotSnapshot
        fields = '__all__'


class TradeGroupSerializer(serializers.ModelSerializer):
    lot_snapshots = TradeLotSnapshotSerializer(many=True, read_only=True)
    raw_executions = serializers.SerializerMethodField()
    fills = serializers.SerializerMethodField()
    linked_daily_reviews = serializers.SerializerMethodField()

    class Meta:
        model = TradeGroup
        fields = '__all__'

    def _group_executions_queryset(self, obj):
        qs = RawIBKRExecution.objects.filter(symbol=obj.symbol)
        if obj.opened_at:
            qs = qs.filter(executed_at__gte=obj.opened_at)
        if obj.closed_at:
            qs = qs.filter(executed_at__lte=obj.closed_at)
        return qs.order_by('executed_at', 'id')

    def _group_fills_queryset(self, obj):
        qs = TradeFill.objects.filter(symbol=obj.symbol)
        if obj.opened_at:
            qs = qs.filter(executed_at__gte=obj.opened_at)
        if obj.closed_at:
            qs = qs.filter(executed_at__lte=obj.closed_at)
        return qs.order_by('executed_at', 'id')

    def get_raw_executions(self, obj):
        qs = self._group_executions_queryset(obj)
        return RawIBKRExecutionSerializer(qs, many=True).data

    def get_fills(self, obj):
        qs = self._group_fills_queryset(obj)
        return TradeFillSerializer(qs, many=True).data

    def get_linked_daily_reviews(self, obj):
        review_qs = obj.daily_reviews.all().order_by('-review_date', '-id')
        if not _daily_review_has_strategy_column():
            review_qs = review_qs.defer('strategy', 'thesis', 'entry_logic', 'exit_logic')
        return [
            {
                'id': review.id,
                'review_date': review.review_date,
                'market_summary': review.market_summary,
            }
            for review in review_qs
        ]
