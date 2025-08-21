#!/usr/bin/env python3
"""
AXIS: React for Deterministic Reasoning
Zero-boilerplate Python library for hash-verified, cross-platform logic

Core exports for simple imports:
    from axis import RuleEngine, validate, load_rules
"""

from .engine.rule_engine import RuleEngine
from .utils.validator import validate, quick_validate
from .engine.hash import sha3_256_hex, canonicalize

__version__ = "1.0.0"
__all__ = [
    "RuleEngine", 
    "validate", 
    "quick_validate",
    "load_rules",
    "sha3_256_hex",
    "canonicalize"
]

def load_rules(path: str) -> RuleEngine:
    """Load rules from YAML file - convenience function"""
    return RuleEngine(path)
