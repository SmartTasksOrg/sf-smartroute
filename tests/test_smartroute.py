from smartroute import cli

def test_demo_runs():
    assert cli.main(["--demo"]) == 0

def test_demo_produces_output():
    out = cli.core_demo()
    assert isinstance(out, str) and len(out) > 0


def test_gate_smoke():
    from smartroute import core
    assert core.gate({"agent": "a", "tool": "search", "action": "read", "scope": "r"}).granted
    assert not core.gate({"agent": "a", "tool": "db", "action": "delete", "scope": "x"}).granted
