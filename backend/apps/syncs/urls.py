from django.urls import path
from .views import StartIBKRSyncAPIView, SyncJobListAPIView, IBKRConfigDebugAPIView

urlpatterns = [
    path('ibkr/start/', StartIBKRSyncAPIView.as_view(), name='ibkr-sync-start'),
    path('jobs/', SyncJobListAPIView.as_view(), name='sync-job-list'),
    path('ibkr/config-debug/', IBKRConfigDebugAPIView.as_view(), name='ibkr-config-debug'),
]