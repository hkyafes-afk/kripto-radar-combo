#!/usr/bin/env bash
# Sunucuda bir kez çalıştır. GCP firewall'da tcp:80 ve tcp:443 açık olmalı.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
if ! command -v caddy >/dev/null; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq debian-keyring debian-archive-keyring apt-transport-https curl gnupg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
  sudo apt-get update -qq && sudo apt-get install -y -qq caddy
  sudo systemctl disable --now caddy
fi
sudo setcap cap_net_bind_service=+ep "$(command -v caddy)"
install -m 0644 "$ROOT/ops/systemd/combo-state-serve.service" "$HOME/.config/systemd/user/combo-state-serve.service"
install -m 0644 "$ROOT/ops/systemd/combo-paper.service" "$HOME/.config/systemd/user/combo-paper.service"
systemctl --user daemon-reload
systemctl --user enable --now combo-state-serve.service
systemctl --user restart combo-paper.service
sleep 5
curl -sS -o /dev/null -w "HTTPS state.json: %{http_code}\n" https://35-209-41-139.sslip.io/state.json
