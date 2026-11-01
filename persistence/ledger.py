"""Hash-chained append-only JSONL journal with fsync and idempotency keys."""
from __future__ import annotations
import hashlib,json,os
from pathlib import Path
from threading import RLock
class LedgerCorruption(RuntimeError):pass
class EventLedger:
 GENESIS="0"*64
 def __init__(self,path):self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True);self._lock=RLock();self._ids=set();self._seq=0;self._prev=self.GENESIS;self.verify()
 @staticmethod
 def canonical(x):return json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False)
 def verify(self):
  with self._lock:
   self._ids=set();self._seq=0;self._prev=self.GENESIS;rows=[]
   if not self.path.exists():return rows
   with self.path.open(encoding="utf-8") as f:
    for n,line in enumerate(f,1):
     try:r=json.loads(line)
     except Exception as e:raise LedgerCorruption(f"invalid JSON line {n}") from e
     if set(r)!={"seq","event_id","kind","payload","prev_hash","hash"}:raise LedgerCorruption(f"invalid schema line {n}")
     if r["seq"]!=n or r["prev_hash"]!=self._prev:raise LedgerCorruption(f"chain break line {n}")
     if r["event_id"] in self._ids:raise LedgerCorruption(f"duplicate id line {n}")
     body={k:r[k] for k in ("seq","event_id","kind","payload","prev_hash")};h=hashlib.sha256(self.canonical(body).encode()).hexdigest()
     if h!=r["hash"]:raise LedgerCorruption(f"hash mismatch line {n}")
     self._ids.add(r["event_id"]);self._seq=n;self._prev=h;rows.append(r)
   return rows
 def append(self,event_id,kind,payload):
  if not event_id or not kind or not isinstance(payload,dict):raise ValueError("event_id, kind and dict payload required")
  with self._lock:
   if event_id in self._ids:return None
   body={"seq":self._seq+1,"event_id":event_id,"kind":kind,"payload":payload,"prev_hash":self._prev};h=hashlib.sha256(self.canonical(body).encode()).hexdigest();rec={**body,"hash":h}
   fd=os.open(self.path,os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
   with os.fdopen(fd,"a",encoding="utf-8") as f:f.write(self.canonical(rec)+"\n");f.flush();os.fsync(f.fileno())
   self._seq+=1;self._prev=h;self._ids.add(event_id);return rec
 @property
 def last_seq(self):return self._seq
