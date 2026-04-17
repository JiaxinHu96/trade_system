from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import DailyReviewImageUploadAPIView, DailyReviewViewSet

router = DefaultRouter()
router.register('daily-reviews', DailyReviewViewSet, basename='daily-review')

urlpatterns = router.urls + [
    path('daily-review-image-upload/', DailyReviewImageUploadAPIView.as_view(), name='daily-review-image-upload'),
]
