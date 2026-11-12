#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
chmod +x "$ROOT/scripts/wake-wsl.sh"

install -m 644 "$ROOT/scripts/ponto-away.service" /etc/systemd/system/ponto-away.service
systemctl daemon-reload
systemctl enable ponto-away.service
systemctl enable docker.service

WSLCONFIG="/mnt/c/Users/Julio/.wslconfig"
if [[ ! -f "$WSLCONFIG" ]]; then
  printf '%s\n' '[wsl2]' 'vmIdleTimeout=-1' > "$WSLCONFIG"
  echo "Criei $WSLCONFIG com vmIdleTimeout=-1"
elif ! grep -Eq '^[[:space:]]*vmIdleTimeout=' "$WSLCONFIG"; then
  printf '\n%s\n' 'vmIdleTimeout=-1' >> "$WSLCONFIG"
  echo "Adicionei vmIdleTimeout=-1 em $WSLCONFIG"
else
  echo "vmIdleTimeout já está em $WSLCONFIG"
fi

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(wslpath -w "$ROOT/scripts/install-windows-task.ps1")"

echo "Autostart instalado. O container sobe quando o Windows entrar na sua conta."
