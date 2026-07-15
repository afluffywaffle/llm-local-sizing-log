#!/usr/bin/env python3
"""Aggregate a local-LLM sizing log; --calibrate derives your estimator's bias.

Usage:
    python analyze.py your_log.jsonl              # per-domain distributions
    python analyze.py your_log.jsonl --calibrate  # verified-vs-estimate direction

Neutral: no assumptions about which orchestrating model wrote the log. Whatever
bias --calibrate reports is YOUR estimator's, not anyone else's.
"""
import sys
import json
from collections import Counter, defaultdict

ORDER = ["7B", "14B", "32B", "70B", ">70B", "none"]


def rank(m):
    """Coarse tier rank for a model field; tolerant of free-text suffixes."""
    if not m:
        return None
    head = str(m).split()[0].split("-")[0].strip()
    for i, t in enumerate(ORDER):
        if head == t:
            return i
    # accept a leading token like "14B" inside "14B|DeepSeek..."
    head2 = str(m).split("|")[0].split()[0].strip()
    return ORDER.index(head2) if head2 in ORDER else None


def load(path):
    sessions, calibrations = [], []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if "_schema" in obj:
                continue
            if "_calibration" in obj:
                calibrations.append(obj)
                continue
            sessions.append(obj)
    return sessions, calibrations


def field_dist(rows, field):
    def norm(v):
        return str(v).split()[0].split("|")[0] if v else v
    return dict(Counter(norm(r.get(field)) for r in rows))


def summarize(sessions, calibrations):
    print(f"sessions: {len(sessions)}")
    if sessions:
        ds = sorted(r["date"] for r in sessions if r.get("date"))
        if ds:
            print(f"date range: {ds[0]} -> {ds[-1]}")
    print(f"interaction: {field_dist(sessions, 'interaction')}")
    print()
    by_dom = defaultdict(list)
    for r in sessions:
        by_dom[r.get("domain", "?")].append(r)
    for dom in sorted(by_dom):
        sub = by_dom[dom]
        print(f"== {dom} (n={len(sub)}) ==")
        print(f"   delegatable        : {field_dist(sub, 'delegatable')}")
        print(f"   min_model DELEGATED: {field_dist(sub, 'min_model')}")
        print(f"   min_model_solo     : {field_dist(sub, 'min_model_solo')}")
        gaps = [rank(r.get("min_model_solo")) - rank(r.get("min_model"))
                for r in sub
                if rank(r.get("min_model_solo")) is not None
                and rank(r.get("min_model")) is not None]
        if gaps:
            avg = sum(gaps) / len(gaps)
            print(f"   solo-vs-delegated tier gap (avg over {len(gaps)}): {avg:+.1f} "
                  f"(large = value is in cloud orchestration)")
        print()
    if calibrations:
        print("existing _calibration notes:")
        for c in calibrations:
            print(f"   [{c.get('date','?')}] {c['_calibration'][:140]}...")


def calibrate(sessions):
    """Cross verified oracle outcomes against the estimated min_model, per domain."""
    verified = [r for r in sessions if r.get("verified")]
    print(f"verified oracle runs: {len(verified)} "
          f"({'enough' if len(verified) >= 8 else 'want >= 8'} to read a direction)\n")
    if not verified:
        print("No verified rows yet. Run a delegatable chunk through a real small model")
        print("(Ollama / OpenRouter / local) and fill the `verified` field. See CALIBRATION.md.")
        return
    by_dom = defaultdict(list)
    for r in verified:
        by_dom[r.get("domain", "?")].append(r)
    for dom in sorted(by_dom):
        sub = by_dom[dom]
        outc = Counter(r["verified"].get("outcome") for r in sub)
        print(f"== {dom} (n={len(sub)}) ==")
        print(f"   oracle outcomes: {dict(outc)}")
        for r in sub:
            est = r.get("min_model")
            v = r["verified"]
            arrow = {"pass": "estimate OK / possibly pessimistic",
                     "minor-fix": "estimate ~right",
                     "failed": "estimate OPTIMISTIC (real floor higher / none)"}.get(
                         v.get("outcome"), "?")
            print(f"     estimated {est!s:>5}  ->  ran {v.get('model')!s:>6} = "
                  f"{v.get('outcome'):<9}  => {arrow}")
        fails = outc.get("failed", 0)
        passes = outc.get("pass", 0)
        if fails and fails >= passes:
            print(f"   DIRECTION: estimator skews OPTIMISTIC for {dom} "
                  f"— discount by a tier when logging.")
        elif passes and not fails:
            print(f"   DIRECTION: estimator ~accurate-to-pessimistic for {dom} "
                  f"— trust or slightly relax.")
        else:
            print(f"   DIRECTION: mixed for {dom} — need more runs to call it.")
        print()
    print("Append your conclusion as a _calibration line (see SCHEMA.md). It is specific to")
    print("YOUR orchestrating model. Pair with a domain benchmark oracle (e.g. a graded test")
    print("suite for coding) to make each `verified` outcome objective, not a self-grade.")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(1)
    sessions, calibrations = load(args[0])
    if "--calibrate" in sys.argv:
        calibrate(sessions)
    else:
        summarize(sessions, calibrations)


if __name__ == "__main__":
    main()
