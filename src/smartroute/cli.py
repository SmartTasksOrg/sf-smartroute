"""SmartRoute CLI — run `smartroute --demo`."""
import sys
from . import core
from ._version import __version__


def core_demo() -> str:
    out = ["agent-level routing (allowlist: read, network):"]
    for d in core.route():
        out.append(f"  {'ok ' if d.allowed else 'no '} {d.agent:<14} {d.reason}")
    out.append("")
    out.append("per-call gate:")
    reqs = [
        {"agent": "svc-reporting", "tool": "search", "action": "read", "scope": "reports:read"},
        {"agent": "", "tool": "db", "action": "delete",
         "payload": "DROP TABLE users; key=AKIAIOSFODNN7EXAMPLE", "call_count": 91},
    ]
    for r in reqs:
        g = core.gate(r)
        verb = "ALLOW" if g.granted else "BLOCK"
        out.append(f"  {verb}  score={g.score:<5} risk={g.risk:<6} "
                   f"tool={r.get('tool')!r} action={r.get('action')!r}")
        for s in g.signals:
            out.append(f"      x {s.rule} (-{s.weight}) {s.reason}")
    return "\n".join(out)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if "--version" in argv:
        print(f"SmartRoute {__version__}")
        return 0
    print(f"\nSmartRoute {__version__}  -  IAIso \u00a75 \u00b7 Orchestration")
    print(core_demo())
    print("\nBacked by IAIso \u00a75 \u00b7 Orchestration \u00b7 part of the Smart* family "
          "\u00b7 https://smarttasks.cloud\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
