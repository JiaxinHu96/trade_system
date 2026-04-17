from rest_framework import serializers
from apps.trades.models import TradeGroup
from .models import DailyReview, DailyReviewImage, SetupTag, MistakeTag, TradeJournal


class DailyReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyReviewImage
        fields = ['id', 'image_url', 'sort_order', 'created_at']
        read_only_fields = ['id', 'created_at']


class DailyReviewSerializer(serializers.ModelSerializer):
    related_trade_group_display = serializers.SerializerMethodField(read_only=True)
    related_trade_group = serializers.PrimaryKeyRelatedField(
        queryset=TradeGroup.objects.all(),
        allow_null=True,
        required=False,
    )
    images = DailyReviewImageSerializer(many=True, read_only=True)
    image_urls = serializers.ListField(
        child=serializers.CharField(max_length=500),
        write_only=True,
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = DailyReview
        fields = '__all__'

    def get_related_trade_group_display(self, obj):
        trade_group = obj.related_trade_group
        if not trade_group:
            return None
        return {
            'id': trade_group.id,
            'symbol': trade_group.symbol,
            'trade_date': trade_group.trade_date,
            'status': trade_group.status,
            'direction': trade_group.direction,
            'realized_pnl': trade_group.realized_pnl,
        }

    def create(self, validated_data):
        image_urls = validated_data.pop('image_urls', [])
        instance = super().create(validated_data)
        self._replace_images(instance, image_urls)
        return instance

    def update(self, instance, validated_data):
        image_urls = validated_data.pop('image_urls', None)
        instance = super().update(instance, validated_data)
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


class SetupTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = SetupTag
        fields = '__all__'


class MistakeTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = MistakeTag
        fields = '__all__'


class TradeJournalSerializer(serializers.ModelSerializer):
    trade_group_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = TradeJournal
        fields = '__all__'

    def get_trade_group_display(self, obj):
        group = obj.trade_group
        if not group:
            return None
        return {
            'id': group.id,
            'symbol': group.symbol,
            'trade_date': group.trade_date,
            'status': group.status,
            'direction': group.direction,
            'realized_pnl': group.realized_pnl,
        }
