#!/usr/bin/env python3
"""SmartRoute integration adapter — the single source of truth for every
framework wrapper in this folder. Exposes TOOL_NAME, DESCRIPTION, INPUT_SCHEMA
and run(payload)->dict, plus a CLI:  python adapter.py --file <input>
"""
import argparse
import json
import os
import sys

from smartroute.core import gate

TOOL_NAME = "smartroute_gate"
DESCRIPTION = "Gate one agent tool-access request: return an allow/block decision with a 0..1 trust score and the ROUTE-* signals that moved it."
INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "agent": {
                "type": "string",
                "description": "Agent identity"
        },
        "tool": {
                "type": "string",
                "description": "Tool being called"
        },
        "action": {
                "type": "string",
                "description": "Action verb / description"
        },
        "payload": {
                "type": "string",
                "description": "Action payload (checked for secrets/exfil)"
        },
        "scope": {
                "type": "string",
                "description": "Declared scope/permission"
        },
        "call_count": {
                "type": "integer",
                "description": "Calls so far this window",
                "default": 0
        }
    },
    "required": ["tool", "action"],
}


def _read(p):
    with open(p, encoding="utf-8", errors="ignore") as f:
        return f.read()


def run(payload):
    """Run SmartRoute on a payload dict and return a compact, JSON-safe result."""
    d = gate(payload)
    result = {'granted': d.granted, 'score': d.score, 'risk': d.risk,
              'signals': [{'rule': s.rule, 'weight': s.weight, 'reason': s.reason} for s in d.signals]}
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=DESCRIPTION)
    ap.add_argument("--text")
    ap.add_argument("--file")
    ap.add_argument("--root")
    ap.add_argument("--sources")
    args = ap.parse_args(argv)
    import json as _j
    raw = args.file or args.text or ''
    if raw and os.path.exists(raw):
        payload = _j.load(open(raw, encoding='utf-8'))
    elif raw:
        try:
            payload = _j.loads(raw)
        except Exception:
            payload = {}
    else:
        payload = {}
    print(json.dumps(run(payload)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
