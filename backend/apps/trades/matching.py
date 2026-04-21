from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import List


ZERO = Decimal('0')
ONE = Decimal('1')


def _to_decimal(value, default: str = '0') -> Decimal:
    if value in (None, ''):
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


@dataclass
class OpenLot:
    side: str
    remaining_qty: Decimal
    open_price: Decimal
    multiplier: Decimal
    entry_commission_per_unit: Decimal
    opened_at: object = None


class DayFIFOSummary:
    """
    Stateful FIFO matcher.

    Despite the legacy class name, this matcher is intentionally *not* restricted to a
    single trade day. It can be carried across multiple days so overnight positions are
    closed against the original opening lots instead of being reset at midnight.
    """

    def __init__(self):
        self.long_lots: List[OpenLot] = []
        self.short_lots: List[OpenLot] = []
        self.realized_pnl = ZERO

    def _extract_multiplier(self, fill) -> Decimal:
        raw_execution = getattr(fill, 'raw_execution', None)
        payload = getattr(raw_execution, 'raw_payload', None) or {}
        raw_value = (
            payload.get('multiplier')
            or payload.get('Multiplier')
            or payload.get('contractMultiplier')
            or payload.get('contract_multiplier')
            or payload.get('mult')
            or ONE
        )
        try:
            value = _to_decimal(raw_value, '1')
        except Exception:
            value = ONE
        return value if value != ZERO else ONE

    def _close_long_lot(self, lot: OpenLot, close_qty: Decimal, close_price: Decimal, close_commission_per_unit: Decimal) -> Decimal:
        gross = (close_price - lot.open_price) * close_qty * lot.multiplier
        entry_commission = lot.entry_commission_per_unit * close_qty
        exit_commission = close_commission_per_unit * close_qty
        return gross - entry_commission - exit_commission

    def _close_short_lot(self, lot: OpenLot, close_qty: Decimal, close_price: Decimal, close_commission_per_unit: Decimal) -> Decimal:
        gross = (lot.open_price - close_price) * close_qty * lot.multiplier
        entry_commission = lot.entry_commission_per_unit * close_qty
        exit_commission = close_commission_per_unit * close_qty
        return gross - entry_commission - exit_commission

    def apply_fill(self, fill_or_side, quantity=None, price=None):
        """
        Apply one fill and return matching details.

        Supports either:
        - apply_fill(fill_model_instance)
        - apply_fill(side, quantity, price)  # backwards-compatible fallback
        """
        if quantity is None and price is None and hasattr(fill_or_side, 'side'):
            fill = fill_or_side
            side = (fill.side or '').upper()
            qty = _to_decimal(fill.quantity)
            fill_price = _to_decimal(fill.price)
            commission = _to_decimal(getattr(fill, 'commission', ZERO))
            executed_at = getattr(fill, 'executed_at', None)
            multiplier = self._extract_multiplier(fill)
        else:
            fill = None
            side = (fill_or_side or '').upper()
            qty = _to_decimal(quantity)
            fill_price = _to_decimal(price)
            commission = ZERO
            executed_at = None
            multiplier = ONE

        if qty <= ZERO:
            return {
                'closed_qty': ZERO,
                'opened_qty': ZERO,
                'fallback_realized_pnl': ZERO,
                'closed_lots': [],
                'multiplier': multiplier,
            }

        close_commission_per_unit = (commission / qty) if qty else ZERO
        remaining_qty = qty
        closed_qty = ZERO
        fallback_realized_pnl = ZERO
        closed_lots = []

        if side == 'BUY':
            opposite_lots = self.short_lots
            close_fn = self._close_short_lot
            same_side_lots = self.long_lots
            new_lot_side = 'LONG'
        else:
            opposite_lots = self.long_lots
            close_fn = self._close_long_lot
            same_side_lots = self.short_lots
            new_lot_side = 'SHORT'

        while remaining_qty > ZERO and opposite_lots:
            lot = opposite_lots[0]
            matched_qty = min(remaining_qty, lot.remaining_qty)
            realized_piece = close_fn(lot, matched_qty, fill_price, close_commission_per_unit)
            entry_commission = lot.entry_commission_per_unit * matched_qty
            exit_commission = close_commission_per_unit * matched_qty
            fallback_realized_pnl += realized_piece
            lot.remaining_qty -= matched_qty
            remaining_qty -= matched_qty
            closed_qty += matched_qty
            closed_lots.append(
                {
                    'lot_side': lot.side,
                    'matched_qty': matched_qty,
                    'open_price': lot.open_price,
                    'close_price': fill_price,
                    'opened_at': lot.opened_at,
                    'entry_commission': entry_commission,
                    'exit_commission': exit_commission,
                    'realized_pnl': realized_piece,
                    'multiplier': lot.multiplier,
                }
            )
            if lot.remaining_qty <= ZERO:
                opposite_lots.pop(0)

        opened_qty = remaining_qty
        if opened_qty > ZERO:
            open_commission = commission * (opened_qty / qty)
            entry_commission_per_unit = (open_commission / opened_qty) if opened_qty else ZERO
            same_side_lots.append(
                OpenLot(
                    side=new_lot_side,
                    remaining_qty=opened_qty,
                    open_price=fill_price,
                    multiplier=multiplier,
                    entry_commission_per_unit=entry_commission_per_unit,
                    opened_at=executed_at,
                )
            )

        self.realized_pnl += fallback_realized_pnl
        return {
            'closed_qty': closed_qty,
            'opened_qty': opened_qty,
            'fallback_realized_pnl': fallback_realized_pnl,
            'closed_lots': closed_lots,
            'multiplier': multiplier,
        }

    def get_open_qty(self) -> Decimal:
        long_qty = sum((lot.remaining_qty for lot in self.long_lots), ZERO)
        short_qty = sum((lot.remaining_qty for lot in self.short_lots), ZERO)
        return long_qty - short_qty

    def get_avg_open_cost(self):
        if self.long_lots:
            total_qty = sum((lot.remaining_qty for lot in self.long_lots), ZERO)
            total_notional = sum((lot.remaining_qty * lot.open_price for lot in self.long_lots), ZERO)
            return (total_notional / total_qty) if total_qty > ZERO else None
        if self.short_lots:
            total_qty = sum((lot.remaining_qty for lot in self.short_lots), ZERO)
            total_notional = sum((lot.remaining_qty * lot.open_price for lot in self.short_lots), ZERO)
            return (total_notional / total_qty) if total_qty > ZERO else None
        return None

    def snapshot_open_lots(self):
        snapshots = []
        for lot in self.long_lots:
            snapshots.append(
                {
                    'side': 'LONG',
                    'open_qty': lot.remaining_qty,
                    'remaining_qty': lot.remaining_qty,
                    'open_price': lot.open_price,
                    'opened_at': lot.opened_at,
                }
            )
        for lot in self.short_lots:
            snapshots.append(
                {
                    'side': 'SHORT',
                    'open_qty': -lot.remaining_qty,
                    'remaining_qty': lot.remaining_qty,
                    'open_price': lot.open_price,
                    'opened_at': lot.opened_at,
                }
            )
        return snapshots
