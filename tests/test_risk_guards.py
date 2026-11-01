import pytest
from combo.config import ComboConfig
from combo.models import ComboQuote, ComboOrderStatus
from combo.paper import ComboPaperAdapter
from combo.position import LongLot
from combo.strategy import ComboStrategy

NOW = 1_800_000_000_000

def q(last, *, bid=None, ask=None, bid_size=.1, ask_size=.1, ts=NOW):
    return ComboQuote("BTC-USDT-SWAP", bid if bid is not None else last-.1,
                      ask if ask is not None else last+.1, last, ts, bid_size, ask_size)

def test_low_boundary_guard_cancels_dca_but_preserves_reduce_only_sells():
    s=ComboStrategy();s.on_quote(q(78000),now_ms=NOW)
    buys=[o for o in s.paper.orders.values() if o.active and o.side=="buy"]
    sells=[o for o in s.paper.orders.values() if o.active and o.side=="sell"]
    assert buys and sells
    mark=s.cfg.low_price*1.01
    result=s.on_quote(q(mark,bid=mark-.1,ask=mark+.1,ts=NOW+1000),now_ms=NOW+1000)
    assert result["status"]=="active"
    assert all(not o.active for o in buys)
    assert any(o.active and o.side=="sell" and o.reduce_only for o in s.paper.orders.values())
    assert any(e.kind=="dca_paused" for e in s.paper.events)

def test_free_margin_below_15_percent_pauses_new_buys():
    s=ComboStrategy();s.on_quote(q(78000),now_ms=NOW)
    s.paper.fees_paid_usdt=2490
    mark=78000
    assert s.paper.free_margin_ratio(mark)<.15
    s.on_quote(q(mark,ts=NOW+1000),now_ms=NOW+1000)
    assert not any(o.active and o.side=="buy" for o in s.paper.orders.values())

def test_gap_crossing_multiple_grid_levels_executes_only_at_current_bbo():
    s=ComboStrategy();s.on_quote(q(78000),now_ms=NOW)
    buys=sorted([o for o in s.paper.orders.values() if o.active and o.side=="buy"],
                key=lambda o:o.price,reverse=True)
    assert len(buys)>=2
    ask=buys[1].price-.1
    result=s.on_quote(q(ask-.1,bid=ask-.2,ask=ask,ask_size=.026,ts=NOW+1000),now_ms=NOW+1000)
    filled=[f for f in s.paper.fills if f.side=="buy" and f.ts_ms==NOW+1000]
    assert len(filled)==2
    assert all(f.price==pytest.approx(ask) for f in filled)
    assert result["last_gap_levels_skipped"]>=1
    assert any(e.kind=="gap_quote" for e in s.paper.events)

def test_same_grid_level_has_minimum_200ms_cooldown():
    p=ComboPaperAdapter(ComboConfig());p.last_mark=78000
    first=p.place_limit(side="buy",price=77000,qty=.013,role="dca_buy",
                        level_index=7,now_ms=1000)
    assert first is not None
    first.status=ComboOrderStatus.CANCELLED
    assert p.place_limit(side="buy",price=77000,qty=.013,role="dca_buy",
                         level_index=7,now_ms=1199) is None
    second=p.place_limit(side="buy",price=77000,qty=.013,role="dca_buy",
                         level_index=7,now_ms=1200)
    assert second is not None

def test_funding_fee_posts_each_eight_hour_period_and_hits_net_equity():
    s=ComboStrategy();s.on_quote(q(78000),now_ms=NOW)
    start_fees=s.paper.fees_paid_usdt
    start_funding=s.paper.funding_fees_usdt
    s.on_quote(q(78000,ts=NOW+s.cfg.funding_interval_ms),now_ms=NOW+s.cfg.funding_interval_ms)
    expected=.013*78000*s.cfg.estimated_funding_rate_8h
    assert s.paper.funding_fees_usdt-start_funding==pytest.approx(expected)
    assert s.paper.fees_paid_usdt-start_fees==pytest.approx(expected)
    assert s.paper.snapshot()["funding_fees_usdt"]==pytest.approx(expected)

def test_funding_and_throttle_state_survive_restart(tmp_path):
    p=ComboPaperAdapter(ComboConfig(),root=tmp_path);p.last_mark=78000
    p.last_funding_ts_ms=NOW;p.last_level_action_ms["9"]=NOW
    p.funding_fees_usdt=1.23;p.fees_paid_usdt=1.23
    p.save()
    recovered=ComboPaperAdapter(ComboConfig(),root=tmp_path)
    assert recovered.last_funding_ts_ms==NOW
    assert recovered.last_level_action_ms["9"]==NOW
    assert recovered.funding_fees_usdt==pytest.approx(1.23)
    assert recovered.fees_paid_usdt==pytest.approx(1.23)

def test_invalid_risk_guard_configuration_is_rejected():
    with pytest.raises(ValueError):ComboConfig(order_update_cooldown_ms=199)
    with pytest.raises(ValueError):ComboConfig(min_free_margin_ratio=0)
