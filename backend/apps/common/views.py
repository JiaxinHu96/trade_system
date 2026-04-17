from django.db.models import Max
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DashboardPreference, DashboardTab
from .serializers import DashboardPreferenceSerializer, DashboardTabSerializer

DEFAULT_WIDGETS = [
    "overviewCards",
    "performanceCards",
    "dailyPnl",
    "winsLosses",
    "cumulativePnl",
    "symbolPnl",
    "miniAnalytics",
    "detailTabs",
]
DEFAULT_PANEL_ORDER = [
    "dailyPnl",
    "winsLosses",
    "cumulativePnl",
    "symbolPnl",
    "miniAnalytics",
]


def ensure_default_tab():
    first = DashboardTab.objects.order_by("sort_order", "id").first()
    if first:
        return first
    return DashboardTab.objects.create(
        name="Overview",
        sort_order=0,
        visible_widgets=DEFAULT_WIDGETS,
        filters={"date_from": "", "date_to": "", "account": "", "symbol": "", "strategy": "", "asset_class": ""},
        panel_order=DEFAULT_PANEL_ORDER,
    )


class DashboardTabViewSet(viewsets.ModelViewSet):
    serializer_class = DashboardTabSerializer
    queryset = DashboardTab.objects.all().order_by("sort_order", "id")

    def get_queryset(self):
        ensure_default_tab()
        return super().get_queryset()

    def perform_create(self, serializer):
        max_order = DashboardTab.objects.aggregate(value=Max("sort_order")).get("value") or 0
        serializer.save(sort_order=max_order + 1)


class DashboardPreferenceAPIView(APIView):
    def get(self, request):
        default_tab = ensure_default_tab()
        pref = DashboardPreference.get_solo()
        if pref.default_dashboard_tab is None:
            pref.default_dashboard_tab = default_tab
            pref.save(update_fields=["default_dashboard_tab", "updated_at"])
        serializer = DashboardPreferenceSerializer(pref)
        return Response(serializer.data)

    def put(self, request):
        pref = DashboardPreference.get_solo()
        serializer = DashboardPreferenceSerializer(pref, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    patch = put
