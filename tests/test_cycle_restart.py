"""MAIN_TP sonrası yeni döngü: ledger korunur, bant ortalanır, HARD_STOP kalıcıdır."""
from combo.config import ComboConfig
from combo.models import ComboQuote
from combo.strategy import ComboStrategy

NOW = 1_800_000_000_000


def quote(last, ts=NOW):
    return ComboQuote("BTC-USDT-SWAP", last - 0.1, last + 0.1, last, ts, 0.05, 0.05)


def halted_strategy(tmp_path, reason="MAIN_TP", restart=True):
    s = ComboStrategy(ComboConfig(), root=tmp_path)
    s.cycle_restart = restart
    p = s.paper
    p.initialized = True
    p.grid_seeded = True
    p.tp_triggered = True
    p.halted = True
    p.halt_reason = reason
    p.last_funding_ts_ms = NOW
    p.fees_paid_usdt = 1.5
    p.realized_gross_usdt = 10.0
    return s


def test_new_cycle_recenters_band_and_keeps_ledger_totals(tmp_path):
    s = halted_strategy(tmp_path)
    res = s.on_quote(quote(90_000.0), NOW)
    assert res["status"] == "base_opened"
    assert s.cfg.low_price < 90_000.0 < s.cfg.high_price
    assert s.cfg.hard_stop_price < s.cfg.low_price
    assert not s.paper.halted and s.paper.halt_reason is None
    assert s.paper.realized_gross_usdt == 10.0
    assert s.paper.fees_paid_usdt >= 1.5
    assert any(e.kind == "cycle_restart" for e in s.paper.events)


def test_recentered_band_survives_restart(tmp_path):
    s = halted_strategy(tmp_path)
    s.on_quote(quote(90_000.0), NOW)
    s2 = ComboStrategy(ComboConfig(), root=tmp_path)
    assert s2.cfg.low_price == s.cfg.low_price
    assert s2.cfg.high_price == s.cfg.high_price


def test_lot_scales_with_equity(tmp_path):
    s = halted_strategy(tmp_path)
    s.lot_equity_fraction = 0.16
    s.on_quote(quote(90_000.0), NOW)
    assert 0.004 <= s.cfg.order_qty_btc <= 0.0045


def test_hard_stop_stays_halted(tmp_path):
    s = halted_strategy(tmp_path, reason="HARD_STOP")
    res = s.on_quote(quote(90_000.0), NOW)
    assert res["status"] == "halted_hard_stop"
    assert s.paper.halted and s.paper.halt_reason == "HARD_STOP"


def test_flag_off_keeps_old_behavior(tmp_path):
    s = halted_strategy(tmp_path, restart=False)
    res = s.on_quote(quote(90_000.0), NOW)
    assert res["status"] == "halted"
    assert s.paper.halt_reason == "MAIN_TP"


def test_cooldown_blocks_restart(tmp_path):
    s = halted_strategy(tmp_path)
    s.cycle_cooldown_ms = 10 ** 15
    res = s.on_quote(quote(90_000.0), NOW)
    assert res["status"] == "halted"


def test_drop_guard_defers_new_cycle_then_resumes(tmp_path):
    s = halted_strategy(tmp_path)
    s.drop_guard_pct = 0.02
    s._px_hist = [(NOW - 600_000, 90_000.0)]                     # son saatte yüksek fiyat
    res = s.on_quote(quote(87_000.0, NOW), NOW)                  # ~3.3% düşüş
    assert res["status"] == "halted"
    assert any(e.kind == "cycle_wait_drop" for e in s.paper.events)
    later = NOW + 4_000_000                                      # düşüş penceresi geçti
    res = s.on_quote(quote(87_000.0, later), later)
    assert res["status"] == "base_opened"


def test_drop_guard_off_by_default(tmp_path):
    s = halted_strategy(tmp_path)
    s._px_hist = [(NOW - 600_000, 90_000.0)]
    res = s.on_quote(quote(80_000.0, NOW), NOW)
    assert res["status"] == "base_opened"
