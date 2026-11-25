"""Match ground truth to the device's decisions and print ASR, FPR and per-scenario results.

Run inside the app container (no host Python needed):
    docker compose --profile attack run --rm --no-deps --entrypoint python attacker evaluate.py
"""
import json
import os
from collections import Counter, defaultdict

OUT = "/out"


def load(name):
    path = os.path.join(OUT, name)
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    truth = load("controller_truth.jsonl") + load("attack_truth.jsonl")
    decisions = load("device_decisions.jsonl")

    # Each message id is unique, so a substring match on the raw payload is enough.
    # Malformed JSON cannot be parsed, so matching on raw text is what works for every case.
    def decision_for(msg_id):
        for d in decisions:
            if msg_id in d["raw"]:
                return d
        return None

    per = defaultdict(lambda: Counter())
    reasons = Counter()
    for t in truth:
        d = decision_for(t["id"])
        if d is None:
            outcome = "no_decision"
        else:
            outcome = d["decision"]
            reasons[(t["label"], d["reason"])] += 1
        per[(t["label"], t["scenario"])][outcome] += 1

    guard = next((d["guard"] for d in decisions), "?")
    print(f"=== device guard: {guard} ===")
    print(f"{'label':10s} {'scenario':20s} {'total':>5s} {'executed':>9s} {'rejected':>9s} {'missing':>8s}")
    for (label, scenario), c in sorted(per.items()):
        total = sum(c.values())
        print(f"{label:10s} {scenario:20s} {total:5d} {c['executed']:9d} {c['rejected']:9d} "
              f"{c['no_decision']:8d}")

    mal = [k for k in per if k[0] == "malicious"]
    ben = [k for k in per if k[0] == "benign"]
    mal_total = sum(sum(per[k].values()) for k in mal)
    mal_exec = sum(per[k]["executed"] for k in mal)
    ben_total = sum(sum(per[k].values()) for k in ben)
    ben_rej = sum(per[k]["rejected"] for k in ben)

    print()
    if mal_total:
        print(f"ASR (malicious executed / malicious total): {mal_exec}/{mal_total} = {mal_exec / mal_total:.1%}")
    if ben_total:
        print(f"FPR (benign rejected / benign total):       {ben_rej}/{ben_total} = {ben_rej / ben_total:.1%}")
    print()
    print("Reasons (label, device reason) -> count:")
    for (label, reason), n in sorted(reasons.items()):
        print(f"  {label:10s} {reason:16s} {n}")


if __name__ == "__main__":
    main()
