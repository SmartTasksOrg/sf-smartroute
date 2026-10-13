"""SmartRoute — Route only what you trust. Gate agents and tools with trust scores and guardrails."""
from ._version import __version__
from . import core, models
from .core import gate, route, trust
