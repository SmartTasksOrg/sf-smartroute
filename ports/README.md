# SmartRoute — language ports

The same deterministic per-call trust gate, natively in five languages. Each port
reproduces the Python reference (`smartroute.core.gate`) **exactly** — the same
rule IDs, weights, reason strings, ordering, score (`1 − Σweights`, clamped, 3 dp),
fail-closed secret block, `MIN_SCORE = 0.5` grant boundary, and risk bands.

| Language | Entry | Runtime |
|---|---|---|
| Python (reference) | `smartroute.core.gate` | 3.8+ |
| Node | [`node/`](node/) | zero-dep |
| Go | [`go/`](go/) | stdlib only |
| Java | [`java/`](java/) | JDK-only |
| PHP | [`php/`](php/) | no deps |

## Conformance

```bash
ports/conformance/run.sh
```

Runs every available runtime against [`conformance/vectors.json`](conformance/vectors.json)
and diffs each against [`conformance/expected.json`](conformance/expected.json) (regenerated
from Python). Missing runtimes **SKIP** — they never fail the run — so this drops straight
into CI. `compare.py` normalises numeric formatting so a language printing `0.5` vs `0.50`
is not a spurious diff.
