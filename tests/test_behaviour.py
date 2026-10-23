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
