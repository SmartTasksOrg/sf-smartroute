"""SmartRoute CLI.

    sf-smartroute --demo
    sf-smartroute AGENTS.json [--allow read,network] [--min-score 0.5] [--risk RISK.json] [--json]

AGENTS.json is a list of {"name": ..., "capabilities": [...]}. Exit code 0 when
every agent is cleared, 1 when any is blocked.
"""
import argparse
import json
import os
import sys
from dataclasses import asdict

from . import core
from ._version import __version__

BANNER = f"\n🦔 SmartRoute {__version__}  ·  IAIso §5 · Orchestration"
FOOTER = "\nBacked by IAIso §5 · Orchestration · part of the Smart* family · https://smarttasks.cloud\n"


def _demo_dir():
    return os.path.join(os.path.dirname(__file__), "..", "..", "demo")


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if "--version" in argv:
        print(f"SmartRoute {__version__}"); return 0
    if not argv or "--demo" in argv:
        print(BANNER); print(core_demo()); print(FOOTER); return 0

    ap = argparse.ArgumentParser(prog="sf-smartroute")
    ap.add_argument("agents", help="JSON file listing agents and their capabilities")
    ap.add_argument("--allow", default=",".join(core.DEFAULT_ALLOWLIST),
                    help="comma-separated capabilities agents may use")
    ap.add_argument("--min-score", type=float, default=core.MIN_SCORE)
    ap.add_argument("--risk", default=None, help="JSON file mapping capability -> risk weight")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    allow = tuple(c.strip() for c in a.allow.split(",") if c.strip())
    risk = core.load_risk(a.risk) if a.risk else None
    decisions = core.route(core.load_agents(a.agents), allow, risk=risk, min_score=a.min_score)
    if a.json:
        print(json.dumps([asdict(d) for d in decisions], indent=2))
    else:
        for d in decisions:
            print(f"  {'✓' if d.allowed else '✗'} {d.agent:<14} {d.reason}")
    return 0 if all(d.allowed for d in decisions) else 1


def core_demo() -> str:
    return _DEMO()


def _DEMO():
    out = ["routing the 4 sample agents against allowlist (read, network):"]
    for d in core.route():
        mark = "✓" if d.allowed else "✗"
        out.append(f"  {mark} {d.agent:<14} {d.reason}")
    return "\n".join(out)

if __name__ == "__main__":
    sys.exit(main())
