from django.db import IntegrityError, transaction

from apps.syncs.models import SyncJob
from apps.trades.models import RawIBKRExecution
from apps.trades.services import create_fill_from_raw, rebuild_trade_groups_for_dates
from apps.journal.auto_snapshots import ensure_trade_journal_snapshots
from decimal import Decimal

from .normalizers import build_execution_dedupe_key, parse_dt


class IBKRSyncService:
    def __init__(self, client):
        self.client = client

    def normalize_row(self, row: dict) -> dict:
        executed_at = parse_dt(row.get('executed_at'))
        side = (row.get('side') or '').upper()
        return {
            'execution_id': row.get('execution_id'),
            'perm_id': row.get('perm_id'),
            'order_id': row.get('order_id'),
            'client_id': row.get('client_id'),
            'account': row.get('account'),
            'symbol': row.get('symbol'),
            'local_symbol': row.get('local_symbol'),
            'conid': row.get('conid'),
            'sec_type': row.get('sec_type'),
            'currency': row.get('currency'),
            'exchange': row.get('exchange'),
            'side': side,
            'quantity': Decimal(str(row.get('quantity'))),
            'price': Decimal(str(row.get('price'))),
            'commission': Decimal(str(row.get('commission') or '0')),
            'realized_pnl': Decimal(str(row.get('realized_pnl'))) if row.get('realized_pnl') not in (None, '') else None,
            'executed_at': executed_at,
            'trade_date': executed_at.date() if executed_at else None,
            "raw_payload": row.get("raw_payload", {})
        }

    def run_full_sync(self, sync_job: SyncJob):
        rows = self.client.fetch_all_executions()
        sync_job.raw_count = len(rows)
        sync_job.save(update_fields=['raw_count', 'updated_at'])

        inserted = 0
        duplicate_count = 0
        touched_trade_dates = set()

        for row in rows:
            normalized = self.normalize_row(row)
            if normalized.get('trade_date'):
                touched_trade_dates.add(normalized['trade_date'])
            dedupe_key = build_execution_dedupe_key(normalized)
            normalized['dedupe_key'] = dedupe_key
            try:
                with transaction.atomic():
                    raw_obj = RawIBKRExecution.objects.create(sync_job=sync_job, **normalized)
                    create_fill_from_raw(raw_obj)
                    inserted += 1
                    if raw_obj.trade_date:
                        touched_trade_dates.add(raw_obj.trade_date)
            except IntegrityError:
                duplicate_count += 1
            except Exception as exc:
                sync_job.error_count += 1
                sync_job.error_message = str(exc)
                sync_job.save(update_fields=['error_count', 'error_message', 'updated_at'])

        rebuild_trade_groups_for_dates(touched_trade_dates)
        auto_snapshot_count = ensure_trade_journal_snapshots(touched_trade_dates)

        sync_job.inserted_count = inserted
        sync_job.duplicate_count = duplicate_count
        sync_job.status = 'success' if sync_job.error_count == 0 else 'partial'
        sync_job.save(update_fields=['inserted_count', 'duplicate_count', 'status', 'updated_at'])

        return {
            'raw_count': len(rows),
            'inserted_count': inserted,
            'duplicate_count': duplicate_count,
            'error_count': sync_job.error_count,
            'touched_trade_dates': [str(x) for x in sorted(touched_trade_dates)],
            'auto_snapshot_count': auto_snapshot_count,
        }
