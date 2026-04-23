from pathlib import Path
import uuid

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.trades.models import TradeGroup
from .models import DailyReview, PositionCheckpoint, TradeJournal, TradeReview
from .serializers import (
    DailyReviewSerializer,
    PositionCheckpointSerializer,
    TradeJournalSerializer,
    TradeReviewSerializer,
)


class DailyReviewViewSet(viewsets.ModelViewSet):
    queryset = DailyReview.objects.all().order_by('-review_date', '-updated_at')
    serializer_class = DailyReviewSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        review_date = self.request.query_params.get('date')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        strategy = self.request.query_params.get('strategy')
        if review_date:
            qs = qs.filter(review_date=review_date)
        if date_from:
            qs = qs.filter(review_date__gte=date_from)
        if date_to:
            qs = qs.filter(review_date__lte=date_to)
        if strategy:
            qs = qs.filter(strategy__icontains=strategy)
        return qs

    def create(self, request, *args, **kwargs):
        payload = request.data.copy()
        if not payload.get('review_date'):
            payload['review_date'] = timezone.localdate().isoformat()

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='trade-options')
    def trade_options(self, request):
        review_date = request.query_params.get('date')
        if not review_date:
            return Response([])
        trade_groups = (
            TradeGroup.objects.filter(
                Q(trade_date=review_date)
                | Q(opened_at__date=review_date)
                | Q(closed_at__date=review_date)
            )
            .order_by('opened_at', 'id')
        )
        data = [
            {
                'id': item.id,
                'label': f"{item.symbol} | {item.opened_at} -> {item.closed_at} | PnL {item.realized_pnl}",
                'symbol': item.symbol,
                'trade_date': item.trade_date,
                'opened_at': item.opened_at,
                'closed_at': item.closed_at,
                'status': item.status,
                'realized_pnl': item.realized_pnl,
            }
            for item in trade_groups
        ]
        return Response(data)


class TradeJournalViewSet(viewsets.ModelViewSet):
    queryset = TradeJournal.objects.select_related('trade_group').all().order_by('-updated_at', '-id')
    serializer_class = TradeJournalSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        trade_group_id = self.request.query_params.get('trade_group')
        if trade_group_id:
            qs = qs.filter(trade_group_id=trade_group_id)
        return qs

    def create(self, request, *args, **kwargs):
        trade_group_id = request.data.get('trade_group')
        if trade_group_id:
            instance = TradeJournal.objects.filter(trade_group_id=trade_group_id).first()
            if instance:
                serializer = self.get_serializer(instance, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                return Response(serializer.data, status=status.HTTP_200_OK)
        return super().create(request, *args, **kwargs)


class TradeReviewViewSet(viewsets.ModelViewSet):
    queryset = TradeReview.objects.select_related('trade_group', 'daily_review', 'setup').prefetch_related('mistake_tags').all()
    serializer_class = TradeReviewSerializer

    def get_queryset(self):
        qs = super().get_queryset().order_by('-updated_at', '-id')
        trade_group_id = self.request.query_params.get('trade_group')
        daily_review_id = self.request.query_params.get('daily_review')
        if trade_group_id:
            qs = qs.filter(trade_group_id=trade_group_id)
        if daily_review_id:
            qs = qs.filter(daily_review_id=daily_review_id)
        return qs

    def create(self, request, *args, **kwargs):
        trade_group_id = request.data.get('trade_group')
        if trade_group_id:
            instance = TradeReview.objects.filter(trade_group_id=trade_group_id).first()
            if instance:
                serializer = self.get_serializer(instance, data=request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                self.perform_update(serializer)
                return Response(serializer.data, status=status.HTTP_200_OK)
        return super().create(request, *args, **kwargs)


class PositionCheckpointViewSet(viewsets.ModelViewSet):
    queryset = PositionCheckpoint.objects.select_related('trade_group').all().order_by('-review_date', '-updated_at')
    serializer_class = PositionCheckpointSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        review_date = self.request.query_params.get('date')
        trade_group_id = self.request.query_params.get('trade_group')
        status_value = self.request.query_params.get('status')
        if review_date:
            qs = qs.filter(review_date=review_date)
        if trade_group_id:
            qs = qs.filter(trade_group_id=trade_group_id)
        if status_value:
            qs = qs.filter(status=status_value)
        return qs


class DailyReviewImageUploadAPIView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_files = request.FILES.getlist('images')
        single_file = request.FILES.get('image')
        if single_file and not uploaded_files:
            uploaded_files = [single_file]

        if not uploaded_files:
            return Response({'error': 'No image uploaded.'}, status=status.HTTP_400_BAD_REQUEST)

        image_urls = []
        for image_file in uploaded_files:
            ext = Path(image_file.name).suffix or '.png'
            file_name = f"daily_reviews/{uuid.uuid4().hex}{ext}"
            file_path = Path(settings.MEDIA_ROOT) / file_name
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'wb+') as destination:
                for chunk in image_file.chunks():
                    destination.write(chunk)

            image_urls.append(request.build_absolute_uri(settings.MEDIA_URL + file_name))

        if len(image_urls) == 1:
            return Response({'image_url': image_urls[0], 'image_urls': image_urls})
        return Response({'image_urls': image_urls})
