#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_DIR="${HOME}/.config/systemd/user"
mkdir -p "$UNIT_DIR"
install -m 0644 "$ROOT/ops/systemd/combo-paper.service" "$UNIT_DIR/combo-paper.service"
install -m 0644 "$ROOT/ops/systemd/combo-dashboard-publish.service" "$UNIT_DIR/combo-dashboard-publish.service"
install -m 0644 "$ROOT/ops/systemd/combo-dashboard-publish.timer" "$UNIT_DIR/combo-dashboard-publish.timer"
for u in combo-watchdog.service combo-watchdog.timer combo-backup.service combo-backup.timer; do install -m 0644 "$ROOT/ops/systemd/$u" "$UNIT_DIR/$u"; done
systemctl --user daemon-reload
echo "Kullanıcı servis dosyaları kuruldu; hiçbir servis başlatılmadı veya etkinleştirilmedi."
