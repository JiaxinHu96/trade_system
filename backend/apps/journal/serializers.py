from rest_framework import serializers
from apps.trades.models import TradeGroup
from .models import (
    DailyReview,
    DailyReviewImage,
    MistakeTag,
    PositionCheckpoint,
    PreTradePlan,
    SetupSnapshot,
    SetupTag,
    TradeJournal,
    TradeReview,
)


class DailyReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyReviewImage
        fields = ['id', 'image_url', 'sort_order', 'created_at']
        read_only_fields = ['id', 'created_at']


class SetupTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = SetupTag
        fields = '__all__'


class MistakeTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = MistakeTag
        fields = '__all__'


class DailyReviewSerializer(serializers.ModelSerializer):
    related_trade_group_display = serializers.SerializerMethodField(read_only=True)
    related_trade_groups_display = serializers.SerializerMethodField(read_only=True)
    related_trade_group = serializers.PrimaryKeyRelatedField(queryset=TradeGroup.objects.all(), allow_null=True, required=False)
    related_trade_groups = serializers.PrimaryKeyRelatedField(queryset=TradeGroup.objects.all(), many=True, required=False)
    images = DailyReviewImageSerializer(many=True, read_only=True)
    image_urls = serializers.ListField(child=serializers.CharField(max_length=500), write_only=True, required=False, allow_empty=True)

    class Meta:
        model = DailyReview
        fields = '__all__'

    def _trade_group_display(self, trade_group):
        return {
            'id': trade_group.id,
            'symbol': trade_group.symbol,
            'trade_date': trade_group.trade_date,
            'status': trade_group.status,
            'direction': trade_group.direction,
            'realized_pnl': trade_group.realized_pnl,
        }

    def get_related_trade_group_display(self, obj):
        if not obj.related_trade_group:
            return None
        return self._trade_group_display(obj.related_trade_group)

    def get_related_trade_groups_display(self, obj):
        return [self._trade_group_display(item) for item in obj.related_trade_groups.all().order_by('opened_at', 'id')]

    def create(self, validated_data):
        image_urls = validated_data.pop('image_urls', [])
        related_trade_groups = validated_data.pop('related_trade_groups', [])
        instance = super().create(validated_data)
        if related_trade_groups:
            instance.related_trade_groups.set(related_trade_groups)
        elif instance.related_trade_group:
            instance.related_trade_groups.set([instance.related_trade_group])
        self._replace_images(instance, image_urls)
        return instance

    def update(self, instance, validated_data):
        image_urls = validated_data.pop('image_urls', None)
        related_trade_groups = validated_data.pop('related_trade_groups', None)
        instance = super().update(instance, validated_data)
        if related_trade_groups is not None:
            instance.related_trade_groups.set(related_trade_groups)
        elif instance.related_trade_group and not instance.related_trade_groups.filter(id=instance.related_trade_group_id).exists():
            instance.related_trade_groups.add(instance.related_trade_group)
        if image_urls is not None:
            self._replace_images(instance, image_urls)
        return instance

    def _replace_images(self, instance, image_urls):
        instance.images.all().delete()
        normalized = [url for url in image_urls if url]
        for idx, url in enumerate(normalized):
            DailyReviewImage.objects.create(daily_review=instance, image_url=url, sort_order=idx)
        instance.image_url = normalized[0] if normalized else ''
        instance.save(update_fields=['image_url'])


class TradeJournalSerializer(serializers.ModelSerializer):
    trade_group_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TradeJournal
        fields = '__all__'

    def get_trade_group_display(self, obj):
        group = obj.trade_group
        return {
            'id': group.id,
            'symbol': group.symbol,
            'trade_date': group.trade_date,
            'status': group.status,
            'direction': group.direction,
            'realized_pnl': group.realized_pnl,
        }


class TradeReviewSerializer(serializers.ModelSerializer):
    trade_group_display = serializers.SerializerMethodField(read_only=True)
    setup_display = SetupTagSerializer(source='setup', read_only=True)
    mistake_tags_display = MistakeTagSerializer(source='mistake_tags', many=True, read_only=True)

    class Meta:
        model = TradeReview
        fields = '__all__'

    def get_trade_group_display(self, obj):
        group = obj.trade_group
        return {
            'id': group.id,
            'symbol': group.symbol,
            'trade_date': group.trade_date,
            'status': group.status,
            'direction': group.direction,
            'realized_pnl': group.realized_pnl,
        }


class PositionCheckpointSerializer(serializers.ModelSerializer):
    trade_group_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = PositionCheckpoint
        fields = '__all__'

    def get_trade_group_display(self, obj):
        group = obj.trade_group
        return {
            'id': group.id,
            'symbol': group.symbol,
            'trade_date': group.trade_date,
            'status': group.status,
            'direction': group.direction,
            'open_qty': group.open_qty,
        }


class PreTradePlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreTradePlan
        fields = '__all__'


class SetupSnapshotSerializer(serializers.ModelSerializer):
    setup_display = SetupTagSerializer(source='setup', read_only=True)

    class Meta:
        model = SetupSnapshot
        fields = '__all__'
