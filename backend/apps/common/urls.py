from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DashboardPreferenceAPIView, DashboardTabViewSet, StrategyOptionViewSet

router = DefaultRouter()
router.register("dashboard-tabs", DashboardTabViewSet, basename="dashboard-tab")
router.register("strategy-options", StrategyOptionViewSet, basename="strategy-option")

urlpatterns = router.urls + [
    path("dashboard-preferences/", DashboardPreferenceAPIView.as_view(), name="dashboard-preferences"),
]
