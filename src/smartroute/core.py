"""SmartRoute core — route only what you trust, and gate every call.

Two altitudes, one trust model, both deterministic and dependency-free:

  * trust() / route() — agent-level: score an agent by its declared capabilities.
  * gate()            — per-call: score ONE concrete tool-access request (identity,
                        tool allowlist, dangerous/mutating actions, secrets, exfil,
                        rate, scope) and return an allow/block Decision with the exact
                        ROUTE-* signals that moved it.

The advanced ML/streaming implementation is a separate product in the SmartTasks
desktop app & cloud — not this code bundled.
"""
import json
import re
from .models import Agent, TrustScore, RouteDecision, Signal, Decision


# ── agent-level routing ───────────────────────────────────────────────
def _catalog():
    return [Agent("summarizer", ["read"]), Agent("db-writer", ["read", "write", "delete"]),
            Agent("web-fetcher", ["network"]), Agent("unknown-3p", ["read", "network", "exec"])]


RISK = {"delete": .5, "exec": .6, "network": .2, "write": .3, "read": .0}


def trust(agent: Agent, allowlist=("read", "network")) -> TrustScore:
    """Score an agent by its declared capabilities (coarse, agent-level)."""
    risk = sum(RISK.get(c, .4) for c in agent.capabilities)
    score = round(max(0, 1 - risk), 2)
    allowed = all(c in allowlist for c in agent.capabilities) and score >= .5
    return TrustScore(agent.name, score, allowed)


def route(allowlist=("read", "network")):
    """Route a catalog of agents against an allowlist — the agent-level view."""
    out = []
    for a in _catalog():
        ts = trust(a, allowlist)
        out.append(RouteDecision(a.name, ts.allowed,
                   "cleared" if ts.allowed else f"blocked (trust {ts.score}, caps {a.capabilities})"))
    return out


# ── per-call gate ──────────────────────────────────────────────────────
# Destructive / high-blast-radius verbs.
_DANGER = re.compile(
    r"\b(delete|drop|truncate|exec|shell|sudo|rm|rmdir|wire|transfer|payment|"
    r"refund|deploy|shutdown|revoke|grant|chmod|chown|purge)\b", re.I)
# State-changing (but not destructive) verbs.
_WRITE = re.compile(r"\b(write|update|insert|create|modify|patch|put|post|send|email)\b", re.I)
# Secrets/credentials in the payload (kin to SmartPangolin / SmartPrompt).
_SECRET = re.compile(
    r"(sk-[A-Za-z0-9]{12,}|AKIA[0-9A-Z]{12,}|-----BEGIN|password\s*=|api[_-]?key\s*=)", re.I)
# External destination markers.
_EXTERNAL = re.compile(r"(https?://|ftp://|@[\w.-]+\.\w+|\bexternal\b)", re.I)

# Read-only tools that are safe by default.
SAFE_TOOLS = {"search", "fetch_data", "read", "list", "get", "lookup",
              "retrieve", "summarize", "describe", "count"}

RATE_LIMIT = 60      # rate rule: call_count > 60
MIN_SCORE = 0.5      # grant threshold
HARD_BLOCK = {"ROUTE-SECRET-IN-PAYLOAD"}   # fail closed regardless of score


def _stringify(payload) -> str:
    if payload is None:
        return ""
    if isinstance(payload, (dict, list)):
        return json.dumps(payload)
    return str(payload)


def gate(request: dict) -> Decision:
    """Score one agent tool-access request (fine-grained, per-call). Deterministic."""
    agent = str(request.get("agent") or "").strip()
    tool = str(request.get("tool") or "").strip().lower()
    action = str(request.get("action") or "")
    payload = _stringify(request.get("payload"))
    scope = request.get("scope")
    try:
        call_count = int(request.get("call_count") or 0)
    except (TypeError, ValueError):
        call_count = 0

    signals = []
    if not agent:
        signals.append(Signal("ROUTE-NO-IDENTITY", 0.4, "no agent identity on the request"))
    if tool and tool not in SAFE_TOOLS:
        signals.append(Signal("ROUTE-UNLISTED-TOOL", 0.25,
                              f"tool '{tool}' is not on the read-only allowlist"))
    if _DANGER.search(action):
        signals.append(Signal("ROUTE-DANGEROUS-ACTION", 0.5,
                              "action is destructive / high blast-radius"))
    elif _WRITE.search(action):
        signals.append(Signal("ROUTE-WRITE-ACTION", 0.2, "action mutates state"))
    if _SECRET.search(payload):
        signals.append(Signal("ROUTE-SECRET-IN-PAYLOAD", 0.6,
                              "a secret/credential is present in the payload"))
    if _EXTERNAL.search(payload) and (_DANGER.search(action) or _WRITE.search(action)):
        signals.append(Signal("ROUTE-EXFIL", 0.3,
                              "state-changing action with an external destination"))
    if call_count > RATE_LIMIT:
        signals.append(Signal("ROUTE-RATE", 0.2,
                              f"call_count {call_count} exceeds rate limit {RATE_LIMIT}"))
    if not scope:
        signals.append(Signal("ROUTE-UNSCOPED", 0.15, "no scope/permission declared"))

    score = max(0.0, round(1.0 - sum(s.weight for s in signals), 3))
    hard = any(s.rule in HARD_BLOCK for s in signals)
    granted = (score >= MIN_SCORE) and not hard
    risk = "low" if score >= 0.75 else ("medium" if score >= MIN_SCORE else "high")
    return Decision(granted, score, risk, signals)
