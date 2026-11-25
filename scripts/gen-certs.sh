#!/usr/bin/env bash
# Creates a private CA and a broker server certificate for TLS (port 8883).
# Output: mosquitto/config/certs/{ca.crt,ca.key,server.crt,server.key}
# ca.key and server.key are secrets: the certs/ folder is git-ignored.
# Runs openssl inside a container, so only bash and Docker are needed (Git Bash or WSL on Windows).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CERT_DIR="$ROOT/mosquitto/config/certs"
IMAGE=alpine:3.20

if [[ -e "$CERT_DIR/ca.crt" ]]; then
  echo "certificates already exist under $CERT_DIR"
  echo "Delete that folder first if you want to regenerate them."
  exit 1
fi

mkdir -p "$CERT_DIR"

docker run --rm -v "$CERT_DIR:/certs" -w /certs \
  -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" "$IMAGE" sh -c '
  set -eu
  apk add --no-cache -q openssl >/dev/null

  # 1. Private CA (10 years).
  openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
    -keyout ca.key -out ca.crt -subj "/CN=IIoT-Lab-CA" >/dev/null 2>&1

  # 2. Broker server key + CSR.
  openssl req -newkey rsa:2048 -nodes \
    -keyout server.key -out server.csr -subj "/CN=mosquitto" >/dev/null 2>&1

  # 3. Sign with the CA. SANs cover the compose service name and host-side names.
  printf "%s\n" "subjectAltName = DNS:mosquitto, DNS:localhost, DNS:host.docker.internal" \
    "extendedKeyUsage = serverAuth" > server.ext
  openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
    -days 825 -extfile server.ext -out server.crt >/dev/null 2>&1

  rm -f server.csr server.ext ca.srl
  chmod 600 ca.key server.key
  # Hand the files back to the host user (the container ran as root).
  chown "$HOST_UID:$HOST_GID" ./*
'

echo "Written to $CERT_DIR:"
echo "  ca.crt, server.crt (public)"
echo "  ca.key, server.key (secret, git-ignored)"
echo "Restart the stack so the broker loads them: docker compose up -d"
