# Changelog

## 3.0.0 — absorbed the per-call gate
- **Two altitudes, one trust model**: kept agent-level `trust()`/`route()` and added a
  real per-call `gate(request) -> Decision` engine (formerly a separate prototype),
  with `ROUTE-*` signals, fail-closed secret block, `MIN_SCORE = 0.5`, rate limit 60.
- **Language ports**: native Go, Java, Node, PHP of `gate()`, each verified against the
  Python reference by a shared conformance harness.
- **Framework integrations**: LangChain, LlamaIndex, Flowise, OpenAI/Anthropic
  function-calling, a zero-dep MCP server, a VS Code extension, and a GitHub Action.
- **UML data objects** now include `Signal` and `Decision` alongside `Agent`/`TrustScore`/`RouteDecision`.


## 2.x — standalone tool (pre-family)
## 1.x — initial release
