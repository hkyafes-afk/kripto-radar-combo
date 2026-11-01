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
