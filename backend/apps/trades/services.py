from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from django.db import transaction

from .matching import DayFIFOSummary
from .models import RawIBKRExecution, TradeFill, TradeGroup, TradeLotSnapshot


ZERO = Decimal('0')


def _to_decimal(value, default: str = '0') -> Decimal:
    if value in (None, ''):
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


@transaction.atomic
def create_fill_from_raw(raw_execution: RawIBKRExecution):
    side = (raw_execution.side or '').upper()
    qty = _to_decimal(raw_execution.quantity)
    signed_qty = qty if side == 'BUY' else -qty
    fill, _ = TradeFill.objects.update_or_create(
        raw_execution=raw_execution,
        defaults={
            'symbol': raw_execution.symbol,
            'side': raw_execution.side,
            'quantity': raw_execution.quantity,
            'price': raw_execution.price,
            'executed_at': raw_execution.executed_at,
            'commission': raw_execution.commission or ZERO,
            'signed_qty': signed_qty,
            'asset_class': raw_execution.sec_type,
            'trade_day': raw_execution.trade_date or raw_execution.executed_at.date(),
        },
    )
    return fill


@transaction.atomic
def rebuild_trade_groups_for_dates(trade_dates):
    """
    Rebuild all trade groups.

    The previous date-scoped rebuild reset matching at midnight, which breaks overnight
    positions and causes the dashboard PnL/open-position totals to drift away from IBKR.
    Rebuilding from the full ordered fill history keeps FIFO state continuous across days.
    """
    rebuild_all_trade_groups()


@transaction.atomic
def rebuild_trade_groups_for_date(trade_date):
    rebuild_all_trade_groups()


@transaction.atomic
def rebuild_all_trade_groups():
    fills = list(
        TradeFill.objects.select_related('raw_execution')
        .all()
        .order_by('symbol', 'asset_class', 'executed_at', 'id')
    )

    TradeLotSnapshot.objects.all().delete()
    TradeGroup.objects.all().delete()

    if not fills:
        return

    buckets = {}
    fills_by_position_key = defaultdict(list)
    for fill in fills:
        account = getattr(fill.raw_execution, 'account', None) if getattr(fill, 'raw_execution', None) else None
        key = (account or '', fill.symbol or '', fill.asset_class or '')
        fills_by_position_key[key].append(fill)

    for (_, symbol, asset_class), key_fills in fills_by_position_key.items():
        matcher = DayFIFOSummary()

        for fill in key_fills:
            trade_day = fill.trade_day or fill.executed_at.date()
            bucket_key = (symbol, trade_day)
            bucket = buckets.get(bucket_key)
            if bucket is None:
                bucket = {
                    'symbol': symbol,
                    'trade_date': trade_day,
                    'asset_class': asset_class,
                    'total_buy_qty': ZERO,
                    'total_sell_qty': ZERO,
                    'buy_notional': ZERO,
                    'sell_notional': ZERO,
                    'net_qty': ZERO,
                    'avg_open_cost': None,
                    'open_qty': ZERO,
                    'realized_pnl': ZERO,
                    'commission_total': ZERO,
                    'opened_at': fill.executed_at,
                    'closed_at': None,
                    'last_fill_at': fill.executed_at,
                    'direction': None,
                    'status': 'open',
                    'had_buy': False,
                    'had_sell': False,
                    'lot_snapshots': [],
                }
                buckets[bucket_key] = bucket

            match_info = matcher.apply_fill(fill)
            raw_realized = None
            if getattr(fill, 'raw_execution', None) is not None and fill.raw_execution.realized_pnl is not None:
                raw_realized = _to_decimal(fill.raw_execution.realized_pnl)

            if raw_realized is not None and match_info['closed_qty'] > ZERO:
                realized_delta = raw_realized
            else:
                realized_delta = match_info['fallback_realized_pnl']

            qty = _to_decimal(fill.quantity)
            price = _to_decimal(fill.price)
            signed_qty = _to_decimal(fill.signed_qty)
            commission = _to_decimal(fill.commission)

            bucket['last_fill_at'] = fill.executed_at
            bucket['commission_total'] += commission
            bucket['realized_pnl'] += realized_delta
            bucket['net_qty'] += signed_qty

            if (fill.side or '').upper() == 'BUY':
                bucket['had_buy'] = True
                bucket['total_buy_qty'] += qty
                bucket['buy_notional'] += qty * price
            else:
                bucket['had_sell'] = True
                bucket['total_sell_qty'] += qty
                bucket['sell_notional'] += qty * price

        # Determine each day's remaining lots from final FIFO state.
        # This prevents earlier days from being stuck as "open/partial" after a later close.
        remaining_by_day = defaultdict(list)
        for snapshot in matcher.snapshot_open_lots():
            opened_at = snapshot.get('opened_at')
            opened_day = opened_at.date() if opened_at is not None else None
            if opened_day is None:
                continue
            remaining_by_day[opened_day].append(snapshot)

        symbol_bucket_keys = [key for key in buckets.keys() if key[0] == symbol]
        for bucket_symbol, bucket_trade_day in symbol_bucket_keys:
            bucket = buckets[(bucket_symbol, bucket_trade_day)]
            day_snapshots = remaining_by_day.get(bucket_trade_day, [])

            day_open_qty = sum((snapshot['open_qty'] for snapshot in day_snapshots), ZERO)
            day_abs_qty = sum((abs(snapshot['remaining_qty']) for snapshot in day_snapshots), ZERO)
            day_notional = sum((abs(snapshot['remaining_qty']) * snapshot['open_price'] for snapshot in day_snapshots), ZERO)

            bucket['open_qty'] = day_open_qty
            bucket['avg_open_cost'] = (day_notional / day_abs_qty) if day_abs_qty > ZERO else None
            bucket['lot_snapshots'] = [dict(item) for item in day_snapshots]

            if day_open_qty > ZERO:
                bucket['direction'] = 'LONG'
            elif day_open_qty < ZERO:
                bucket['direction'] = 'SHORT'
            else:
                bucket['direction'] = None

            if day_open_qty == ZERO:
                bucket['status'] = 'closed' if (bucket['had_buy'] and bucket['had_sell']) else 'open'
                bucket['closed_at'] = bucket['last_fill_at'] if bucket['status'] == 'closed' else None
            elif bucket['had_buy'] and bucket['had_sell']:
                bucket['status'] = 'partial'
                bucket['closed_at'] = None
            else:
                bucket['status'] = 'open'
                bucket['closed_at'] = None

    for bucket_key in sorted(buckets.keys(), key=lambda item: (item[1], item[0])):
        bucket = buckets[bucket_key]
        avg_buy_price = None
        if bucket['total_buy_qty'] > ZERO:
            avg_buy_price = bucket['buy_notional'] / bucket['total_buy_qty']

        avg_sell_price = None
        if bucket['total_sell_qty'] > ZERO:
            avg_sell_price = bucket['sell_notional'] / bucket['total_sell_qty']

        group = TradeGroup.objects.create(
            symbol=bucket['symbol'],
            trade_date=bucket['trade_date'],
            asset_class=bucket['asset_class'],
            direction=bucket['direction'],
            status=bucket['status'],
            total_buy_qty=bucket['total_buy_qty'],
            total_sell_qty=bucket['total_sell_qty'],
            net_qty=bucket['net_qty'],
            avg_buy_price=avg_buy_price,
            avg_sell_price=avg_sell_price,
            avg_open_cost=bucket['avg_open_cost'],
            open_qty=bucket['open_qty'],
            realized_pnl=bucket['realized_pnl'],
            commission_total=bucket['commission_total'],
            opened_at=bucket['opened_at'],
            closed_at=bucket['closed_at'],
        )

        snapshots = bucket['lot_snapshots']
        if snapshots:
            TradeLotSnapshot.objects.bulk_create(
                [
                    TradeLotSnapshot(
                        trade_group=group,
                        symbol=group.symbol,
                        open_qty=snapshot['open_qty'],
                        remaining_qty=snapshot['remaining_qty'],
                        open_price=snapshot['open_price'],
                        opened_at=snapshot['opened_at'] or group.opened_at,
                    )
                    for snapshot in snapshots
                ]
            )
