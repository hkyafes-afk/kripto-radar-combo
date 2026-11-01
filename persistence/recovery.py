"""Fail-closed snapshot recovery from the latest verified journal checkpoint."""
from __future__ import annotations
import json,os,tempfile
from pathlib import Path
class RecoveryError(RuntimeError):pass
class RecoveryManager:
 def __init__(self,ledger):self.ledger=ledger
 def write_checkpoint(self,path,state,checkpoint_id):
  rec=self.ledger.append(checkpoint_id,"state_checkpoint",{"state":state})
  if rec is None:raise RecoveryError("duplicate checkpoint id")
  wrapper={"schema_version":1,"ledger_seq":rec["seq"],"ledger_hash":rec["hash"],"state":state};target=Path(path);target.parent.mkdir(parents=True,exist_ok=True)
  fd,tmp=tempfile.mkstemp(prefix=target.name+".",dir=target.parent)
  try:
   with os.fdopen(fd,"w",encoding="utf-8") as f:json.dump(wrapper,f,sort_keys=True,separators=(",",":"),allow_nan=False);f.flush();os.fsync(f.fileno())
   os.replace(tmp,target);dfd=os.open(target.parent,os.O_RDONLY)
   try:os.fsync(dfd)
   finally:os.close(dfd)
  finally:
   if os.path.exists(tmp):os.unlink(tmp)
 def recover(self,path):
  rows=self.ledger.verify();checkpoints=[r for r in rows if r["kind"]=="state_checkpoint"];target=Path(path)
  if not checkpoints:
   if target.exists() or rows:raise RecoveryError("state or journal events exist without a durable checkpoint")
   return None
  latest=checkpoints[-1]
  if latest["seq"] != len(rows):raise RecoveryError("uncheckpointed journal tail; fail closed")
  if target.exists():
   try:s=json.loads(target.read_text(encoding="utf-8"))
   except Exception as e:raise RecoveryError("snapshot unreadable; fail closed") from e
   if s.get("schema_version")!=1:raise RecoveryError("snapshot schema mismatch")
   if s.get("ledger_seq",0)>latest["seq"]:raise RecoveryError("snapshot ahead of journal")
   if s.get("ledger_seq")==latest["seq"] and s.get("ledger_hash")!=latest["hash"]:raise RecoveryError("snapshot hash mismatch")
  return latest["payload"]["state"]
