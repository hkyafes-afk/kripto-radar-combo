"""Exclusive local runner lease. Existing lock always blocks a second runner."""
import json,os,socket
from pathlib import Path
class AlreadyRunning(RuntimeError):pass
class RunnerLease:
 def __init__(self,path):self.path=Path(path);self.fd=None
 def acquire(self):
  self.path.parent.mkdir(parents=True,exist_ok=True)
  try:self.fd=os.open(self.path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
  except FileExistsError as e:raise AlreadyRunning("runner lease exists; refusing duplicate process") from e
  os.write(self.fd,json.dumps({"pid":os.getpid(),"host":socket.gethostname()}).encode());os.fsync(self.fd);return self
 def release(self):
  if self.fd is not None:
   os.close(self.fd);self.fd=None
   try:self.path.unlink()
   except FileNotFoundError:pass
 def __enter__(self):return self.acquire()
 def __exit__(self,*exc):self.release()
