#!/usr/bin/env bash
# Checks the baseline: normal flow works, unauthorized access is denied.
# Usage: ./scripts/smoke-test.sh <sensor-pw> <monitor-pw> <device-pw>
# Needs only bash and Docker (Git Bash or WSL on Windows).
set -uo pipefail

if [[ $# -ne 3 ]]; then
  echo "usage: $0 <sensor-pw> <monitor-pw> <device-pw>"
  exit 2
fi
SENSOR_PW="$1"; MONITOR_PW="$2"; DEVICE_PW="$3"
IMAGE=eclipse-mosquitto:2
HOST=host.docker.internal
TOPIC=factory/machine1/temperature
CONTROL=factory/machine1/control
pass=0; fail=0

report() {  # report <ok|fail> <description>
  if [[ "$1" == ok ]]; then echo "PASS  $2"; pass=$((pass+1))
  else echo "FAIL  $2"; fail=$((fail+1)); fi
}

# 1. Normal flow: monitor receives the sensor's message.
RECV="$(mktemp)"
docker run --rm "$IMAGE" mosquitto_sub -h "$HOST" -u monitor -P "$MONITOR_PW" \
  -t "$TOPIC" -C 1 -W 8 > "$RECV" 2>/dev/null &
SUB_PID=$!
sleep 2
docker run --rm "$IMAGE" mosquitto_pub -h "$HOST" -u sensor -P "$SENSOR_PW" \
  -t "$TOPIC" -m '{"value":25.0}' >/dev/null 2>&1
wait "$SUB_PID"
if grep -q '"value":25.0' "$RECV"; then report ok "monitor receives sensor message"
else report fail "monitor receives sensor message"; fi
rm -f "$RECV"

# 2. Anonymous connection must be rejected (non-zero exit).
if docker run --rm "$IMAGE" mosquitto_pub -h "$HOST" -t "$TOPIC" -m 'x' >/dev/null 2>&1; then
  report fail "anonymous connection rejected"
else
  report ok "anonymous connection rejected"
fi

# 3. Sensor publishes to control topic; device must NOT receive it (ACL).
#    The broker drops denied publishes silently, so check delivery, not exit code.
RECV="$(mktemp)"
docker run --rm "$IMAGE" mosquitto_sub -h "$HOST" -u device -P "$DEVICE_PW" \
  -t "$CONTROL" -C 1 -W 8 > "$RECV" 2>/dev/null &
SUB_PID=$!
sleep 2
docker run --rm "$IMAGE" mosquitto_pub -h "$HOST" -u sensor -P "$SENSOR_PW" \
  -t "$CONTROL" -m 'forged-command' >/dev/null 2>&1
wait "$SUB_PID"
if [[ -s "$RECV" ]]; then report fail "sensor's forged publish to control topic is blocked"
else report ok "sensor's forged publish to control topic is blocked"; fi
rm -f "$RECV"

echo
echo "passed=$pass failed=$fail"
[[ $fail -eq 0 ]]
