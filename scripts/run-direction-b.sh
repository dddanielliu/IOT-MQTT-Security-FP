#!/usr/bin/env bash
# Direction B experiment: a TLS-authenticated client sends malicious control messages.
# Runs twice: GUARD=off (baseline, no app-layer checks), then GUARD=on (guard enabled).
# Results: experiments/summary-guard-{off,on}.txt (git-ignored).
# Needs setup done first: .env, mosquitto/config/certs/ (see README). Only bash and Docker.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env || ! -f mosquitto/config/certs/ca.crt ]]; then
  echo "Run ./scripts/setup-users.sh and ./scripts/gen-certs.sh first."
  exit 1
fi
mkdir -p experiments

for mode in off on; do
  echo "##### GUARD=$mode"
  rm -f experiments/*.jsonl

  GUARD=$mode docker compose up -d --build --force-recreate device controller >/dev/null
  sleep 4   # let benign traffic start and the device subscribe

  docker compose --profile attack run --rm attacker | tail -n 3
  sleep 6   # let the last benign messages arrive

  docker compose stop controller >/dev/null
  docker compose --profile attack run --rm --no-deps --entrypoint python attacker evaluate.py \
    | tee "experiments/summary-guard-$mode.txt"
  echo
done

echo "Done. Summaries: experiments/summary-guard-off.txt and experiments/summary-guard-on.txt"
