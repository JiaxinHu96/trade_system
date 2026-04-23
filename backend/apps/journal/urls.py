from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    DailyReviewImageUploadAPIView,
    DailyReviewViewSet,
    MistakeTagViewSet,
    PositionCheckpointViewSet,
    PreTradePlanViewSet,
    SetupSnapshotViewSet,
    SetupTagViewSet,
    TradeJournalViewSet,
    TradeReviewViewSet,
)

router = DefaultRouter()
router.register('daily-reviews', DailyReviewViewSet, basename='daily-review')
router.register('trade-journals', TradeJournalViewSet, basename='trade-journal')
router.register('trade-reviews', TradeReviewViewSet, basename='trade-review')
router.register('position-checkpoints', PositionCheckpointViewSet, basename='position-checkpoint')
router.register('setup-tags', SetupTagViewSet, basename='setup-tag')
router.register('mistake-tags', MistakeTagViewSet, basename='mistake-tag')
router.register('pretrade-plans', PreTradePlanViewSet, basename='pretrade-plan')
router.register('setup-snapshots', SetupSnapshotViewSet, basename='setup-snapshot')

urlpatterns = router.urls + [
    path('daily-review-image-upload/', DailyReviewImageUploadAPIView.as_view(), name='daily-review-image-upload'),
]
