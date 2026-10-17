# MQTT Security in OT/IIoT — Baseline Environment

Eclipse Mosquitto broker in Docker with authentication and per-user ACL enabled.
No TLS yet (planned as a later step).

## Requirements

- Docker Desktop (macOS, or Windows with WSL2 backend)
- Bash: macOS/Linux terminal, or **Git Bash / WSL** on Windows

Windows: run the scripts from Git Bash or WSL. Do not double-click `.sh` files.
The repo's `.gitattributes` keeps shell scripts on LF line endings; if you cloned
before that file existed, re-clone rather than editing the scripts in place.

## Setup

```bash
./scripts/setup-users.sh          # creates mosquitto/config/passwd (git-ignored)
docker compose up -d              # start the broker on port 1883
```

Share the printed credentials through a private channel. Do not commit them.
To regenerate passwords: delete `mosquitto/config/passwd`, run setup again, then `docker compose restart`.

## Smoke test

```bash
./scripts/smoke-test.sh <sensor-pw> <monitor-pw> <device-pw>
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

- `docker-compose.yml` — broker service
- `mosquitto/config/mosquitto.conf` — broker settings
- `mosquitto/config/acl` — per-user topic rules
- `scripts/` — setup and smoke test
- `.gitattributes` — forces LF on `.sh` files
