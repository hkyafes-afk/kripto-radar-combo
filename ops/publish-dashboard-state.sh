#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PUBLISH_DIR="${HOME}/services/combo-paper-publisher"
CACHE_DIR="${HOME}/.cache"
LOCK_FILE="${CACHE_DIR}/combo-paper-dashboard-publisher.lock"
SSH_REMOTE="git@github-combo-paper:hkyafes-afk/kripto-radar-combo.git"
BRANCH="paper-live-state"

mkdir -p "$CACHE_DIR"
exec 9>"$LOCK_FILE"
flock -n 9 || exit 0

if ! systemctl --user is-active --quiet combo-paper.service; then
  echo "PAPER motoru aktif değil; yayın atlandı."
  exit 0
fi

# Fail closed: publish only a fresh, healthy, real OKX-backed snapshot and
# a matching, fully verified append-only PAPER ledger/checkpoint.
python - "$ROOT" <<'PY'
import json
import sys
import time
from pathlib import Path

root = Path(sys.argv[1])
state = json.loads((root / "state.json").read_text(encoding="utf-8"))
now_ms = int(time.time() * 1000)
generated = int(state.get("generated_at_ms") or 0)
quote_ts = state.get("market", {}).get("exchange_ts_ms")
feed = state.get("feed", {}).get("feed", {})
if state.get("schema_version") != 1 or state.get("execution_mode") != "PAPER_ONLY":
    raise SystemExit("Dashboard state schema/mode doğrulanamadı.")
if state.get("symbol") != "BTC-USDT-SWAP":
    raise SystemExit("Dashboard symbol uyuşmazlığı.")
if state.get("private_api_enabled") is not False or state.get("live_order_submission") is not False:
    raise SystemExit("Güvenlik bayrakları PAPER-only değil.")
if not str(state.get("provenance", "")).startswith("COMBO PAPER adapter + accepted public OKX ticker"):
    raise SystemExit("Gerçek veri provenance alanı doğrulanamadı.")
if not feed.get("healthy"):
    raise SystemExit("OKX public feed sağlıklı değil; eski/boş veri yayınlanmadı.")
if quote_ts is None or not -5000 <= now_ms - int(quote_ts) <= 120000:
    raise SystemExit("Son OKX ticker 120 saniyeden eski; snapshot yayınlanmadı.")
if not 0 <= now_ms - generated <= 120000:
    raise SystemExit("Dashboard snapshot zamanı eski veya geçersiz.")

from persistence.ledger import EventLedger
from persistence.recovery import RecoveryManager

runtime = root / "runtime"
ledger = EventLedger(runtime / "events.jsonl")
recovered = RecoveryManager(ledger).recover(runtime / "combo_paper.json")
if recovered is None or ledger.last_seq < 1:
    raise SystemExit("PAPER ledger/checkpoint bulunamadı.")
print(f"Doğrulama OK: seq={ledger.last_seq}, quote_age_ms={now_ms-int(quote_ts)}")
PY

if ! git -C "$ROOT" worktree list --porcelain | grep -Fqx "worktree $PUBLISH_DIR"; then
  if [ -e "$PUBLISH_DIR" ]; then
    echo "Yayın worktree yolu mevcut fakat Git worktree değil: $PUBLISH_DIR" >&2
    exit 1
  fi
  git -C "$ROOT" fetch origin main
  git -C "$ROOT" worktree add --detach "$PUBLISH_DIR" origin/main
fi

git -C "$PUBLISH_DIR" -c remote.origin.url="$SSH_REMOTE" fetch origin \
  "+refs/heads/$BRANCH:refs/remotes/origin/$BRANCH"
git -C "$PUBLISH_DIR" checkout -B "$BRANCH" "origin/$BRANCH"

mkdir -p "$PUBLISH_DIR/runtime"
cp "$ROOT/state.json" "$PUBLISH_DIR/state.json"
cp "$ROOT/runtime/combo_paper.json" "$PUBLISH_DIR/runtime/combo_paper.json"
cp "$ROOT/runtime/events.jsonl" "$PUBLISH_DIR/runtime/events.jsonl"

git -C "$PUBLISH_DIR" add -- state.json runtime/combo_paper.json runtime/events.jsonl
if git -C "$PUBLISH_DIR" diff --cached --quiet; then
  echo "Yayınlanacak yeni PAPER state yok."
  exit 0
fi

LAST_SUBJECT="$(git -C "$PUBLISH_DIR" log -1 --format=%s)"
if [ "$LAST_SUBJECT" = "chore(paper): publish latest verified VM state" ]; then
  git -C "$PUBLISH_DIR" -c user.name="COMBO PAPER VM" \
    -c user.email="combo-paper-vm@users.noreply.github.com" commit --amend --no-edit
else
  git -C "$PUBLISH_DIR" -c user.name="COMBO PAPER VM" \
    -c user.email="combo-paper-vm@users.noreply.github.com" \
    commit -m "chore(paper): publish latest verified VM state"
fi

EXPECTED="$(git -C "$PUBLISH_DIR" rev-parse "refs/remotes/origin/$BRANCH")"
git -C "$PUBLISH_DIR" -c remote.origin.url="$SSH_REMOTE" push \
  "--force-with-lease=refs/heads/$BRANCH:$EXPECTED" origin "HEAD:refs/heads/$BRANCH"

echo "PAPER snapshot ve doğrulanmış ledger $BRANCH dalına yayınlandı."
