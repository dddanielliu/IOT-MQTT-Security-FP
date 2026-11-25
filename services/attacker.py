"""Attacker for direction B: a legitimate, TLS-authenticated client sends bad control messages.

Model: the controller's credentials are stolen. The attacker connects over TLS exactly like the
real controller (valid cert chain, valid password, allowed topic), so the transport and ACL
both pass. Only the message content is malicious.

Ground truth goes to /out/attack_truth.jsonl. The device never reads it.
"""
import json
import os
import time
import uuid

from common import TOPIC_CTRL, connect

OUT = "/out/attack_truth.jsonl"


def valid_json(scenario, cmd, value, seq):
    msg_id = f"atk-{scenario}-{uuid.uuid4().hex[:8]}"
    return msg_id, json.dumps({"id": msg_id, "cmd": cmd, "value": value, "seq": seq, "ts": int(time.time())})


def scenarios():
    """Yields (scenario, id, payload, pause_after_s)."""
    seq = 0

    # 1. Values outside the physical range.
    for cmd, value in [("set_setpoint", 90.0), ("set_setpoint", -40.0),
                       ("set_fan_pct", 150), ("set_fan_pct", -20)]:
        seq += 1
        yield ("out_of_range", *valid_json("out_of_range", cmd, value, seq), 1.0)

    # 2. Commands the device does not support.
    for cmd in ["emergency_stop", "heater_override", "valve_open"]:
        seq += 1
        yield ("unknown_cmd", *valid_json("unknown_cmd", cmd, 1, seq), 1.0)

    # 3. Malformed content: broken JSON, wrong type, missing field. The id is embedded so
    #    evaluate.py can still match the decision to this message.
    atk_id = f"atk-malformed-{uuid.uuid4().hex[:8]}"
    yield ("malformed", atk_id, '{"id":"%s","cmd":"set_setpoint","value":' % atk_id, 1.0)
    seq += 1
    atk_id = f"atk-malformed-{uuid.uuid4().hex[:8]}"
    yield ("malformed", atk_id,
           json.dumps({"id": atk_id, "cmd": "set_setpoint", "value": "30", "seq": seq, "ts": int(time.time())}), 1.0)
    atk_id = f"atk-malformed-{uuid.uuid4().hex[:8]}"
    yield ("malformed", atk_id, json.dumps({"id": atk_id, "cmd": "set_setpoint"}), 1.0)

    # 4. Flood: many in-range commands in a short burst. The rate limit should stop most of them.
    for _ in range(30):
        seq += 1
        yield ("flood", *valid_json("flood", "set_fan_pct", 50, seq), 0.02)
    time.sleep(1.0)

    # 5. Residual risk: in range and plausible, so the guard should let it through.
    #    Included on purpose; it documents what range checks cannot catch.
    for _ in range(2):
        seq += 1
        yield ("in_range_residual", *valid_json("in_range_residual", "set_setpoint", 34.0, seq), 6.0)


def main():
    client = connect("attacker", "controller", os.environ["CONTROLLER_PW"])
    client.loop_start()
    print("attacker: sending scenarios as controller (TLS, valid credentials)", flush=True)

    for scenario, msg_id, payload, pause in scenarios():
        client.publish(TOPIC_CTRL, payload, qos=1)
        with open(OUT, "a") as f:
            f.write(json.dumps({"id": msg_id, "label": "malicious", "scenario": scenario, "raw": payload}) + "\n")
        print(f"sent {scenario:18s} {msg_id}", flush=True)
        time.sleep(pause)

    time.sleep(1.0)  # let the last messages reach the device before exiting
    client.loop_stop()
    client.disconnect()


if __name__ == "__main__":
    main()
