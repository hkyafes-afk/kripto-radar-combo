# GitHub Actions PAPER runtime

## Architecture

The scheduled workflow runs a bounded PAPER session on a GitHub-hosted runner:

1. Checkout the last committed `runtime/combo_paper.json` and hash-chained `runtime/events.jsonl`.
2. Start the existing COMBO PAPER adapter and connect only to the public OKX `BTC-USDT-SWAP` ticker.
3. Process actual accepted ticker/BBO updates for up to 210 seconds.
4. Atomically export `state.json` from the adapter's actual wallet, orders, fills, lots, events, grid and feed-health objects.
5. Commit the durable PAPER checkpoint/journal and dashboard snapshot back to `main`.

The workflow is scheduled every five minutes and can also be started manually from Actions. Concurrency is serialized so two PAPER cycles cannot intentionally mutate the same state at once. Failed/no-ticker runs do not publish a new snapshot.

## Dashboard data

The static dashboard fetches the public raw `state.json` file and polls it every 20 seconds. Public OKX ticker display remains a direct browser WebSocket. PAPER values are snapshots from the last successful Actions cycle, not a continuous API stream. The dashboard marks a snapshot older than ten minutes as stale.

BUY/SELL markers are drawn only when a persisted fill timestamp overlaps the browser's currently visible ticker trace. All fills remain listed in the Virtual Trades tab even when they fall outside that short chart window.

## Hard limitations

- GitHub Actions is not a continuously running server. A scheduled workflow has a five-minute minimum cron interval, can start late, and may be delayed or skipped. Each run observes the market only during its bounded execution window.
- This is not millisecond-live execution or a 24/7 WebSocket connection. Price can move between cycles and those unseen ticks are not simulated.
- The PAPER ledger and `state.json` are committed to this public repository. They are publicly readable. They contain simulated balances, strategy state, orders and fills; do not add credentials or personal information.
- GitHub Actions write permission is used only by this trusted scheduled/manual workflow to commit the PAPER state. No workflow runs with write access on pull requests.
- Dashboard controls remain read-only. GitHub Pages is static and there is no authenticated command channel. No settings or trading controls are exposed to anonymous browser users.
- The workflow must never submit exchange orders or use private OKX credentials. It is PAPER-only.

## Starting and monitoring

Open **Actions → COMBO GitHub Actions PAPER engine → Run workflow** for a manual cycle. Check the latest run result and commit timestamp. If the last successful `state.json` is stale, the dashboard must show that condition rather than reuse it as live data.
