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

    TradeLotSnapshot.objects.all().delete()
    if has_matched_lot_table:
        TradeMatchedLot.objects.all().delete()
    TradeGroup.objects.all().delete()

    if not fills:
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

        for snapshot in matcher.snapshot_open_lots():
            remaining_qty = _to_decimal(snapshot.get('remaining_qty'))
            if remaining_qty <= ZERO:
                continue
            lot_side = (snapshot.get('side') or '').upper()
            open_price = _to_decimal(snapshot.get('open_price'))
            opened_at = snapshot.get('opened_at')
            if lot_side == 'SHORT':
                total_buy_qty = ZERO
                total_sell_qty = remaining_qty
                buy_notional = ZERO
                sell_notional = remaining_qty * open_price
                net_qty = -remaining_qty
                direction = 'SHORT'
            else:
                total_buy_qty = remaining_qty
                total_sell_qty = ZERO
                buy_notional = remaining_qty * open_price
                sell_notional = ZERO
                net_qty = remaining_qty
                direction = 'LONG'

            trade_buckets.append(
                {
                    'symbol': symbol,
                    'asset_class': asset_class,
                    'total_buy_qty': total_buy_qty,
                    'total_sell_qty': total_sell_qty,
                    'buy_notional': buy_notional,
                    'sell_notional': sell_notional,
                    'net_qty': net_qty,
                    'avg_open_cost': open_price,
                    'open_qty': net_qty,
                    'realized_pnl': ZERO,
                    'commission_total': ZERO,
                    'opened_at': opened_at,
                    'closed_at': None,
                    'last_fill_at': opened_at,
                    'direction': direction,
                    'status': 'open',
                    'had_buy': False,
                    'had_sell': False,
                    'lot_snapshots': [],
                    'matched_lots': [],
                }
            )

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

            current_bucket['last_fill_at'] = fill.executed_at
            current_bucket['commission_total'] += commission
            current_bucket['realized_pnl'] += realized_delta
            current_bucket['net_qty'] += signed_qty

            if (fill.side or '').upper() == 'BUY':
                current_bucket['had_buy'] = True
                current_bucket['total_buy_qty'] += qty
                current_bucket['buy_notional'] += qty * price
            else:
                current_bucket['had_sell'] = True
                current_bucket['total_sell_qty'] += qty
                current_bucket['sell_notional'] += qty * price

            closed_qty = _to_decimal(match_info.get('closed_qty'))
            for closed_lot in (match_info.get('closed_lots') or []):
                matched_qty = _to_decimal(closed_lot.get('matched_qty'))
                if matched_qty <= ZERO:
                    continue
                if raw_realized is not None and closed_qty > ZERO:
                    lot_realized = raw_realized * (matched_qty / closed_qty)
                else:
                    lot_realized = _to_decimal(closed_lot.get('realized_pnl'))
                lot_side = (closed_lot.get('lot_side') or '').upper()
                current_bucket['matched_lots'].append(
                    {
                        'symbol': symbol,
                        'side': lot_side,
                        'matched_qty': matched_qty,
                        'open_price': _to_decimal(closed_lot.get('open_price')),
                        'close_price': _to_decimal(closed_lot.get('close_price')),
                        'realized_pnl': lot_realized,
                        'commission_total': _to_decimal(closed_lot.get('entry_commission')) + _to_decimal(closed_lot.get('exit_commission')),
                        'opened_at': closed_lot.get('opened_at') or fill.executed_at,
                        'closed_at': fill.executed_at,
                    }
                )

            open_qty = matcher.get_open_qty()
            current_bucket['open_qty'] = open_qty
            current_bucket['avg_open_cost'] = matcher.get_avg_open_cost()
            current_bucket['lot_snapshots'] = [dict(item) for item in matcher.snapshot_open_lots()]

            if open_qty > ZERO:
                current_bucket['direction'] = 'LONG'
            elif open_qty < ZERO:
                current_bucket['direction'] = 'SHORT'
            else:
                current_bucket['direction'] = None

            if open_qty == ZERO:
                current_bucket['status'] = 'closed'
                current_bucket['closed_at'] = fill.executed_at
            else:
                if current_bucket['had_buy'] and current_bucket['had_sell']:
                    current_bucket['status'] = 'partial'
                else:
                    current_bucket['status'] = 'open'
                current_bucket['closed_at'] = None

            if current_bucket['status'] == 'closed':
                lifecycle_buckets.append(current_bucket)
                current_bucket = None

        if current_bucket is not None:
            lifecycle_buckets.append(current_bucket)

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

        group = TradeGroup.objects.create(
            symbol=bucket['symbol'],
            trade_date=group_trade_date,
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
