from __future__ import annotations

from pathlib import Path
import uuid

from django.conf import settings
from PIL import Image, ImageDraw, ImageFont

from apps.trades.models import RawIBKRExecution, TradeGroup
from .models import TradeJournal


BG_COLOR = (19, 23, 34)
GRID_COLOR = (52, 58, 73)
LINE_COLOR = (95, 138, 255)
BUY_COLOR = (42, 189, 130)
SELL_COLOR = (240, 75, 75)
TEXT_COLOR = (220, 224, 235)
MUTED_TEXT_COLOR = (142, 151, 172)



def _safe_float(value):
    try:
        return float(value)
    except Exception:
        return 0.0



def _build_chart_points(executions, width, height, left_pad, top_pad, right_pad, bottom_pad):
    prices = [_safe_float(item.price) for item in executions]
    if not prices:
        return []

    min_price = min(prices)
    max_price = max(prices)
    if max_price == min_price:
        max_price = min_price + 1

    plot_width = width - left_pad - right_pad
    plot_height = height - top_pad - bottom_pad
    size = len(executions)

    points = []
    for idx, item in enumerate(executions):
        price = _safe_float(item.price)
        x = left_pad + (plot_width * idx / max(1, size - 1))
        y_ratio = (price - min_price) / (max_price - min_price)
        y = top_pad + (plot_height * (1 - y_ratio))
        points.append((x, y, item))

    return points



def _draw_marker(draw, x, y, is_buy):
    size = 8
    if is_buy:
        color = BUY_COLOR
        triangle = [(x, y - size), (x - size, y + size), (x + size, y + size)]
    else:
        color = SELL_COLOR
        triangle = [(x, y + size), (x - size, y - size), (x + size, y - size)]
    draw.polygon(triangle, fill=color)



def generate_trade_snapshot(symbol: str, trade_date, executions):
    width, height = 1600, 900
    left_pad, top_pad, right_pad, bottom_pad = 110, 100, 80, 120

    image = Image.new('RGB', (width, height), BG_COLOR)
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    # grid
    grid_rows = 6
    grid_cols = 8
    for r in range(grid_rows + 1):
        y = top_pad + ((height - top_pad - bottom_pad) * r / grid_rows)
        draw.line([(left_pad, y), (width - right_pad, y)], fill=GRID_COLOR, width=1)
    for c in range(grid_cols + 1):
        x = left_pad + ((width - left_pad - right_pad) * c / grid_cols)
        draw.line([(x, top_pad), (x, height - bottom_pad)], fill=GRID_COLOR, width=1)

    points = _build_chart_points(executions, width, height, left_pad, top_pad, right_pad, bottom_pad)
    if points:
        draw.line([(x, y) for x, y, _ in points], fill=LINE_COLOR, width=3)
        for x, y, item in points:
            is_buy = (item.side or '').upper() == 'BUY'
            _draw_marker(draw, x, y, is_buy)

    title = f"{symbol} · {trade_date} · TradingView-style Snapshot"
    draw.text((left_pad, 40), title, fill=TEXT_COLOR, font=font)
    draw.text((left_pad, height - 70), '▲ BUY marker   ▼ SELL marker   |   Auto generated from IBKR executions', fill=MUTED_TEXT_COLOR, font=font)

    file_name = f"trade_snapshots/{symbol}_{trade_date}_{uuid.uuid4().hex}.png".replace(':', '_')
    file_path = Path(settings.MEDIA_ROOT) / file_name
    file_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(file_path, format='PNG')

    return settings.MEDIA_URL + file_name



def ensure_trade_journal_snapshots(trade_dates):
    if not trade_dates:
        return 0

    updated_count = 0
    groups = TradeGroup.objects.filter(trade_date__in=trade_dates).order_by('trade_date', 'symbol', 'id')
    for group in groups:
        executions = list(
            RawIBKRExecution.objects.filter(symbol=group.symbol, trade_date=group.trade_date)
            .order_by('executed_at', 'id')
        )
        if not executions:
            continue

        snapshot_relative_url = generate_trade_snapshot(group.symbol, group.trade_date, executions)
        journal, _ = TradeJournal.objects.get_or_create(trade_group=group)
        journal.tv_snapshot_url = snapshot_relative_url
        journal.save(update_fields=['tv_snapshot_url', 'updated_at'])
        updated_count += 1

    return updated_count
