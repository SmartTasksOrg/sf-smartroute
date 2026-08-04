"""SmartRoute core — trust-gate agents before they act."""
import json, os
from .models import Agent, TrustScore, RouteDecision

def _catalog():
    return [Agent("summarizer", ["read"]), Agent("db-writer", ["read", "write", "delete"]),
            Agent("web-fetcher", ["network"]), Agent("unknown-3p", ["read", "network", "exec"])]

RISK = {"delete": .5, "exec": .6, "network": .2, "write": .3, "read": .0}

def trust(agent: Agent, allowlist=("read", "network")) -> TrustScore:
    risk = sum(RISK.get(c, .4) for c in agent.capabilities)
    score = round(max(0, 1 - risk), 2)
    allowed = all(c in allowlist for c in agent.capabilities) and score >= .5
    return TrustScore(agent.name, score, allowed)

def route(allowlist=("read", "network")):
    out = []
    for a in _catalog():
        ts = trust(a, allowlist)
        out.append(RouteDecision(a.name, ts.allowed,
                   "cleared" if ts.allowed else f"blocked (trust {ts.score}, caps {a.capabilities})"))
    return out
