from rest_framework import serializers
from .models import RawIBKRExecution, TradeFill, TradeGroup, TradeLotSnapshot


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
        return [
            {
                'id': review.id,
                'review_date': review.review_date,
                'market_summary': review.market_summary,
            }
            for review in obj.daily_reviews.all().order_by('-review_date', '-id')
        ]
