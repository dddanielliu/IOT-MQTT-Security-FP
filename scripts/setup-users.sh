#!/usr/bin/env bash
# Creates mosquitto/config/passwd and .env with a random password per user.
# Both files are git-ignored. Share credentials through a private channel only.
# Needs only bash and Docker (Git Bash or WSL on Windows).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PASSWD_FILE="$ROOT/mosquitto/config/passwd"
ENV_FILE="$ROOT/.env"
USERS=(sensor monitor controller device)
IMAGE=eclipse-mosquitto:2

if [[ -e "$PASSWD_FILE" || -e "$ENV_FILE" ]]; then
  echo "passwd or .env already exists under $ROOT"
  echo "Delete both first if you want to regenerate passwords."
  exit 1
fi

# Random 20-char alphanumeric password, generated inside the broker image (no openssl needed).
random_pw() {
  docker run --rm --entrypoint sh "$IMAGE" -c \
    'head -c 64 /dev/urandom | tr -dc A-Za-z0-9 | head -c 20'
}

: > "$PASSWD_FILE"
: > "$ENV_FILE"
for user in "${USERS[@]}"; do
  pw="$(random_pw)"
  docker run --rm -v "$ROOT/mosquitto/config:/mosquitto/config" "$IMAGE" \
    mosquitto_passwd -b /mosquitto/config/passwd "$user" "$pw" >/dev/null
  echo "$(echo "$user" | tr '[:lower:]' '[:upper:]')_PW=$pw" >> "$ENV_FILE"
  echo "$user : $pw"
done

chmod 600 "$PASSWD_FILE" "$ENV_FILE" 2>/dev/null || true
echo
echo "Written: $PASSWD_FILE and $ENV_FILE"
echo "Start or restart the stack: docker compose up -d"
