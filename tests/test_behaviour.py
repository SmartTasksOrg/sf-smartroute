"""Behaviour of core.trust and core.route (agent-level trust from declared capabilities)."""
from sf_smartroute import core
from sf_smartroute.models import Agent


def test_read_only_agent_is_fully_trusted():
    t = core.trust(Agent("a", ["read"]))
    assert t.score == 1.0 and t.allowed


def test_risk_adds_up_per_capability():
    assert core.trust(Agent("a", ["network"])).score == 0.8
    assert core.trust(Agent("a", ["read", "write", "delete"])).score == 0.2
    assert core.trust(Agent("a", ["exec", "delete"])).score == 0.0      # floored at 0


def test_unknown_capabilities_carry_a_default_risk():
    assert core.trust(Agent("a", ["teleport"])).score == 0.6


def test_a_capability_outside_the_allowlist_blocks_even_with_a_high_score():
    t = core.trust(Agent("a", ["write"]))
    assert t.score == 0.7 and not t.allowed
    assert core.trust(Agent("a", ["write"]), allowlist=("read", "write")).allowed


def test_a_low_score_blocks_even_inside_the_allowlist():
    t = core.trust(Agent("a", ["write", "delete"]), allowlist=("write", "delete"))
    assert t.score == 0.2 and not t.allowed


def test_route_over_the_sample_catalog():
    d = {r.agent: r for r in core.route()}
    assert {a for a, r in d.items() if r.allowed} == {"summarizer", "web-fetcher"}
    assert d["db-writer"].reason.startswith("blocked (trust 0.2")
    assert d["summarizer"].reason == "cleared"


def test_route_uses_the_agents_you_pass():
    """Version 3.0 ignored its input and always routed the sample catalog."""
    mine = [Agent("crm-reader", ["read"]), Agent("mailer", ["network", "write"])]
    d = {r.agent: r for r in core.route(mine)}
    assert set(d) == {"crm-reader", "mailer"}
    assert d["crm-reader"].allowed and not d["mailer"].allowed
    assert "not allowed: ['write']" in d["mailer"].reason


def test_risk_weights_and_minimum_score_are_configurable():
    a = Agent("a", ["write"])
    assert core.trust(a, ("write",), risk={"write": 0.9}).allowed is False      # score 0.1 < 0.5
    assert core.trust(a, ("write",), risk={"write": 0.9}, min_score=0.1).allowed
    assert core.trust(Agent("b", ["teleport"]), ("teleport",), unknown_risk=0.9).score == 0.1
    d = core.route([a], ("write",), min_score=0.8)[0]
    assert "below minimum 0.8" in d.reason


def test_agent_files_are_validated(tmp_path):
    import json, pytest
    ok = tmp_path / "agents.json"
    ok.write_text(json.dumps({"agents": [{"name": "x", "capabilities": ["read"]}]}))
    assert core.load_agents(str(ok)) == [Agent("x", ["read"])]
    for bad in ([{"capabilities": ["read"]}], [{"name": "x", "capabilities": "read"}],
                [{"name": "x", "capabilities": ["Read Everything"]}],
                [{"name": "x"}, {"name": "x"}], {"not": "a list"}):
        with pytest.raises(ValueError):
            core.parse_agents(bad)


def test_cli_routes_a_file_and_sets_the_exit_code(tmp_path, capsys):
    import json
    from sf_smartroute import cli
    f = tmp_path / "agents.json"
    f.write_text(json.dumps([{"name": "reader", "capabilities": ["read"]}]))
    assert cli.main([str(f)]) == 0
    f.write_text(json.dumps([{"name": "shell", "capabilities": ["exec"]}]))
    assert cli.main([str(f), "--json"]) == 1
    assert '"allowed": false' in capsys.readouterr().out
    assert cli.main([str(f), "--allow", "exec", "--min-score", "0.4"]) == 0
