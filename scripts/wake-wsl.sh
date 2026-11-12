#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]] || ! grep -Eq '^TELEGRAM_BOT_TOKEN=.+' .env || ! grep -Eq '^PONTO_CPF=.+' .env || ! grep -Eq '^PONTO_SENHA=.+' .env; then
  echo "ponto-away: preencha o .env (veja .env.example) e rode: docker compose up -d --force-recreate"
  exit 0
fi

for _ in $(seq 1 60); do
  if docker info >/dev/null 2>&1; then
    docker compose up -d --remove-orphans
    exit 0
  fi
  sleep 2
done

echo "ponto-away: o Docker não ficou pronto a tempo" >&2
exit 1
