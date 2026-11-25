# MQTT Security in OT/IIoT — Baseline Environment

Eclipse Mosquitto broker in Docker with authentication and per-user ACL enabled,
plus a simulated sensor and a monitor. Two listeners: plaintext 1883 (kept for
before/after comparison) and TLS 8883 (used by sensor and monitor).

## Requirements

- Docker Desktop (macOS, or Windows with WSL2 backend)
- Bash: macOS/Linux terminal, or **Git Bash / WSL** on Windows

Nothing else is needed: certificates and passwords are generated inside containers.

Windows: run the scripts from Git Bash or WSL. Do not double-click `.sh` files.
The repo's `.gitattributes` keeps shell scripts on LF line endings; if you cloned
before that file existed, re-clone rather than editing the scripts in place.

## Setup

Run these in order. The first two each create files the stack needs, and they
refuse to overwrite existing ones.

```bash
./scripts/setup-users.sh          # creates mosquitto/config/passwd and .env (git-ignored)
./scripts/gen-certs.sh            # creates mosquitto/config/certs/ (CA + broker cert, git-ignored)
docker compose up -d              # starts broker, sensor, monitor
docker compose logs -f monitor    # watch sensor readings arrive over TLS
```

**Order matters.** If `certs/ca.crt` is missing when compose starts, Docker creates
an empty directory in its place and the broker will not start with TLS. If that
happens, run `docker compose down`, delete `mosquitto/config/certs`, run
`./scripts/gen-certs.sh`, then `docker compose up -d`.

Share the printed credentials through a private channel. Do not commit them.
The private keys in `mosquitto/config/certs/` are also secrets.

To regenerate everything: `docker compose down`, delete `mosquitto/config/passwd`,
`.env` and `mosquitto/config/certs`, run the setup steps again, then `docker compose up -d`.

## Services

| Service | Role |
|---|---|
| mosquitto | Broker: 1883 plaintext and 8883 TLS, both with auth + ACL |
| sensor | Publishes `{"value","seq","ts"}` to `factory/machine1/temperature` every second over 8883 (`scripts/sensor-sim.sh`) |
| monitor | Subscribes to the temperature topic over 8883 and prints what it receives |

Controller and device are not in compose yet.

## TLS

- `scripts/gen-certs.sh` creates a private CA (`ca.crt`, `ca.key`) and a broker
  certificate (`server.crt`, `server.key`), valid for `mosquitto`, `localhost`,
  and `host.docker.internal`.
- The broker serves TLS 1.2 and above on 8883. Clients must trust `ca.crt`.
- Port 1883 is still plaintext. It is kept only to compare traffic before and after TLS.

## Smoke test

```bash
set -a && . ./.env && set +a
./scripts/smoke-test.sh "$SENSOR_PW" "$MONITOR_PW" "$DEVICE_PW"
```

Checks:
1. Sensor's publish reaches the monitor (1883).
2. Anonymous connections are rejected (1883).
3. Sensor's publish to the control topic does **not** reach the device (ACL).
4. Sensor's publish reaches the monitor over TLS (8883, trusting the lab CA).
5. A client that does not trust the lab CA fails the TLS handshake.

Note: the broker drops denied publishes silently, so check 3 looks at whether a
subscriber receives the message, not at the publisher's exit code. Checks 1 and 4
use a unique `test_id` in the payload, so they cannot match a regular sensor reading.

Checks 4 and 5 need `mosquitto/config/certs/ca.crt`. Without it the script reports a failure.

## Users and topics

| User | Topic | Permission |
|---|---|---|
| sensor | factory/machine1/temperature | publish |
| monitor | factory/machine1/temperature | subscribe |
| controller | factory/machine1/temperature | subscribe |
| controller | factory/machine1/control | publish |
| device | factory/machine1/control | subscribe |

## Layout

- `docker-compose.yml` — broker, sensor, monitor services
- `mosquitto/config/mosquitto.conf` — broker settings (1883 plaintext, 8883 TLS)
- `mosquitto/config/acl` — per-user topic rules
- `mosquitto/config/certs/` — generated CA and broker certificate (git-ignored)
- `scripts/` — setup, certificate generation, smoke test, sensor simulator
- `.gitattributes` — forces LF on `.sh` files
