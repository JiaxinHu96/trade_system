from pathlib import Path
import uuid
from decimal import Decimal
from datetime import datetime

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.trades.models import RawIBKRExecution
from apps.trades.models import TradeGroup
from .models import DailyReview, MistakeTag, PositionCheckpoint, SetupTag, TradeJournal, TradeReview
from .serializers import (
    DailyReviewSerializer,
    MistakeTagSerializer,
    PositionCheckpointSerializer,
    SetupTagSerializer,
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

        existing = DailyReview.objects.filter(review_date=payload['review_date']).first()
        if existing:
            serializer = self.get_serializer(existing, data=payload, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='review-queue')
    def review_queue(self, request):
        selected_date = request.query_params.get('date') or timezone.localdate().isoformat()
        closed_trades = TradeGroup.objects.filter(
            Q(closed_at__date=selected_date) | Q(trade_date=selected_date, status='closed'),
            status='closed',
        ).order_by('closed_at', 'id')
        open_positions = TradeGroup.objects.filter(
            Q(opened_at__date__lte=selected_date) | Q(trade_date__lte=selected_date),
        ).exclude(open_qty=Decimal('0')).order_by('opened_at', 'id')

        daily_review = DailyReview.objects.filter(review_date=selected_date).first()

        def _hold_minutes(group):
            if not group.opened_at or not group.closed_at:
                return None
            return round((group.closed_at - group.opened_at).total_seconds() / 60, 2)

        def _review_completeness(review):
            if not review:
                return 0
            checks = [
                bool(review.setup_id),
                bool(review.thesis),
                review.entry_quality is not None,
                review.exit_quality is not None,
                review.risk_management is not None,
                bool(review.what_i_did_well),
                bool(review.what_to_improve),
                bool(review.final_grade),
            ]
            return int(round((sum(checks) / len(checks)) * 100))

        def _missing_review_items(review):
            if not review:
                return ['strategy', 'setup', 'grade', 'mistake_tags', 'screenshot']
            missing = []
            if not review.strategy:
                missing.append('strategy')
            if not review.setup_id:
                missing.append('setup')
            if not review.final_grade:
                missing.append('grade')
            if review.mistake_tags.count() == 0:
                missing.append('mistake_tags')
            if not review.screenshots:
                missing.append('screenshot')
            return missing

        closed_trade_cards = []
        for group in closed_trades:
            trade_review = getattr(group, 'trade_review', None)
            executions_qs = RawIBKRExecution.objects.filter(symbol=group.symbol)
            if group.opened_at:
                executions_qs = executions_qs.filter(executed_at__gte=group.opened_at)
            else:
                executions_qs = executions_qs.filter(executed_at__gte=timezone.make_aware(datetime.min))
            if group.closed_at:
                executions_qs = executions_qs.filter(executed_at__lte=group.closed_at)
            else:
                executions_qs = executions_qs.filter(executed_at__lte=timezone.now())
            executions_count = executions_qs.count()
            closed_trade_cards.append({
                'trade_group_id': group.id,
                'symbol': group.symbol,
                'status': group.status,
                'realized_pnl': group.realized_pnl,
                'hold_minutes': _hold_minutes(group),
                'executions_count': executions_count,
                'screenshots_count': len(trade_review.screenshots or []) if trade_review else 0,
                'review_completeness': _review_completeness(trade_review),
                'has_review': bool(trade_review),
                'setup_name': trade_review.setup.name if trade_review and trade_review.setup else '',
                'grade': trade_review.final_grade if trade_review else '',
                'mistake_tags': [tag.name for tag in trade_review.mistake_tags.all()] if trade_review else [],
                'missing_items': _missing_review_items(trade_review),
                'trade_review': TradeReviewSerializer(trade_review).data if trade_review else None,
            })

        open_position_cards = []
        for group in open_positions:
            latest_checkpoint = group.position_checkpoints.first()
            open_position_cards.append({
                'trade_group_id': group.id,
                'symbol': group.symbol,
                'status': group.status,
                'open_qty': group.open_qty,
                'avg_open_cost': group.avg_open_cost,
                'opened_at': group.opened_at,
                'latest_checkpoint_id': latest_checkpoint.id if latest_checkpoint else None,
                'latest_checkpoint_date': latest_checkpoint.review_date if latest_checkpoint else None,
            })

        summary = {
            'closed_trade_count': len(closed_trade_cards),
            'open_position_count': len(open_position_cards),
            'daily_review_completed': bool(daily_review),
        }

        return Response({
            'date': selected_date,
            'summary': summary,
            'daily_review': DailyReviewSerializer(daily_review).data if daily_review else None,
            'closed_trades': closed_trade_cards,
            'open_positions': open_position_cards,
        })

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


class SetupTagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SetupTag.objects.all().order_by('name')
    serializer_class = SetupTagSerializer


class MistakeTagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MistakeTag.objects.all().order_by('name')
    serializer_class = MistakeTagSerializer


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
