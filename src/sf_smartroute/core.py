"""SmartRoute core — trust-gate agents before they act.

Each agent declares the capabilities it needs (`read`, `write`, `network`,
`exec`, ...). An agent is cleared only when every capability is on the
allowlist *and* its trust score — 1 minus the summed risk of its
capabilities — is at least `min_score`. Risk weights, the allowlist and the
minimum score are all yours to set; the defaults are a starting point.

    agents = load_agents("agents.json")      # [{"name": ..., "capabilities": [...]}, ...]
    for d in route(agents, allowlist=("read", "network")):
        print(d.agent, d.allowed, d.reason)
"""
from __future__ import annotations

import json
import re
from typing import Iterable, Mapping

from .models import Agent, RouteDecision, TrustScore

RISK = {"delete": .5, "exec": .6, "network": .2, "write": .3, "read": .0}
#: Risk given to a capability that is not in the risk table.
UNKNOWN_RISK = .4
DEFAULT_ALLOWLIST = ("read", "network")
MIN_SCORE = .5

_CAPABILITY = re.compile(r"^[a-z][a-z0-9_.-]*$")


def _sample_catalog() -> list[Agent]:
    """The four sample agents shown by `--demo`."""
    return [Agent("summarizer", ["read"]), Agent("db-writer", ["read", "write", "delete"]),
            Agent("web-fetcher", ["network"]), Agent("unknown-3p", ["read", "network", "exec"])]


_catalog = _sample_catalog   # kept for code written against version 3.0


def trust(agent: Agent, allowlist: Iterable[str] = DEFAULT_ALLOWLIST, *,
          risk: Mapping[str, float] | None = None, min_score: float = MIN_SCORE,
          unknown_risk: float = UNKNOWN_RISK) -> TrustScore:
    """Score one agent and decide whether it may run."""
    table = RISK if risk is None else risk
    allow = set(allowlist)
    total = sum(table.get(c, unknown_risk) for c in agent.capabilities)
    score = round(max(0.0, 1 - total), 2)
    allowed = all(c in allow for c in agent.capabilities) and score >= min_score
    return TrustScore(agent.name, score, allowed)


def _reason(agent: Agent, ts: TrustScore, allow: set[str], min_score: float) -> str:
    if ts.allowed:
        return "cleared"
    outside = [c for c in agent.capabilities if c not in allow]
    parts = [f"trust {ts.score}"]
    if outside:
        parts.append(f"not allowed: {outside}")
    if ts.score < min_score:
        parts.append(f"below minimum {min_score}")
    return f"blocked ({', '.join(parts)}, caps {agent.capabilities})"


def route(agents: Iterable[Agent] | None = None, allowlist: Iterable[str] = DEFAULT_ALLOWLIST, *,
          risk: Mapping[str, float] | None = None, min_score: float = MIN_SCORE,
          unknown_risk: float = UNKNOWN_RISK) -> list[RouteDecision]:
    """Decide, for each agent, whether it is cleared to run.

    With no `agents`, routes the sample catalog used by the demo.
    """
    pool = list(_sample_catalog() if agents is None else agents)
    allow = set(allowlist)
    out = []
    for a in pool:
        ts = trust(a, allow, risk=risk, min_score=min_score, unknown_risk=unknown_risk)
        out.append(RouteDecision(a.name, ts.allowed, _reason(a, ts, allow, min_score)))
    return out


def parse_agents(data) -> list[Agent]:
    """Build agents from a list of {"name", "capabilities"} dicts (or {"agents": [...]})."""
    if isinstance(data, dict):
        data = data.get("agents", data)
    if not isinstance(data, list):
        raise ValueError("expected a list of agents or {\"agents\": [...]}")
    agents, seen = [], set()
    for i, item in enumerate(data):
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"]:
            raise ValueError(f"agent {i}: needs a non-empty string 'name'")
        caps = item.get("capabilities", [])
        if not isinstance(caps, list) or not all(isinstance(c, str) and _CAPABILITY.match(c) for c in caps):
            raise ValueError(f"agent {item['name']!r}: 'capabilities' must be a list of lowercase names")
        if item["name"] in seen:
            raise ValueError(f"agent {item['name']!r} is listed twice")
        seen.add(item["name"])
        agents.append(Agent(item["name"], list(caps)))
    return agents


def load_agents(path: str) -> list[Agent]:
    with open(path, encoding="utf-8") as fh:
        return parse_agents(json.load(fh))


def load_risk(path: str) -> dict[str, float]:
    with open(path, encoding="utf-8") as fh:
        table = json.load(fh)
    if not isinstance(table, dict) or not all(isinstance(v, (int, float)) and v >= 0 for v in table.values()):
        raise ValueError("risk file must map capability names to non-negative numbers")
    return {str(k): float(v) for k, v in table.items()}
