#!/usr/bin/env bash
# Creates a private CA and a broker server certificate for TLS (port 8883).
# Output: mosquitto/config/certs/{ca.crt,ca.key,server.crt,server.key}
# ca.key and server.key are secrets: the certs/ folder is git-ignored.
# Needs openssl on the host (macOS, Linux, or Git Bash on Windows).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CERT_DIR="$ROOT/mosquitto/config/certs"

if [[ -e "$CERT_DIR/ca.crt" ]]; then
  echo "certificates already exist under $CERT_DIR"
  echo "Delete that folder first if you want to regenerate them."
  exit 1
fi

mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

# 1. Private CA (10 years).
openssl req -x509 -newkey rsa:2048 -nodes -days 3650 \
  -keyout ca.key -out ca.crt -subj "/CN=IIoT-Lab-CA" >/dev/null 2>&1

# 2. Broker server key + CSR.
openssl req -newkey rsa:2048 -nodes \
  -keyout server.key -out server.csr -subj "/CN=mosquitto" >/dev/null 2>&1

# 3. Sign with the CA. SANs cover the compose service name and host-side names.
cat > server.ext <<'EOF'
subjectAltName = DNS:mosquitto, DNS:localhost, DNS:host.docker.internal
extendedKeyUsage = serverAuth
EOF
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -days 825 -extfile server.ext -out server.crt >/dev/null 2>&1

rm -f server.csr server.ext ca.srl
chmod 600 ca.key server.key

echo "Written to $CERT_DIR:"
echo "  ca.crt, server.crt (public)"
echo "  ca.key, server.key (secret, git-ignored)"
echo "Restart the stack so the broker loads them: docker compose up -d"
