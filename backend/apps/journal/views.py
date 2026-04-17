from pathlib import Path
import uuid

from django.conf import settings
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.trades.models import TradeGroup
from .models import DailyReview
from .serializers import DailyReviewSerializer


class DailyReviewViewSet(viewsets.ModelViewSet):
    queryset = DailyReview.objects.all().order_by('-review_date', '-updated_at')
    serializer_class = DailyReviewSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        review_date = self.request.query_params.get('date')
        if review_date:
            qs = qs.filter(review_date=review_date)
        return qs

    def create(self, request, *args, **kwargs):
        payload = request.data.copy()
        if not payload.get('review_date'):
            payload['review_date'] = timezone.localdate().isoformat()

        instance = DailyReview.objects.filter(review_date=payload['review_date']).first()
        if instance:
            serializer = self.get_serializer(instance, data=payload, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=payload)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='trade-options')
    def trade_options(self, request):
        review_date = request.query_params.get('date')
        if not review_date:
            return Response([])
        trade_groups = TradeGroup.objects.filter(trade_date=review_date).order_by('symbol', 'id')
        data = [
            {
                'id': item.id,
                'label': f"{item.trade_date} | {item.symbol} | {item.status.upper()} | PnL {item.realized_pnl}",
                'symbol': item.symbol,
                'trade_date': item.trade_date,
                'status': item.status,
                'realized_pnl': item.realized_pnl,
            }
            for item in trade_groups
        ]
        return Response(data)


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
