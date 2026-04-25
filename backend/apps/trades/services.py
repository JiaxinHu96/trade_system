from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from django.db import connection
from django.db import transaction

from .matching import DayFIFOSummary
from .models import RawIBKRExecution, TradeFill, TradeGroup, TradeLotSnapshot, TradeMatchedLot


ZERO = Decimal('0')


def _to_decimal(value, default: str = '0') -> Decimal:
    if value in (None, ''):
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _has_trade_matched_lot_table():
    with connection.cursor() as cursor:
        return TradeMatchedLot._meta.db_table in connection.introspection.table_names(cursor)


def _group_signature(
    *,
    symbol,
    asset_class,
    status,
    total_buy_qty,
    total_sell_qty,
    net_qty,
    avg_open_cost,
    realized_pnl,
    opened_at,
    closed_at,
):
    """
    Deterministic identity used to retain existing TradeGroup ids across rebuilds.
    """
    return (
        symbol or '',
        asset_class or '',
        status or '',
        _to_decimal(total_buy_qty),
        _to_decimal(total_sell_qty),
        _to_decimal(net_qty),
        _to_decimal(avg_open_cost, default='0') if avg_open_cost is not None else None,
        _to_decimal(realized_pnl),
        opened_at,
        closed_at,
    )


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

    has_matched_lot_table = _has_trade_matched_lot_table()

    existing_groups = list(TradeGroup.objects.all().order_by('id'))
    existing_by_signature = defaultdict(list)
    for group in existing_groups:
        signature = _group_signature(
            symbol=group.symbol,
            asset_class=group.asset_class,
            status=group.status,
            total_buy_qty=group.total_buy_qty,
            total_sell_qty=group.total_sell_qty,
            net_qty=group.net_qty,
            avg_open_cost=group.avg_open_cost,
            realized_pnl=group.realized_pnl,
            opened_at=group.opened_at,
            closed_at=group.closed_at,
        )
        existing_by_signature[signature].append(group)

    if not fills:
        TradeLotSnapshot.objects.all().delete()
        if has_matched_lot_table:
            TradeMatchedLot.objects.all().delete()
        TradeGroup.objects.all().delete()
        return

    trade_buckets = []
    fills_by_position_key = defaultdict(list)
    for fill in fills:
        account = getattr(fill.raw_execution, 'account', None) if getattr(fill, 'raw_execution', None) else None
        key = (account or '', fill.symbol or '', fill.asset_class or '')
        fills_by_position_key[key].append(fill)

    for (_, symbol, asset_class), key_fills in fills_by_position_key.items():
        matcher = DayFIFOSummary()

        for fill in key_fills:
            match_info = matcher.apply_fill(fill)
            raw_realized = None
            if getattr(fill, 'raw_execution', None) is not None and fill.raw_execution.realized_pnl is not None:
                raw_realized = _to_decimal(fill.raw_execution.realized_pnl)
            closed_qty = _to_decimal(match_info.get('closed_qty'))
            closed_lots = match_info.get('closed_lots') or []
            for closed_lot in closed_lots:
                matched_qty = _to_decimal(closed_lot.get('matched_qty'))
                if matched_qty <= ZERO:
                    continue
                if raw_realized is not None and closed_qty > ZERO:
                    realized_piece = raw_realized * (matched_qty / closed_qty)
                else:
                    realized_piece = _to_decimal(closed_lot.get('realized_pnl'))
                open_price = _to_decimal(closed_lot.get('open_price'))
                close_price = _to_decimal(closed_lot.get('close_price'))
                lot_side = (closed_lot.get('lot_side') or '').upper()
                if lot_side == 'SHORT':
                    buy_notional = matched_qty * close_price
                    sell_notional = matched_qty * open_price
                else:
                    buy_notional = matched_qty * open_price
                    sell_notional = matched_qty * close_price

                trade_buckets.append(
                    {
                        'symbol': symbol,
                        'asset_class': asset_class,
                        'total_buy_qty': matched_qty,
                        'total_sell_qty': matched_qty,
                        'buy_notional': buy_notional,
                        'sell_notional': sell_notional,
                        'net_qty': ZERO,
                        'avg_open_cost': None,
                        'open_qty': ZERO,
                        'realized_pnl': realized_piece,
                        'commission_total': _to_decimal(closed_lot.get('entry_commission')) + _to_decimal(closed_lot.get('exit_commission')),
                        'opened_at': closed_lot.get('opened_at') or fill.executed_at,
                        'closed_at': fill.executed_at,
                        'last_fill_at': fill.executed_at,
                        'direction': None,
                        'status': 'closed',
                        'lot_snapshots': [],
                    }
                )

        open_lots = matcher.snapshot_open_lots()
        net_open_qty = matcher.get_open_qty()
        if net_open_qty != ZERO and open_lots:
            avg_open_cost = matcher.get_avg_open_cost()
            earliest_opened_at = min((lot.get('opened_at') for lot in open_lots if lot.get('opened_at')), default=None)
            latest_opened_at = max((lot.get('opened_at') for lot in open_lots if lot.get('opened_at')), default=None)
            abs_open_qty = abs(net_open_qty)
            direction = 'SHORT' if net_open_qty < ZERO else 'LONG'
            if direction == 'SHORT':
                total_buy_qty = ZERO
                total_sell_qty = abs_open_qty
                buy_notional = ZERO
                sell_notional = (avg_open_cost or ZERO) * abs_open_qty
            else:
                total_buy_qty = abs_open_qty
                total_sell_qty = ZERO
                buy_notional = (avg_open_cost or ZERO) * abs_open_qty
                sell_notional = ZERO

            trade_buckets.append(
                {
                    'symbol': symbol,
                    'asset_class': asset_class,
                    'total_buy_qty': total_buy_qty,
                    'total_sell_qty': total_sell_qty,
                    'buy_notional': buy_notional,
                    'sell_notional': sell_notional,
                    'net_qty': net_open_qty,
                    'avg_open_cost': avg_open_cost,
                    'open_qty': net_open_qty,
                    'realized_pnl': ZERO,
                    'commission_total': ZERO,
                    'opened_at': earliest_opened_at,
                    'closed_at': None,
                    'last_fill_at': latest_opened_at or earliest_opened_at,
                    'direction': direction,
                    'status': 'open',
                    'had_buy': False,
                    'had_sell': False,
                    'lot_snapshots': open_lots,
                    'matched_lots': [],
                }
            )

    retained_group_ids = set()
    for bucket in sorted(
        trade_buckets,
        key=lambda item: (
            item['closed_at'] or item['last_fill_at'] or item['opened_at'],
            item['symbol'],
            item['opened_at'],
        ),
    ):
        group_trade_date = (
            bucket['closed_at'].date()
            if bucket['closed_at']
            else bucket['opened_at'].date()
        )
        avg_buy_price = None
        if bucket['total_buy_qty'] > ZERO:
            avg_buy_price = bucket['buy_notional'] / bucket['total_buy_qty']

        avg_sell_price = None
        if bucket['total_sell_qty'] > ZERO:
            avg_sell_price = bucket['sell_notional'] / bucket['total_sell_qty']

        signature = _group_signature(
            symbol=bucket['symbol'],
            asset_class=bucket['asset_class'],
            status=bucket['status'],
            total_buy_qty=bucket['total_buy_qty'],
            total_sell_qty=bucket['total_sell_qty'],
            net_qty=bucket['net_qty'],
            avg_open_cost=bucket['avg_open_cost'],
            realized_pnl=bucket['realized_pnl'],
            opened_at=bucket['opened_at'],
            closed_at=bucket['closed_at'],
        )
        candidates = existing_by_signature.get(signature) or []
        group = candidates.pop(0) if candidates else None
        payload = {
            'symbol': bucket['symbol'],
            'trade_date': group_trade_date,
            'asset_class': bucket['asset_class'],
            'direction': bucket['direction'],
            'status': bucket['status'],
            'total_buy_qty': bucket['total_buy_qty'],
            'total_sell_qty': bucket['total_sell_qty'],
            'net_qty': bucket['net_qty'],
            'avg_buy_price': avg_buy_price,
            'avg_sell_price': avg_sell_price,
            'avg_open_cost': bucket['avg_open_cost'],
            'open_qty': bucket['open_qty'],
            'realized_pnl': bucket['realized_pnl'],
            'commission_total': bucket['commission_total'],
            'opened_at': bucket['opened_at'],
            'closed_at': bucket['closed_at'],
        }
        if group is None:
            group = TradeGroup.objects.create(**payload)
        else:
            for field, value in payload.items():
                setattr(group, field, value)
            group.save()
            group.lot_snapshots.all().delete()
            if has_matched_lot_table:
                group.matched_lots.all().delete()

        retained_group_ids.add(group.id)

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

        matched_lots = bucket.get('matched_lots') or []
        if matched_lots and has_matched_lot_table:
            TradeMatchedLot.objects.bulk_create(
                [
                    TradeMatchedLot(
                        trade_group=group,
                        symbol=lot['symbol'],
                        side=lot['side'],
                        matched_qty=lot['matched_qty'],
                        open_price=lot['open_price'],
                        close_price=lot['close_price'],
                        realized_pnl=lot['realized_pnl'],
                        commission_total=lot['commission_total'],
                        opened_at=lot['opened_at'],
                        closed_at=lot['closed_at'],
                    )
                    for lot in matched_lots
                ]
            )

    stale_group_ids = [group.id for group in existing_groups if group.id not in retained_group_ids]
    if stale_group_ids:
        TradeGroup.objects.filter(id__in=stale_group_ids).delete()
