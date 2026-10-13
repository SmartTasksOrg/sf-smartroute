"""UML data objects for SmartRoute — the diagram in the README is these classes."""
from __future__ import annotations
from dataclasses import dataclass


# ── agent-level routing ──────────────────────────────────────────────
@dataclass
class Agent:
    name: str
    capabilities: list[str]


@dataclass
class TrustScore:
    agent: str
    score: float
    allowed: bool


@dataclass
class RouteDecision:
    agent: str
    allowed: bool
    reason: str


# ── per-call gate ────────────────────────────────────────────────────
@dataclass
class Signal:
    rule: str
    weight: float
    reason: str


@dataclass
class Decision:
    granted: bool
    score: float
    risk: str
    signals: list[Signal]
