# MQTT Security in OT/IIoT — Baseline Environment

Eclipse Mosquitto broker in Docker with authentication and per-user ACL enabled,
plus a simulated sensor and a monitor. No TLS yet (planned as a later step).

## Requirements

- Docker Desktop (macOS, or Windows with WSL2 backend)
- Bash: macOS/Linux terminal, or **Git Bash / WSL** on Windows

Windows: run the scripts from Git Bash or WSL. Do not double-click `.sh` files.
The repo's `.gitattributes` keeps shell scripts on LF line endings; if you cloned
before that file existed, re-clone rather than editing the scripts in place.

## Setup

```bash
./scripts/setup-users.sh          # creates mosquitto/config/passwd and .env (both git-ignored)
docker compose up -d              # starts broker, sensor, monitor
docker compose logs -f monitor    # watch sensor readings arrive
```

Share the printed credentials through a private channel. Do not commit them.
To regenerate passwords: `docker compose down`, delete `mosquitto/config/passwd` and `.env`,
run setup again, then `docker compose up -d`.

## Services

| Service | Role |
|---|---|
| mosquitto | Broker on port 1883 (auth + ACL) |
| sensor | Publishes `{"value","seq","ts"}` to `factory/machine1/temperature` every second (`scripts/sensor-sim.sh`) |
| monitor | Subscribes to the temperature topic and prints what it receives |

Controller and device are not in compose yet.

## Smoke test

```bash
set -a && . ./.env && set +a
./scripts/smoke-test.sh "$SENSOR_PW" "$MONITOR_PW" "$DEVICE_PW"
```

Checks:
1. Sensor's publish reaches the monitor.
2. Anonymous connections are rejected.
3. Sensor's publish to the control topic does **not** reach the device (ACL).

Note: the broker drops denied publishes silently, so check 3 looks at whether a
subscriber receives the message, not at the publisher's exit code.

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
- `mosquitto/config/mosquitto.conf` — broker settings
- `mosquitto/config/acl` — per-user topic rules
- `scripts/` — setup, smoke test, sensor simulator
- `.gitattributes` — forces LF on `.sh` files
