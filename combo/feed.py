"""Independent OKX public ticker adapter; no legacy radar imports."""
from __future__ import annotations
import math
from typing import Any
from .instrument import OKXInstrumentMetadata
from .models import ComboQuote
from .strategy import ComboStrategy
from .websocket import OKXPublicFeed
class ComboWebSocketListener:
 def __init__(self,strategy:ComboStrategy,feed=None,instrument_meta:OKXInstrumentMetadata|None=None):
  self.strategy=strategy; self.feed=feed if feed is not None else OKXPublicFeed(); self.owns_feed=feed is None
  self.instrument_meta=instrument_meta or OKXInstrumentMetadata.fetch_public(strategy.cfg.symbol)
  if self.instrument_meta.inst_id!=strategy.cfg.symbol: raise ValueError("OKX metadata symbol mismatch")
  if not math.isclose(self.instrument_meta.tick_size,strategy.cfg.price_tick,rel_tol=0,abs_tol=1e-10): raise ValueError("Configured tick differs from OKX tickSz")
  self.last_result=None; self.last_error=None; self.feed.add_tick_listener(self._on_tick_event)
 def _on_tick_event(self,tick:dict[str,Any]):
  if tick.get("exchange")!="okx" or tick.get("inst")!=self.strategy.cfg.symbol:return
  try:
   if tick.get("size_unit")!="contracts_for_swap":raise ValueError("Unverified SWAP BBO size unit")
   bid=self.instrument_meta.contracts_to_btc(float(tick["bid_size_contracts"])); ask=self.instrument_meta.contracts_to_btc(float(tick["ask_size_contracts"]))
   q=ComboQuote(symbol=tick["inst"],last=float(tick["last"]),bid=float(tick["bid"]),ask=float(tick["ask"]),ts_ms=int(tick["ts_ms"]),bid_size=bid,ask_size=ask)
   self.last_result=self.strategy.on_quote(q); self.last_error=None
  except Exception as exc:self.last_error=f"{type(exc).__name__}: {exc}"
 def start(self):
  self.feed.set_symbols([self.strategy.cfg.symbol])
  if self.owns_feed and not self.feed.is_alive():self.feed.start()
 def stop(self):
  if self.owns_feed:self.feed.stop()
 def status(self):return {"feed":self.feed.status(),"owns_feed":self.owns_feed,"last_error":self.last_error,"execution_mode":"PAPER_ONLY","private_api_enabled":False,"live_order_submission":False}
