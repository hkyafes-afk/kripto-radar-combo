# COMBO PAPER risk guards

These defaults are conservative PAPER simulation rules, not an exchange liquidation guarantee.

- **DCA boundary guard:** stop placing and cancel outstanding BUY/DCA orders once the last price is within 2% above the configured lower grid boundary. Reduce-only SELL orders remain eligible. The hard stop remains at 1% below the lower boundary and can only close existing LONG inventory.
- **Margin guard:** pause/cancel new BUY/DCA orders when free margin divided by PAPER equity is below 15%. Reduce-only exits remain enabled.
- **Gap handling:** if a quote crosses multiple grid levels, record the gap and evaluate crossed limit orders against the current observed OKX BBO. Execution is capped by visible bid/ask size. Partial fills remain partial; no synthetic depth, queue position, or guaranteed market execution is modeled.
- **Order throttling:** at least 200 ms between new order intents for the same grid level. Existing active orders are reused; blocked child intents are retried during reconciliation on a later quote.
- **Funding estimate:** charge a configurable estimated LONG funding rate of 0.01% per 8-hour interval against current marked notional. This is an explicit simulation assumption, **not** a fetched or guaranteed OKX funding rate. Funding is included in fees, net PnL and equity, and its ledger state is persisted.

Live integration is read-only public market data. The PAPER engine may simulate fills using the displayed BBO sizes; it never sends orders or accesses private account channels.
