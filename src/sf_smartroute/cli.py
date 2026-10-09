"""SmartRoute CLI — run `sf-smartroute --demo`."""
import os, sys, json
from . import core
from ._version import __version__


def _demo_dir():
    return os.path.join(os.path.dirname(__file__), "..", "..", "demo")


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if "--version" in argv:
        print(f"SmartRoute {__version__}"); return 0
    demo = "--demo" in argv or not argv
    print(f"\n🦔 SmartRoute {__version__}  ·  IAIso §5 · Orchestration")
    result = core_demo()
    print(result)
    print(f"\nBacked by IAIso §5 · Orchestration · part of the Smart* family · https://smarttasks.cloud\n")
    return 0


def core_demo() -> str:
    return _DEMO()


def _DEMO():
    out = ["routing agents against allowlist (read, network):"]
    for d in core.route():
        mark = "✓" if d.allowed else "✗"
        out.append(f"  {mark} {d.agent:<14} {d.reason}")
    return "\n".join(out)

if __name__ == "__main__":
    sys.exit(main())
