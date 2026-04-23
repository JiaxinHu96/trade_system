from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    DailyReviewImageUploadAPIView,
    DailyReviewViewSet,
    PositionCheckpointViewSet,
    TradeJournalViewSet,
    TradeReviewViewSet,
)

router = DefaultRouter()
router.register('daily-reviews', DailyReviewViewSet, basename='daily-review')
router.register('trade-journals', TradeJournalViewSet, basename='trade-journal')
router.register('trade-reviews', TradeReviewViewSet, basename='trade-review')
router.register('position-checkpoints', PositionCheckpointViewSet, basename='position-checkpoint')

urlpatterns = router.urls + [
    path('daily-review-image-upload/', DailyReviewImageUploadAPIView.as_view(), name='daily-review-image-upload'),
]
