from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DashboardPreferenceAPIView, DashboardTabViewSet

router = DefaultRouter()
router.register("dashboard-tabs", DashboardTabViewSet, basename="dashboard-tab")

urlpatterns = router.urls + [
    path("dashboard-preferences/", DashboardPreferenceAPIView.as_view(), name="dashboard-preferences"),
]
