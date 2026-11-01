"""Export a provenance-preserving, read-only PAPER snapshot for GitHub Pages."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile

from combo.grid import GridBuilder


def build_dashboard_state(strategy, listener) -> dict:
    paper = strategy.paper
    cfg = strategy.cfg
    feed = listener.status()
    orders = []
    for order in paper.orders.values():
        orders.append({
            "order_id": order.order_id, "side": order.side, "price": order.price,
            "qty": order.qty, "filled_qty": order.filled_qty,
            "remaining_qty": order.remaining_qty, "role": order.role,
            "level_index": order.level_index, "lot_id": order.lot_id,
            "reduce_only": order.reduce_only, "status": order.status.value,
            "created_ts_ms": order.created_ts_ms, "updated_ts_ms": order.updated_ts_ms,
            "reason": order.reason, "parent_order_id": order.parent_order_id,
        })
    fills = [{
        "order_id": f.order_id, "side": f.side, "role": f.role,
        "level_index": f.level_index, "lot_id": f.lot_id, "qty": f.qty,
        "price": f.price, "fee_usdt": f.fee_usdt, "ts_ms": f.ts_ms,
    } for f in paper.fills]
    lots = [{
        "lot_id": lot.lot_id, "entry_price": lot.entry_price, "qty": lot.qty,
        "level_index": lot.level_index, "opened_ts_ms": lot.opened_ts_ms,
        "source_order_id": lot.source_order_id,
        "unrealized_gross_usdt": (float(paper.last_mark or lot.entry_price) - lot.entry_price) * lot.qty,
    } for lot in paper.position.lots.values()]
    events = [{
        "ts_ms": e.ts_ms, "kind": e.kind, "message": e.message,
        "order_id": e.order_id, "qty": e.qty, "price": e.price,
    } for e in paper.events]
    grid = GridBuilder(cfg)
    levels = []
    for level in grid.levels:
        level_orders = [o for o in orders if o["level_index"] == level.index and o["status"] in ("accepted", "partially_filled")]
        levels.append({
            "index": level.index, "price": level.price,
            "orders": level_orders,
        })
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_at_ms": int(datetime.now(timezone.utc).timestamp() * 1000),
        "execution_mode": "PAPER_ONLY",
        "symbol": cfg.symbol,
        "private_api_enabled": False,
        "live_order_submission": False,
        "market": {
            "last": paper.last_mark,
            "exchange_ts_ms": paper.last_quote_ts_ms,
        },
        "feed": feed,
        "paper": paper.snapshot(),
        "config": {
            "low_price": cfg.low_price, "high_price": cfg.high_price,
            "grid_intervals": cfg.grid_intervals, "grid_step_pct": cfg.grid_step_pct,
            "order_qty_btc": cfg.order_qty_btc, "take_profit_pct": cfg.take_profit_pct,
            "hard_stop_price": cfg.hard_stop_price,
            "estimated_funding_rate_8h": cfg.estimated_funding_rate_8h,
            "funding_is_estimate": True,
        },
        "grid_levels": levels,
        "orders": orders,
        "fills": fills,
        "lots": lots,
        "events": events,
        "last_result": listener.last_result,
        "last_error": listener.last_error,
        "provenance": "COMBO PAPER adapter + accepted public OKX ticker; no synthetic values",
    }


def write_dashboard_state(strategy, listener, destination: str | Path) -> None:
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = build_dashboard_state(strategy, listener)
    fd, temp_name = tempfile.mkstemp(prefix=target.name + ".", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, target)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
