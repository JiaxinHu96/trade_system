from django.urls import path
from .views import StartIBKRSyncAPIView, SyncJobListAPIView, IBKRConfigDebugAPIView, IBKRAccountSummaryAPIView

urlpatterns = [
    path('ibkr/start/', StartIBKRSyncAPIView.as_view(), name='ibkr-sync-start'),
    path('jobs/', SyncJobListAPIView.as_view(), name='sync-job-list'),
    path('ibkr/config-debug/', IBKRConfigDebugAPIView.as_view(), name='ibkr-config-debug'),
    path('ibkr/account-summary/', IBKRAccountSummaryAPIView.as_view(), name='ibkr-account-summary'),
]
