"""Exclusive local runner lease. Existing lock always blocks a second runner."""
import json,os,socket
from pathlib import Path
class AlreadyRunning(RuntimeError):pass
class RunnerLease:
 def __init__(self,path):self.path=Path(path);self.fd=None;self.identity=None
 def acquire(self):
  self.path.parent.mkdir(parents=True,exist_ok=True)
  try:self.fd=os.open(self.path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
  except FileExistsError as e:raise AlreadyRunning("runner lease exists; refusing duplicate process") from e
  st=os.fstat(self.fd);self.identity=(st.st_dev,st.st_ino)
  os.write(self.fd,json.dumps({"pid":os.getpid(),"host":socket.gethostname()}).encode());os.fsync(self.fd);return self
 def release(self):
  if self.fd is not None:
   os.close(self.fd);self.fd=None
   try:
    st=self.path.stat()
    if self.identity==(st.st_dev,st.st_ino):self.path.unlink()
   except FileNotFoundError:pass
   self.identity=None
 def __enter__(self):return self.acquire()
 def __exit__(self,*exc):self.release()
