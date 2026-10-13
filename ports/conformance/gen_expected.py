#!/usr/bin/env python3
"""Regenerate expected.json from the Python reference (smartroute.core.gate)."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..", "src")))
from smartroute.core import gate  # noqa: E402

def to_dict(name, d):
    return {"name": name, "granted": d.granted, "score": d.score, "risk": d.risk,
            "signals": [{"rule": s.rule, "weight": s.weight, "reason": s.reason} for s in d.signals]}

v = json.load(open(os.path.join(HERE, "vectors.json"), encoding="utf-8"))
out = {"results": [to_dict(c["name"], gate(c.get("request", {}))) for c in v["cases"]]}
with open(os.path.join(HERE, "expected.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False); f.write("\n")
print(f"wrote expected.json ({len(out['results'])} cases)")
