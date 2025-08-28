"""
AXIS: Deterministic JSON Math Engine

"LLMs guess; AXIS proves."
"""

__version__ = "0.1.0"
__all__ = [
    "canonicalize", 
    "sha3_256_hex",
    "PipelineEngine",
    "RuleEngine", 
    "AdapterEngine",
    "StructureRegistry"
]

try:
    from .axis_core import canonicalize, sha3_256_hex
    from .axis_pipes import PipelineEngine
    from .axis_rules import RuleEngine
    from .axis_adapters import AdapterEngine
    from .axis_structures import StructureRegistry
except ImportError:
    # Handle missing dependencies gracefully
    pass
