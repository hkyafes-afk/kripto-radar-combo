"""PAPER-only runner; optional bounded live-public-data smoke mode."""
import argparse
import json
import time
from pathlib import Path

from combo.config import ComboConfig
from combo.strategy import ComboStrategy
from combo.feed import ComboWebSocketListener
from runner.lifecycle import RunnerLease


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", default="./state")
    parser.add_argument("--smoke-seconds", type=int, default=0,
                        help="Exit after this many seconds; requires at least one real OKX ticker.")
    args = parser.parse_args()
    if args.smoke_seconds < 0 or args.smoke_seconds > 600:
        parser.error("--smoke-seconds must be between 0 and 600")
    root = Path(args.state_dir)
    with RunnerLease(root / "runner.lock"):
        strategy = ComboStrategy(ComboConfig(), root=root)
        listener = ComboWebSocketListener(strategy)
        listener.start()
        started = time.monotonic()
        try:
            if args.smoke_seconds:
                while time.monotonic() - started < args.smoke_seconds:
                    time.sleep(1)
                feed_status = listener.feed.status()
                result = {
                    "execution_mode": "PAPER_ONLY",
                    "private_api_enabled": False,
                    "live_order_submission": False,
                    "feed": feed_status,
                    "last_result": listener.last_result,
                    "last_error": listener.last_error,
                    "paper": strategy.paper.snapshot(),
                }
                print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)
                if feed_status.get("ticks", 0) < 1 or strategy.paper.last_quote_ts_ms is None:
                    raise SystemExit("No valid OKX public ticker was processed during smoke window")
            else:
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            listener.stop()


if __name__ == "__main__":
    main()
