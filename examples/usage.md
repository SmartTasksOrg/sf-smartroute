# Using SmartRoute

```bash
smartroute --demo
```

<!-- SMARTTASKS-MODELS:START -->
> **Tip:** run this offline against a governance-validated local model — see the [SmartTasks GGUF models](https://huggingface.co/smarttasks) (each ships a scorecard, IAIso invariants + a garak red-team).
<!-- SMARTTASKS-MODELS:END -->

## Per-call gate

```python
from smartroute.core import gate

gate({"agent": "svc", "tool": "search", "action": "read", "scope": "reports:read"})
# -> Decision(granted=True, score=1.0, risk='low', signals=[])

d = gate({"agent": "", "tool": "db", "action": "delete",
          "payload": "DROP TABLE users; key=AKIAIOSFODNN7EXAMPLE", "call_count": 91})
print(d.granted, d.score, d.risk)          # False 0.0 high
for s in d.signals:
    print(s.rule, s.reason)                # ROUTE-NO-IDENTITY, ROUTE-DANGEROUS-ACTION, ...
```

Run it in Go, Java, Node, or PHP — see [`../ports/`](../ports/). Drop it into an agent
loop, MCP client, LangChain, LlamaIndex, Flowise, a GitHub Action, or VS Code — see
[`../integrations/`](../integrations/).
