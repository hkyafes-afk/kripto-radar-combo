# Kripto Radar COMBO

Independent BTC-USDT-SWAP grid service, PAPER-only.

## Safety boundary
- Public OKX ticker feed only; no private credentials, account channels or live orders.
- LONG-only; SELL orders are reduce-only and tied to inventory lots.
- Invalid, stale, duplicate and out-of-order quotes are rejected.
- Visible BBO sizes are converted from contracts to BTC using public instrument metadata. No depth or queue simulation is claimed.
- Runner uses an exclusive local process lease.
- Append-only journal is hash chained and fsynced; recovery uses the latest verified durable checkpoint and fails closed on corruption.

## Run
Python 3.11+: install with python -m pip install -e .[test], run tests with python -m pytest -q, start with python -m runner.main --state-dir ./state.

No private API keys are used. Live execution is intentionally unsupported.

## PAPER risk guards

See [docs/RISK_GUARDS.md](docs/RISK_GUARDS.md) for the lower-band DCA pause, 15% free-margin threshold, BBO-only gap handling, 200ms per-level cooldown and estimated 8-hour LONG funding charge. Funding is a configurable simulation estimate, not live OKX funding data.


## VM live dashboard publishing

The long-running VM runner can write a read-only dashboard snapshot every 15 seconds while durable PAPER checkpoints continue at a bounded interval. The separate publisher validates the snapshot provenance, recent healthy public OKX ticker, hash-chained journal and matching recovery checkpoint before publishing.

The dashboard reads `state.json` from the dedicated `paper-live-state` branch. The publisher mirrors only the latest verified dashboard state and runtime ledger files to that branch; it amends its dedicated publish commit so the branch does not accumulate one commit per refresh. It never writes to `main`. The VM engine and the manual GitHub Actions PAPER workflow must never be run at the same time.

After reviewing and merging the VM publisher PR:

1. On the VM, run `bash ops/install-user-services.sh` to install user units. This only installs files; it does not start or enable the engine.
2. Run `bash ops/setup-deploy-key.sh`. Add the displayed **public** key under repository Settings → Deploy keys, enable write access, and never share the private key.
3. Enable the publisher timer with `systemctl --user enable --now combo-dashboard-publish.timer`.
4. Verify one publisher run with `systemctl --user start combo-dashboard-publish.service` and inspect `systemctl --user status combo-dashboard-publish.service --no-pager`.
5. Only after the SSH publish succeeds, start the PAPER engine with `systemctl --user enable --now combo-paper.service`.

The dashboard's market ticker remains directly connected to OKX WebSocket. PAPER wallet/order/fill/event snapshots are refreshed approximately once per minute; this is not millisecond-level dashboard state. If the public feed is unhealthy, the ticker is stale, or the journal/checkpoint fails verification, the publisher refuses to publish and the dashboard eventually marks the last snapshot stale. No private API credentials or live orders are used.
