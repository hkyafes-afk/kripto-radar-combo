"""PAPER-only runner entry point."""
import argparse,time
from pathlib import Path
from combo.config import ComboConfig
from combo.strategy import ComboStrategy
from combo.feed import ComboWebSocketListener
from runner.lifecycle import RunnerLease
def main():
 p=argparse.ArgumentParser();p.add_argument("--state-dir",default="./state");a=p.parse_args();root=Path(a.state_dir);strategy=ComboStrategy(ComboConfig(),root=root)
 with RunnerLease(root/"runner.lock"):
  listener=ComboWebSocketListener(strategy);listener.start()
  try:
   while True:time.sleep(1)
  except KeyboardInterrupt:pass
  finally:listener.stop()
if __name__=="__main__":main()
