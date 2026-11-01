"""Minimal public OKX ticker feed. No credentials, private channels or Bitget."""
from __future__ import annotations
import json,threading,time
import websocket
class OKXPublicFeed(threading.Thread):
 URL="wss://ws.okx.com:8443/ws/v5/public"
 def __init__(self):
  super().__init__(daemon=True,name="combo-okx-public"); self.symbols=[]; self.listeners=[]; self.stop_event=threading.Event(); self.connected=False; self.error=""; self.msgs=0; self.ticks=0; self.reconnects=0; self.last_msg=0.; self._ws=None; self._lock=threading.RLock()
 def add_tick_listener(self,cb):
  if not callable(cb):raise TypeError("listener must be callable")
  with self._lock:
   if cb not in self.listeners:self.listeners.append(cb)
 def set_symbols(self,symbols):
  syms=sorted(set(symbols))
  if any(not isinstance(s,str) or not s.endswith("-SWAP") for s in syms):raise ValueError("Only SWAP IDs supported")
  with self._lock:self.symbols=syms
 def status(self):
  age=time.time()-self.last_msg if self.last_msg else None
  return {"connected":self.connected,"healthy":self.connected and age is not None and age<15,"last_msg_age_s":age,"msgs":self.msgs,"ticks":self.ticks,"reconnects":self.reconnects,"symbols":len(self.symbols),"error":self.error[:200]}
 def stop(self):
  self.stop_event.set()
  try:
   if self._ws:self._ws.close()
  except Exception:pass
 def run(self):
  backoff=1.
  while not self.stop_event.is_set():
   with self._lock:syms=list(self.symbols)
   if not syms:self.stop_event.wait(.25);continue
   try:
    self._ws=websocket.create_connection(self.URL,timeout=5,enable_multithread=True)
    self._ws.send(json.dumps({"op":"subscribe","args":[{"channel":"tickers","instId":s} for s in syms]}));self.connected=True;self.error="";backoff=1.
    while not self.stop_event.is_set():
     try:raw=self._ws.recv()
     except websocket.WebSocketTimeoutException:
      if self.last_msg and time.time()-self.last_msg>30:raise TimeoutError("OKX public ticker stale for 30 seconds")
      continue
     if raw is None:raise ConnectionError("OKX socket closed")
     self.last_msg=time.time();self.msgs+=1
     if raw=="ping":self._ws.send("pong");continue
     if raw=="pong":continue
     obj=json.loads(raw)
     if obj.get("event")=="error":raise RuntimeError("OKX subscription error: "+str(obj.get("msg","unknown")))
     if (obj.get("arg") or {}).get("channel")!="tickers":continue
     for d in obj.get("data") or []:
      event={"exchange":"okx","inst":d["instId"],"last":float(d["last"]),"bid":float(d["bidPx"]),"ask":float(d["askPx"]),"bid_size_contracts":float(d["bidSz"]),"ask_size_contracts":float(d["askSz"]),"size_unit":"contracts_for_swap","ts_ms":int(d["ts"])};self.ticks+=1
      with self._lock:cbs=tuple(self.listeners)
      for cb in cbs:cb(dict(event))
   except Exception as exc:self.error=f"{type(exc).__name__}: {exc}"
   finally:
    self.connected=False
    try:
     if self._ws:self._ws.close()
    except Exception:pass
    self._ws=None
   if not self.stop_event.is_set():self.reconnects+=1;self.stop_event.wait(backoff);backoff=min(backoff*2,30)
