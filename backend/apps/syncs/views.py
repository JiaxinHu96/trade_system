from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView

from apps.brokers.ibkr_client import IBKRClient
from apps.brokers.services import IBKRSyncService
from .models import SyncJob
from .serializers import SyncJobSerializer


class StartIBKRSyncAPIView(APIView):
    def post(self, request):
        job = SyncJob.objects.create(
            source='ibkr',
            job_type='full_sync',
            status='running',
            started_at=timezone.now(),
        )
        try:
            service = IBKRSyncService(client=IBKRClient())
            result = service.run_full_sync(job)
            job.finished_at = timezone.now()
            if job.status == 'running':
                job.status = 'success'
            job.save(update_fields=['finished_at', 'status', 'updated_at'])
            return Response({'job_id': job.id, 'result': result})
        except Exception as exc:
            job.status = 'failed'
            job.error_message = str(exc)
            job.finished_at = timezone.now()
            job.save(update_fields=['status', 'error_message', 'finished_at', 'updated_at'])
            return Response({'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SyncJobListAPIView(ListAPIView):
    queryset = SyncJob.objects.all()
    serializer_class = SyncJobSerializer


class IBKRConfigDebugAPIView(APIView):
    def get(self, request):
        token = settings.IBKR_FLEX_TOKEN or ""
        query_id = settings.IBKR_FLEX_QUERY_ID or ""
        return Response({
            "token_exists": bool(token),
            "query_id_exists": bool(query_id),
            "token_preview": f"{token[:6]}...{token[-4:]}" if len(token) >= 10 else "",
            "query_id": query_id,
        })


class IBKRAccountSummaryAPIView(APIView):
    def get(self, request):
        try:
            client = IBKRClient()
            summary = client.fetch_account_summary()
            payload = {
                "account_id": summary.get("account_id") or "",
                "currency": summary.get("currency") or "USD",
                "net_liq": str(summary.get("net_liq")),
                "as_of": summary.get("as_of") or "",
            }
            return Response(payload)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
