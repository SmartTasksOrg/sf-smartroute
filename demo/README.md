# demo

- `smartroute --demo` shows both altitudes: agent-level routing and the per-call gate.
- `request.json` is a deliberately risky tool-access request (no identity, unlisted tool,
  destructive action, secret in payload, external destination, rate breach). Gate it:

```python
import json
from smartroute.core import gate
print(gate(json.load(open("demo/request.json"))))   # granted=False, risk='high'
```
