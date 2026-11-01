# Live Dashboard Contract

This dashboard is a real-time view and safe PAPER control surface for the independent COMBO service. It must never synthesize exchange, order, fill, PnL, funding, or health data.

## Data provenance

- Market price and BBO: accepted OKX public `BTC-USDT-SWAP` ticker updates only.
- Chart: timestamped accepted ticker samples from the live listener. If candle history is not available, render a live price trace rather than fabricated OHLC candles.
- Trade markers: derive only from persisted `ComboFill` records and journal events. Every marker carries the source order ID, fill timestamp, side, quantity, price, and role.
- Orders: derive from `ComboPaperAdapter.orders`; show active, partial, filled, cancelled and rejected states separately.
- Positions/lots: derive from `ComboPosition` lots, preserving lot IDs and source order IDs.
- Wallet, equity, margin, fees, funding, realized and unrealized PnL: use PAPER adapter calculations and label the estimated funding assumption.
- Feed health: use actual WebSocket connection, message age, tick and reconnect counters. Stale/disconnected data must be visibly marked and must not be presented as live.

## Mobile navigation

1. Overview: market status, account/PAPER metrics, live chart and execution markers.
2. Grid: 25 configured levels, live active order state per level.
3. Virtual trades: one row/card per PAPER lot/trade with open/closed state, entry/exit fills, fees, funding and realized/unrealized PnL. Link every row to source fills and order IDs.
4. Events: append-only event journal with timestamp and event type.
5. Settings: real service controls and validated configuration. No decorative controls.

## Chart execution markers

- BUY fill: green upward marker.
- SELL fill: red downward marker.
- Partial fill: outlined marker with partial quantity.
- TP / hard-stop: distinct labeled markers.
- Order accepted/cancelled/rejected: optional event pins, visually distinct from fills.
- Marker selection opens the exact source order/fill details.
- Chart and marker timestamps use exchange timestamps; do not infer a fill from price crossing alone.

## Settings safety contract

- The dashboard remains PAPER-only. No private API credentials, private account channels, live order endpoints, shorting or hedge controls.
- Safe runtime controls may pause/resume new BUY entries and cancel pending BUY orders. Reduce-only exits and risk-reduction behavior must remain available while entries are paused.
- Strategy-defining values (symbol, price band, 24 intervals, 0.013 BTC order size, LONG-only, TP and hard stop) are read-only in the UI unless a separately reviewed, validated configuration migration is implemented.
- Risk settings must be validated against `ComboConfig`, persisted atomically, surfaced with their applied/restart-required status, and never silently diverge from the running strategy.
- Every mutating action must return a success/error result and create a timestamped audit event. No UI-only optimistic success.

## Delivery gates

- Unit tests for API payload provenance, marker-to-fill mapping, stale feed display, settings validation, pause/resume, pending BUY cancellation and persistence/recovery.
- Real OKX public-feed smoke test with zero private API usage and zero live order submission.
- Browser/mobile responsive test.
- Dashboard must not be called live/complete until a real running service has supplied the values and the end-to-end checks pass.
