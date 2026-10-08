<!-- mcp-name: io.github.smarttasksorg/sf-smartroute -->
<h1 align="center">🦔 SmartRoute</h1>
<p align="center"><b>Route only what you trust. Gate agents and tools with trust scores and guardrails.</b></p>
<p align="center">
  <a href="https://iaiso.org">IAIso §5 · Orchestration</a> ·
  <a href="https://smarttasks.cloud">SmartTasks.cloud</a> ·
  <a href="#part-of-the-smart-family">the Smart* family</a>
</p>

---

## You're managing ten agents you have no reason to trust.

As AI reshapes how we work, a new gap opens: untrusted, uncoordinated agents create risk and rework. **SmartRoute** closes it —
`route` at the exact moment the gap bites, and it works the second you clone it
(a synthetic demo ships in `demo/`).

## Install

SmartRoute is not published on PyPI or any other package registry yet. Until
this section says otherwise, a package called `sf-smartroute` on any registry
is not ours, and neither is `smartroute`.

Install from a clone (Python 3.10 or later):

```bash
git clone https://github.com/SmartTasksOrg/sf-smartroute
cd sf-smartroute
python -m venv .venv
. .venv/bin/activate          # Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install .
sf-smartroute --demo
```

## Status

- **Version 3.0.0, experimental.** A small deterministic command-line tool with a bundled synthetic demo and two smoke tests.
- **Published:** nowhere yet; install from a clone (above).
- **Tested:** the 2 smoke tests in `tests/` on Python 3.12, Linux, on every push to master and every pull request (`.github/workflows/ci.yml`).
- **Not tested:** Windows and macOS; Python versions other than 3.12.
- **Security review:** none independent. Report vulnerabilities as described in [SECURITY.md](SECURITY.md).

## Run it in your stack

| Where you work | How you run it |
|---|---|
| **Python** | from a clone: `python -m pip install .` (not on PyPI yet) |
| **Go · Java · Node · PHP** | native ports in [`ports/`](ports/), each verified against the Python reference by [`ports/conformance/run.sh`](ports/conformance/run.sh) |
| **Flowise · OpenAI/Anthropic tools · GitHub Actions · LangChain · LlamaIndex · MCP · pre-commit · VS Code** | ready-made wrappers in [`integrations/`](integrations/), all calling one `adapter.py` |
| **CI / pre-commit** | add the hook from [`.pre-commit-hooks.yaml`](.pre-commit-hooks.yaml) |

## What's in this repo

- **Core engine** — [`src/sf_smartroute/`](src/sf_smartroute/): trust() -> TrustScore; gate() -> Decision. Deterministic, dependency-free.
- **CLI** — `sf-smartroute --demo` (and `--version`): a deterministic demo of the core.
- **Language ports** — [`ports/`](ports/): native Go, Java, Node, PHP implementations that reproduce the Python reference, with a shared conformance harness.
- **Framework integrations** — [`integrations/`](integrations/): Flowise, OpenAI/Anthropic function-calling, GitHub Action, LangChain, LlamaIndex, MCP server, pre-commit, VS Code extension — each a thin wrapper over one `adapter.py` bound to the core.
- **Also included** — a runnable [`demo/`](demo/), [`examples/`](examples/), the IAIso mapping [`spec/iaiso-map.json`](spec/iaiso-map.json), a browser [`site/playground.html`](site/playground.html), plus public smoke tests in `tests/`.

## How it works

SmartRoute works at **two altitudes, one trust model** — both deterministic,
dependency-free, and fail-loud:

- **Agent-level** — `trust(agent)` / `route()` score an agent by its declared
  capabilities (`read`, `write`, `delete`, `exec`, `network`): coarse, "should this
  agent be allowed to act at all."
- **Per-call** — `gate(request)` scores one concrete tool-access request and returns an
  allow/block `Decision` with a `0..1` trust score and the exact `ROUTE-*` signals that
  moved it. Every request starts fully trusted (`1.0`); each signal subtracts its weight;
  the call is **granted** when `score >= 0.5` (`MIN_SCORE`) **and** nothing hard-blocks.

| Rule | −weight | Fires when |
|---|---|---|
| `ROUTE-NO-IDENTITY` | 0.40 | the request carries no agent identity |
| `ROUTE-UNLISTED-TOOL` | 0.25 | the tool isn't on the read-only allowlist |
| `ROUTE-DANGEROUS-ACTION` | 0.50 | the action is destructive / high blast-radius |
| `ROUTE-WRITE-ACTION` | 0.20 | the action mutates state (and isn't already dangerous) |
| `ROUTE-SECRET-IN-PAYLOAD` | 0.60 | a secret/credential is present in the payload — **hard block** |
| `ROUTE-EXFIL` | 0.30 | a state-changing action has an external destination |
| `ROUTE-RATE` | 0.20 | `call_count` exceeds the rate limit (60) |
| `ROUTE-UNSCOPED` | 0.15 | no scope/permission was declared |

Rule IDs are namespaced `ROUTE-*` so output reads kin to the rest of the family
(SmartPangolin's `SEC-*`, SmartPrompt's `PROMPT-*`). `risk` bands the per-call score:
`low >= 0.75`, `medium >= 0.5`, else `high`.

### The data objects (UML)

These are real dataclasses in [`src/sf_smartroute/models.py`](src/sf_smartroute/models.py) — the
diagram and the code are the same thing:

```mermaid
classDiagram
    class Agent {
      +name: str
      +capabilities: list[str]
    }
    class TrustScore {
      +agent: str
      +score: float
      +allowed: bool
    }
    class RouteDecision {
      +agent: str
      +allowed: bool
      +reason: str
    }
    class Signal {
      +rule: str
      +weight: float
      +reason: str
    }
    class Decision {
      +granted: bool
      +score: float
      +risk: str
      +signals: list[Signal]
    }
    class IAIsoControl {
      +section: str
      +name: str
    }
    Decision "1" *-- "many" Signal : records
    RouteDecision ..> IAIsoControl : conforms to
    Decision ..> IAIsoControl : conforms to
```

## Where it sits in the architecture

SmartRoute doesn't stand alone — it stacks with the family, and everything conforms to
the IAIso standard — the same standard that governs SmartTasks' own apps, while each tool here stays standalone and drops into your architecture:

```mermaid
graph LR
    IAIso([IAIso standard]):::std
    Cloud([SmartTasks.cloud]):::cloud
    SmartPangolin[SmartPangolin]:::tool
    SmartPrompt[SmartPrompt]:::tool
    SmartCheck[SmartCheck]:::tool
    SmartSeal[SmartSeal]:::tool
    SmartStandard[SmartStandard]:::tool
    SmartSim[SmartSim]:::tool
    SmartMoat[SmartMoat]:::tool
    SmartRoute[SmartRoute]:::tool
    SmartFeed[SmartFeed]:::tool
    SmartPangolin -->|emits clean artifacts to| SmartSeal
    SmartPrompt -->|hands secret/PII flags to| SmartPangolin
    SmartPrompt -->|enforces prompt rules from| SmartStandard
    SmartCheck -->|stamps verified output with| SmartSeal
    SmartCheck -->|checks against rules from| SmartStandard
    SmartSeal -->|issues receipts consumed by| SmartCheck
    SmartSeal -->|issues receipts consumed by| SmartRoute
    SmartStandard -->|supplies rule sets to| SmartPrompt
    SmartStandard -->|supplies rule sets to| SmartCheck
    SmartSim -->|feeds role forecasts to| SmartMoat
    SmartSim -->|draws signals from| SmartFeed
    SmartMoat -->|consumes forecasts from| SmartSim
    SmartRoute -->|verifies receipts from| SmartSeal
    SmartRoute -->|enforces the standard from| SmartStandard
    SmartFeed -->|feeds signals to| SmartSim
    SmartFeed -->|feeds signals to| SmartMoat
    SmartPangolin -.conforms.-> IAIso
    SmartPangolin -.shares IAIso with.-> Cloud
    SmartPrompt -.conforms.-> IAIso
    SmartPrompt -.shares IAIso with.-> Cloud
    SmartCheck -.conforms.-> IAIso
    SmartCheck -.shares IAIso with.-> Cloud
    SmartSeal -.conforms.-> IAIso
    SmartSeal -.shares IAIso with.-> Cloud
    SmartStandard -.conforms.-> IAIso
    SmartStandard -.shares IAIso with.-> Cloud
    SmartSim -.conforms.-> IAIso
    SmartSim -.shares IAIso with.-> Cloud
    SmartMoat -.conforms.-> IAIso
    SmartMoat -.shares IAIso with.-> Cloud
    SmartRoute -.conforms.-> IAIso
    SmartRoute -.shares IAIso with.-> Cloud
    SmartFeed -.conforms.-> IAIso
    SmartFeed -.shares IAIso with.-> Cloud
    IAIso -.governs.-> Cloud
    classDef tool fill:#1c232d,stroke:#f5b83d,color:#efe9f5;
    classDef std fill:#04121f,stroke:#46d6c8,color:#46d6c8;
    classDef cloud fill:#1a1327,stroke:#a78bfa,color:#a78bfa;
    style SmartRoute stroke-width:3px,stroke:#ff6b6b;
```

- **SmartRoute verifies receipts from SmartSeal** →
- **SmartRoute enforces the standard from SmartStandard** →

Open [`site/playground.html`](site/playground.html) for the interactive version.

## Part of the Smart* family

One system, not nine projects — same mascot, same manifesto voice, same rule-ID style,
all aligned to the [IAIso standard](https://github.com/SmartTasksOrg/IAIso). Each is an independent, open-source, single-purpose tool you can integrate into your own architecture:

| Tool | IAIso | What it does |
|---|---|---|
| [SmartPangolin](https://github.com/SmartTasksOrg/sf-smartpangolin) | §1 · Secure Sharing | Scan before you share. Stop leaking secrets into AI models, agents, and tools. |
| [SmartPrompt](https://github.com/SmartTasksOrg/sf-smartprompt) | §4 · Context | Lint before you send. Bad prompt in, bad work out — and it's your name on it. |
| [SmartCheck](https://github.com/SmartTasksOrg/sf-smartcheck) | §2 · Verification | Check before you sign off. Catch the AI when it's confidently wrong. |
| [SmartSeal](https://github.com/SmartTasksOrg/sf-smartseal) | §3 · Provenance | Seal what you ship. A signed receipt so anyone can verify what they received. |
| [SmartStandard](https://github.com/SmartTasksOrg/sf-smartstandard) | §7 · Standards | Standardize before you scale. One shared, auditable convention for AI-assisted work. |
| [SmartSim](https://github.com/SmartTasksOrg/sf-smartsim) | §8 · Foresight | Simulate before it hits you. See your role's task-by-task collapse sequence. |
| [SmartMoat](https://github.com/SmartTasksOrg/sf-smartmoat) | §6 · Workforce | Know your moat. Score the tasks AI can't easily take — and widen them. |
| [SmartFeed](https://github.com/SmartTasksOrg/sf-smartfeed) | §9 · Awareness | Distill the firehose. A tight brief of only what moves your work. |

**Backed by the standard:** SmartRoute implements **IAIso §5 · Orchestration**.
**Open-source edition:** this repo is the simplified, single-purpose version, built for any org to integrate into its own architecture. SmartTasks' desktop app and [SmartTasks.cloud](https://smarttasks.cloud) run a more advanced, deeply-integrated implementation of the same IAIso governance — a separate product, not this code bundled.

## Who's behind this

- **Roen Branham** — CEO & AI Strategy Architect · CISSP-certified AI, security & governance architect; author of IAIso and sole inventor of the Z4 Semantic Fabric patent application. [LinkedIn](https://www.linkedin.com/in/roen-branham-167ab29/)
- **Le Vu Tanh** — CTO & Core Engineering Lead · Chief architect of the Cortex engine; large-scale system reliability and low-latency infrastructure — the engineer who ships what gets architected. [LinkedIn](https://www.linkedin.com/in/lee-thanh-76aa8ba0/)

The team behind IAIso & SmartTasks: a CISSP-certified security & governance architect
and a large-scale systems engineer — 20+ years shipping secure, AI-driven platforms for
regulated, blue-chip environments (Allianz, BMW, Rolls-Royce, Heidenhain).

<!-- SMARTTASKS-MODELS:START -->
## Runs on governed local models

Each card ships an OWASP-mapped **red-team** result and an `agent_hint`, so an orchestrator can trust-gate a model before wiring it into a loop — exactly SmartRoute's job.

This tool is local-first, so pair it with models you can actually vet. **SmartTasks** publishes 21+ governance-validated GGUF builds on Hugging Face — each with a machine-readable **scorecard** (capability tiers L1 Layman → L5 Agentic, IAIso conformance invariants (pass/warn/fail), OWASP-mapped garak red-team, transparency probes (viewpoint-alignment / over-refusal), and per-file SHA-256). Gate model selection on evidence, not vibes — and every finding, including warnings, is published in full.

→ **[SmartTasks on Hugging Face](https://huggingface.co/smarttasks)** · [Qwen3.6-27B](https://huggingface.co/smarttasks/Qwen3.6-27B-GGUF) (L5 agentic) · [react-agent-coder-llama-3.1-8b](https://huggingface.co/smarttasks/react-agent-coder-llama-3.1-8b-GGUF) (agentic coder) · [gpt-oss-20b](https://huggingface.co/smarttasks/gpt-oss-20b-GGUF) (open reasoning)
<!-- SMARTTASKS-MODELS:END -->

## Get in touch

- **Companies & enterprises:** [enterprise@smarttasks.cloud](mailto:enterprise@smarttasks.cloud) — we help
  teams integrate SmartRoute + IAIso into their architecture so governance and
  audit-readiness become a byproduct of how they already work.
- **The standard:** [IAIso](https://github.com/SmartTasksOrg/IAIso) · [iaiso.org](https://iaiso.org)
- **The product:** [SmartTasks.cloud](https://smarttasks.cloud)

Built by **SmartTasks Lab**. Apache-2.0. Contributions welcome.
