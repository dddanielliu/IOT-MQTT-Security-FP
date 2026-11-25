"""Benign controller. Logs in as `controller`, reads temperature, publishes control commands.

Simplified logic: fan speed follows the last temperature reading; setpoint stays near 25 C
with small jitter. Every message is recorded in /out/controller_truth.jsonl as benign,
for evaluate.py only. The guard never sees these labels.
"""
import json
import os
import random
import time
import uuid

from common import TOPIC_CTRL, TOPIC_TEMP, connect

OUT = "/out/controller_truth.jsonl"
INTERVAL_S = 5.0

last_temp = 25.0
seq = 0


def on_temp(client, userdata, message):
    global last_temp
    try:
        last_temp = float(json.loads(message.payload)["value"])
    except (ValueError, KeyError, TypeError):
        pass


def publish(client, cmd, value):
    global seq
    seq += 1
    msg_id = f"benign-{uuid.uuid4().hex[:12]}"
    payload = json.dumps({"id": msg_id, "cmd": cmd, "value": value, "seq": seq, "ts": int(time.time())})
    client.publish(TOPIC_CTRL, payload, qos=1)
    with open(OUT, "a") as f:
        f.write(json.dumps({"id": msg_id, "label": "benign", "scenario": "normal", "raw": payload}) + "\n")


def main():
    client = connect("controller", "controller", os.environ["CONTROLLER_PW"])
    client.on_connect = lambda c, u, flags, rc, props: c.subscribe(TOPIC_TEMP, qos=0)
    client.message_callback_add(TOPIC_TEMP, on_temp)
    client.loop_start()
    print("controller up", flush=True)

    while True:
        publish(client, "set_setpoint", round(25.0 + random.uniform(-0.5, 0.5), 2))
        fan = max(0, min(100, round((last_temp - 22.0) * 20)))
        publish(client, "set_fan_pct", fan)
        time.sleep(INTERVAL_S)


if __name__ == "__main__":
    main()
