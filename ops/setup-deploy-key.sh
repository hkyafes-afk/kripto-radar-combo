#!/usr/bin/env bash
set -euo pipefail

KEY="$HOME/.ssh/combo_paper_deploy"
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
if [ -e "$KEY" ] || [ -e "$KEY.pub" ]; then
  echo "Deploy key zaten mevcut; üzerine yazılmadı: $KEY" >&2
  exit 1
fi
ssh-keygen -t ed25519 -f "$KEY" -C "combo-paper-live-state" -N ""
touch "$HOME/.ssh/config"
if ! grep -q '^Host github-combo-paper$' "$HOME/.ssh/config"; then
  printf '\nHost github-combo-paper\n  HostName github.com\n  User git\n  IdentityFile %s\n  IdentitiesOnly yes\n  StrictHostKeyChecking accept-new\n' "$KEY" >> "$HOME/.ssh/config"
fi
chmod 600 "$HOME/.ssh/config" "$KEY"
echo "Aşağıdaki PUBLIC key'i GitHub repo Settings > Deploy keys > Add deploy key alanına ekle."
echo "Write access kutusunu işaretle. PRIVATE key dosyasını kimseyle paylaşma."
cat "$KEY.pub"
