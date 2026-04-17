from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import TradeGroupViewSet, RawExecutionListAPIView

router = DefaultRouter()
router.register('groups', TradeGroupViewSet, basename='trade-group')

urlpatterns = router.urls + [
    path('raw-executions/', RawExecutionListAPIView.as_view(), name='raw-execution-list'),
]
