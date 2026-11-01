from __future__ import annotations

import json
import time

from combo.config import ComboConfig
from combo.models import ComboQuote
from combo.strategy import ComboStrategy
from runner.dashboard_state import build_dashboard_state, write_dashboard_state


class FakeListener:
    last_result = {"status": "base_opened"}
    last_error = None

    def status(self):
        return {
            "feed": {"connected": True, "healthy": True, "ticks": 1, "reconnects": 0},
            "execution_mode": "PAPER_ONLY",
            "private_api_enabled": False,
            "live_order_submission": False,
        }


def test_dashboard_state_uses_real_paper_objects_and_fill_provenance(tmp_path):
    now = int(time.time() * 1000)
    strategy = ComboStrategy(ComboConfig())
    quote = ComboQuote(
        symbol="BTC-USDT-SWAP", bid=77_999.9, ask=78_000.1, last=78_000.0,
        ts_ms=now, bid_size=0.05, ask_size=0.05,
    )
    strategy.on_quote(quote, now_ms=now)

    state = build_dashboard_state(strategy, FakeListener())
    assert state["execution_mode"] == "PAPER_ONLY"
    assert state["private_api_enabled"] is False
    assert state["live_order_submission"] is False
    assert state["paper"]["position_qty_btc"] == 0.013
    assert state["fills"][0]["side"] == "buy"
    assert state["fills"][0]["order_id"]
    assert state["fills"][0]["ts_ms"] == now
    assert len(state["grid_levels"]) == 25
    assert state["market"]["exchange_ts_ms"] == now

    target = tmp_path / "state.json"
    write_dashboard_state(strategy, FakeListener(), target)
    saved = json.loads(target.read_text(encoding="utf-8"))
    assert saved["fills"] == state["fills"]
    assert saved["paper"]["equity_usdt"] == state["paper"]["equity_usdt"]
