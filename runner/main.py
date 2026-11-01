"""PAPER-only runner with periodic, provenance-preserving dashboard snapshots."""
import argparse
import json
import time
from pathlib import Path

from combo.config import ComboConfig
from combo.strategy import ComboStrategy
from combo.feed import ComboWebSocketListener
from runner.lifecycle import RunnerLease
from runner.dashboard_state import write_dashboard_state


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", default="./state")
    parser.add_argument("--smoke-seconds", type=int, default=0,
                        help="Exit after this many seconds; requires at least one real OKX ticker.")
    parser.add_argument("--dashboard-state", default=None,
                        help="Atomically write a read-only dashboard JSON snapshot.")
    parser.add_argument("--dashboard-interval", type=float, default=15.0,
                        help="Seconds between dashboard snapshots in continuous mode (5..300).")
    parser.add_argument("--checkpoint-interval", type=float, default=60.0,
                        help="Maximum interval between durable PAPER checkpoints in continuous mode (15..3600).")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if args.smoke_seconds < 0 or args.smoke_seconds > 600:
        parser.error("--smoke-seconds must be between 0 and 600")
    if not 5 <= args.dashboard_interval <= 300:
        parser.error("--dashboard-interval must be between 5 and 300 seconds")
    if not 15 <= args.checkpoint_interval <= 3600:
        parser.error("--checkpoint-interval must be between 15 and 3600 seconds")
    if args.checkpoint_interval < args.dashboard_interval:
        parser.error("--checkpoint-interval must be >= --dashboard-interval")

    root = Path(args.state_dir)
    with RunnerLease(root / "runner.lock"):
        strategy = ComboStrategy(ComboConfig(), root=root)
        # In dashboard mode, normal quotes are not checkpointed one-by-one.
        # Strategy events/fills still checkpoint immediately; this interval adds
        # a bounded durability checkpoint even when the market is quiet.
        strategy.persist_each_quote = not bool(args.dashboard_state)
        listener = ComboWebSocketListener(strategy)
        listener.start()
        started = time.monotonic()
        try:
            if args.smoke_seconds:
                while time.monotonic() - started < args.smoke_seconds:
                    time.sleep(1)
                feed_status = listener.status()
                result = {
                    "execution_mode": "PAPER_ONLY",
                    "private_api_enabled": False,
                    "live_order_submission": False,
                    "feed": feed_status,
                    "last_result": listener.last_result,
                    "last_error": listener.last_error,
                    "paper": strategy.paper.snapshot(),
                }
                if args.dashboard_state:
                    strategy.paper.save()
                    write_dashboard_state(strategy, listener, args.dashboard_state)
                print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)
                if feed_status.get("feed", {}).get("ticks", 0) < 1 or strategy.paper.last_quote_ts_ms is None:
                    raise SystemExit("No valid OKX public ticker was processed during smoke window")
            else:
                next_dashboard = started
                next_checkpoint = started + args.checkpoint_interval
                while True:
                    now = time.monotonic()
                    if args.dashboard_state and now >= next_dashboard:
                        if now >= next_checkpoint:
                            strategy.paper.save()
                            next_checkpoint = now + args.checkpoint_interval
                        write_dashboard_state(strategy, listener, args.dashboard_state)
                        next_dashboard = now + args.dashboard_interval
                    time.sleep(0.25)
        except KeyboardInterrupt:
            pass
        finally:
            listener.stop()
            if args.dashboard_state and not args.smoke_seconds:
                strategy.paper.save()
                write_dashboard_state(strategy, listener, args.dashboard_state)


if __name__ == "__main__":
    main()
