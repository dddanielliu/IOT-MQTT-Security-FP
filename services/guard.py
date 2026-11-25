"""Application-layer checks for control commands, run on the device before actuating.

TLS only proves the sender holds valid credentials and that the bytes were not changed
in transit. It says nothing about whether the command is safe. These checks do that.

Control message format (JSON object):
    {"id": "...", "cmd": "set_setpoint", "value": 25.0, "seq": 12, "ts": 1700000000}

Rules are deliberately simple and documented in docs/PLAN.md / README (direction B).
"""
import json
import math
import time
from collections import defaultdict, deque

# Allowed commands and their physical limits. Anything not listed is rejected.
RULES = {
    "set_setpoint": {"kind": "float", "min": 15.0, "max": 35.0},  # degrees C
    "set_fan_pct": {"kind": "int", "min": 0, "max": 100},         # percent
}

# Per-command rate limit: at most RATE_MAX accepted commands in any RATE_WINDOW_S seconds.
RATE_WINDOW_S = 10.0
RATE_MAX = 5


class Guard:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.accepted_times = defaultdict(deque)

    def check(self, raw):
        """Return (accepted, reason, msg). `msg` is the parsed dict when parsing succeeded."""
        try:
            msg = json.loads(raw)
        except ValueError:
            return False, "malformed_json", None
        if not isinstance(msg, dict):
            return False, "not_an_object", None

        cmd, value = msg.get("cmd"), msg.get("value")
        if not isinstance(cmd, str) or "id" not in msg or "value" not in msg:
            return False, "missing_fields", msg

        rule = RULES.get(cmd)
        if rule is None:
            return False, "unknown_cmd", msg

        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return False, "wrong_type", msg
        if isinstance(value, float) and not math.isfinite(value):
            return False, "wrong_type", msg
        if rule["kind"] == "int" and float(value) != int(value):
            return False, "wrong_type", msg
        if not rule["min"] <= value <= rule["max"]:
            return False, "out_of_range", msg

        now = self.clock()
        times = self.accepted_times[cmd]
        while times and now - times[0] > RATE_WINDOW_S:
            times.popleft()
        if len(times) >= RATE_MAX:
            return False, "rate_limited", msg
        times.append(now)

        return True, "ok", msg
