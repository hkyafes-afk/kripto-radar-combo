#!/usr/bin/env python3
"""PAPER izleyici: state.json'u okur, sorun/dolum olunca Telegram'a yazar. Yalnız standart kütüphane."""
import json, os, sys, time, urllib.parse, urllib.request
from pathlib import Path

STATE = Path(os.environ.get("COMBO_STATE", str(Path.home() / "services/combo-paper/state.json")))
MEM = Path(os.environ.get("COMBO_WATCH_MEM", str(Path.home() / ".cache/combo-watch.json")))
TOKEN, CHAT = os.environ.get("TELEGRAM_TOKEN", ""), os.environ.get("TELEGRAM_CHAT_ID", "")
STALE_S = 120


def send(text):
    if not TOKEN or not CHAT:
        print("TELEGRAM_TOKEN/CHAT_ID yok:", text)
        return
    data = urllib.parse.urlencode({"chat_id": CHAT, "text": text}).encode()
    urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data), timeout=10).read()


def main():
    mem = {}
    try:
        mem = json.loads(MEM.read_text())
    except Exception:
        pass
    problems = []
    try:
        s = json.loads(STATE.read_text())
        age = time.time() - s["generated_at_ms"] / 1000
        p = s["paper"]
        if age > STALE_S:
            problems.append(f"state {int(age)} sn'dir güncellenmiyor (motor/yayın durmuş olabilir)")
        if not (s.get("feed", {}).get("feed", {}) or {}).get("healthy", True):
            problems.append("OKX fiyat akışı kesik")
        if p.get("halted"):
            problems.append(f"motor durdu: {p.get('halt_reason')}")
        fills = s.get("fills", [])
        last = fills[-1]["ts_ms"] if fills else 0
        if mem.get("last_fill") and last > mem["last_fill"]:
            for f in [x for x in fills if x["ts_ms"] > mem["last_fill"]][-5:]:
                send(f"{'ALIŞ' if f['side']=='buy' else 'SATIŞ'} {f['qty']} BTC @ {f['price']:.1f} · öz sermaye {p.get('equity_usdt', 0):.2f} USDT")
        mem["last_fill"] = last
    except Exception as e:  # state okunamıyor
        problems.append(f"state okunamadı: {type(e).__name__}")
    key = "|".join(problems)
    if key != mem.get("problem"):
        if problems:
            send("⚠️ COMBO PAPER sorun: " + "; ".join(problems))
        elif mem.get("problem"):
            send("✅ COMBO PAPER normale döndü")
        mem["problem"] = key
    MEM.parent.mkdir(parents=True, exist_ok=True)
    MEM.write_text(json.dumps(mem))


if __name__ == "__main__":
    sys.exit(main())
