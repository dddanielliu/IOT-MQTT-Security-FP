"""Simulated actuator. Subscribes to the control topic and executes commands.

GUARD=on  -> every command passes through guard.Guard before it is executed.
GUARD=off -> baseline: any JSON object with "cmd" and "value" is executed as-is.

Each decision is appended to /out/device_decisions.jsonl for evaluate.py.
"""
import json
import os
import time

from common import TOPIC_CTRL, connect
from guard import Guard

GUARD_ON = os.environ.get("GUARD", "on") == "on"
OUT = "/out/device_decisions.jsonl"

guard = Guard()
state = {}  # simulated actuator state, e.g. {"set_setpoint": 25.0}


def decide(raw):
    if GUARD_ON:
        return guard.check(raw)
    try:
        msg = json.loads(raw)
    except ValueError:
        return False, "malformed_json", None
    if isinstance(msg, dict) and "cmd" in msg and "value" in msg:
        return True, "no_guard", msg
    return False, "not_executable", msg


def on_message(client, userdata, message):
    t0 = time.monotonic()
    raw = message.payload.decode("utf-8", "replace")
    ok, reason, msg = decide(raw)
    if ok:
        state[msg["cmd"]] = msg["value"]
        print("ACTUATE", msg["cmd"], msg["value"], flush=True)
    else:
        print("REJECT", reason, raw[:80], flush=True)

    entry = {
        "t": time.time(),
        "raw": raw[:300],
        "decision": "executed" if ok else "rejected",
        "reason": reason,
        "proc_ms": round((time.monotonic() - t0) * 1000, 3),
        "guard": "on" if GUARD_ON else "off",
    }
    with open(OUT, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    client = connect("device", "device", os.environ["DEVICE_PW"])
    client.on_message = on_message
    client.on_connect = lambda c, u, flags, rc, props: c.subscribe(TOPIC_CTRL, qos=1)
    print(f"device up, GUARD={'on' if GUARD_ON else 'off'}", flush=True)
    client.loop_forever()


if __name__ == "__main__":
    main()
