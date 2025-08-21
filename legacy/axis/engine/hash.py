#!/usr/bin/env python3
"""
Cryptographic verification and canonicalization
Ensures deterministic execution across platforms
"""

import json
import math
import hashlib
from typing import Any

def canonicalize(obj: Any) -> Any:
    """
    Cross-target deterministic canonicalization
    - Sort dict keys
    - Convert ints to floats for consistent numerics
    - Reject NaN/Inf
    - Preserve list order
    """
    if isinstance(obj, dict):
        return {k: canonicalize(obj[k]) for k in sorted(obj.keys())}
    elif isinstance(obj, list):
        return [canonicalize(v) for v in obj]
    elif isinstance(obj, (int, float)):
        f = float(obj)
        if not math.isfinite(f):
            raise ValueError("Non-finite numbers not allowed")
        return f
    else:
        return obj

def sha3_256_hex(s: str) -> str:
    """Content addressing for IR verification"""
    return hashlib.sha3_256(s.encode("utf-8")).hexdigest()

def generate_ir_hash(rules: dict, component_name: str) -> str:
    """Generate cryptographic hash of canonical rules"""
    canonical_rules = canonicalize({
        'component': component_name,
        'rules': rules,
        'compiler_version': 'axis@1.0.0'
    })
    ir_json = json.dumps(canonical_rules, sort_keys=True, separators=(',', ':'))
    return sha3_256_hex(ir_json)
