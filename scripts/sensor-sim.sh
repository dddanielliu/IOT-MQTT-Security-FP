#!/bin/sh
# Simulated temperature sensor. Publishes {"value","seq","ts"} once per second.
# Values wander around 25 °C with small noise, clamped to 20–30 °C.
# Runs inside the eclipse-mosquitto image (mosquitto_pub, awk, date).
# Env: BROKER, SENSOR_USER, SENSOR_PW
set -eu

TOPIC=factory/machine1/temperature
seq=0
value=25.00

while true; do
  seq=$((seq + 1))
  value=$(awk -v v="$value" -v s="$seq" 'BEGIN {
    srand(s)
    n = v + (rand() - 0.5) * 0.4
    if (n < 20) n = 20
    if (n > 30) n = 30
    printf "%.2f", n
  }')
  ts=$(date +%s)
  mosquitto_pub -h "$BROKER" -u "$SENSOR_USER" -P "$SENSOR_PW" \
    -t "$TOPIC" -m "{\"value\":$value,\"seq\":$seq,\"ts\":$ts}" \
    || echo "publish failed (seq=$seq)" >&2
  sleep 1
done
