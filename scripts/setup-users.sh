#!/usr/bin/env bash
# Creates mosquitto/config/passwd with a random password per user.
# The password file is git-ignored. Share credentials through a private channel only.
# Needs only bash and Docker (Git Bash or WSL on Windows).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PASSWD_FILE="$ROOT/mosquitto/config/passwd"
USERS=(sensor monitor controller device)
IMAGE=eclipse-mosquitto:2

if [[ -e "$PASSWD_FILE" ]]; then
  echo "passwd already exists: $PASSWD_FILE"
  echo "Delete it first if you want to regenerate passwords."
  exit 1
fi

# Random 20-char alphanumeric password, generated inside the broker image (no openssl needed).
random_pw() {
  docker run --rm --entrypoint sh "$IMAGE" -c \
    'head -c 64 /dev/urandom | tr -dc A-Za-z0-9 | head -c 20'
}

: > "$PASSWD_FILE"
for user in "${USERS[@]}"; do
  pw="$(random_pw)"
  docker run --rm -v "$ROOT/mosquitto/config:/mosquitto/config" "$IMAGE" \
    mosquitto_passwd -b /mosquitto/config/passwd "$user" "$pw" >/dev/null
  echo "$user : $pw"
done

echo
echo "Written to $PASSWD_FILE. Restart the broker to apply: docker compose restart"
