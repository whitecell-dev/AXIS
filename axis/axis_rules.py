#!/usr/bin/env python3
"""
AXIS-RULES: Enhanced β-reduction for JSON + Relational Algebra + Structure Registry
Pure decision logic, state transformations, and RA operations with prebuilt structures

Pipeline: JSON → Logic → New JSON (+ RA joins/aggregations + O(1) structure operations)
- If/then conditional logic with priority/conflict resolution
- Pure state transformations
- Deterministic rule application
- Enhanced: σ (select), π (project), ⨝ (join), exists_in, not_exists_in, AGGREGATE
- Structure registry integration for fast joins/semi-joins
- Cryptographic verification and audit trails
- Fixpoint iteration with loop detection

Usage:
    echo '{"age": 25, "role": "admin"}' | python axis_rules.py apply logic.yaml
"""

import json
import sys
import argparse
import os
from typing import Any, Dict, List, Union

# Import shared core functionality
try:
    from .axis_core import (canonicalize, sha3_256_hex, parse_condition_to_ast, 
                          evaluate_ast, get_timestamp, print_audit_summary)
    HAS_CORE = True
except ImportError:
    print("Warning: axis_core.py not found. Using local implementations.", file=sys.stderr)
    HAS_CORE = False

# Import RA primitives
try:
    from .axis_ra import (apply_ra_operation, is_ra_operation, extract_ra_operations, 
                        apply_ra_pipeline, generate_ra_audit, validate_ra_operation)
    HAS_RA = True
except ImportError:
    print("Warning: axis_ra.py not found. RA operations disabled.", file=sys.stderr)
    HAS_RA = False

# Optional YAML support
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

# Fallback implementations if axis_core not available
if not HAS_CORE:
    import hashlib
    import math
    import ast
    from datetime import datetime
    
    def canonicalize(obj: Any) -> Any:
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
        return hashlib.sha3_256(s.encode("utf-8")).hexdigest()
    
    def get_timestamp():
        return datetime.now().isoformat()
    
    def parse_condition_to_ast(condition: str) -> dict:
        # Simplified fallback implementation
        return {'type': 'literal', 'value': True}
    
    def evaluate_ast(ast_node: dict, context: dict) -> Any:
        # Simplified fallback implementation
        return ast_node.get('value', True)
    
    def print_audit_summary(audit: dict, component_name: str = ""):
        print(f"Audit Summary{' - ' + component_name if component_name else ''}:")
        print(f"  Rules Hash: {audit.get('rules_hash', 'N/A')[:16]}...")

# ============================================================================
# STRUCTURE REGISTRY INTEGRATION HELPERS  
# ============================================================================

def _uses_structure(config: dict) -> bool:
    """Check if operation references a structure"""
    structure_ops = ['join', 'difference', 'union', 'exists_in', 'not_exists_in']
    return any(op in config and 'using' in config[op] for op in structure_ops)

def _apply_structure_enhanced_ra(data, config, registry, structures_used_log):
    """Apply RA operation using structure registry"""
    
    if 'join' in config and 'using' in config['join']:
        # Enhanced join
        try:
            from .axis_structures import enhanced_join_with_structure
            result = enhanced_join_with_structure(data, config['join'], registry)
            structures_used_log.append(config['join']['using'])
            return result
        except ImportError:
            return apply_ra_operation(data, config)
    
    elif 'difference' in config and 'using' in config['difference']:
        # Enhanced difference
        try:
            from .axis_structures import enhanced_difference_with_structure
            result = enhanced_difference_with_structure(data, config['difference'], registry)
            structures_used_log.append(config['difference']['using'])
            return result
        except ImportError:
            return apply_ra_operation(data, config)
    
    elif 'exists_in' in config and 'using' in config['exists_in']:
        # Enhanced exists_in (semi-join)
        try:
            from .axis_structures import enhanced_exists_in_with_structure
            result = enhanced_exists_in_with_structure(data, config['exists_in'], registry)
            structures_used_log.append(config['exists_in']['using'])
            return result
        except ImportError:
            return apply_ra_operation(data, config)
    
    elif 'not_exists_in' in config and 'using' in config['not_exists_in']:
        # Enhanced not_exists_in (anti-join)
        try:
            from .axis_structures import enhanced_not_exists_in_with_structure
            result = enhanced_not_exists_in_with_structure(data, config['not_exists_in'], registry)
            structures_used_log.append(config['not_exists_in']['using'])
            return result
        except ImportError:
            return apply_ra_operation(data, config)
    
    else:
        # Fallback to standard RA
        return apply_ra_operation(data, config)

# ============================================================================
# ENHANCED RULE ENGINE (β-reduction + RA + Structures)
# ============================================================================

class RuleEngine:
    """Apply pure logic rules and RA operations to JSON state with structure registry"""
    
    def __init__(self, config: Union[dict, str]):
        if isinstance(config, str):
            if not HAS_YAML:
                raise RuntimeError("YAML support requires: pip install pyyaml")
            with open(config, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = config
        
        self.rules = self.config.get('rules', [])
        self.component_name = self.config.get('component', 'anonymous')
        self.max_iterations = self.config.get('max_iterations', 50)
        self.rules_hash = self._generate_rules_hash()
        
        # Structure registry integration
        self.registry = None
        if 'structures' in self.config:
            try:
                from .axis_structures import StructureRegistry
                self.registry = StructureRegistry(self.config)
            except ImportError:
                pass
    
    def _generate_rules_hash(self) -> str:
        """Generate hash of rules configuration"""
        canonical_rules = canonicalize({
            'component': self.component_name,
            'rules': self.rules,
            'max_iterations': self.max_iterations,
            'version': 'axis-rules@3.0.0'  # Updated for enhanced RA support
        })
        rules_json = json.dumps(canonical_rules, sort_keys=True, separators=(',', ':'))
        return sha3_256_hex(rules_json)
    
    def validate(self) -> List[str]:
        """Validate rules configuration and return error messages"""
        errors = []
        
        for i, rule in enumerate(self.rules):
            try:
                # Validate RA operations
                if HAS_RA and is_ra_operation(rule):
                    ra_ops = extract_ra_operations(rule)
                    for op in ra_ops:
                        ra_errors = validate_ra_operation(op, self.registry)
                        for error in ra_errors:
                            errors.append(f"Rule {i}: {error}")
                else:
                    # Validate traditional if/then rules
                    if 'if' in rule:
                        try:
                            if HAS_CORE:
                                parse_condition_to_ast(rule['if'])
                        except Exception as e:
                            errors.append(f"Rule {i}: Invalid condition '{rule['if']}': {e}")
                    
                    # Check for required then/else branches
                    if 'if' in rule and 'then' not in rule and 'else' not in rule:
                        errors.append(f"Rule {i}: Conditional rule requires 'then' or 'else' branch")
                    
                    # Validate priority values
                    if 'priority' in rule:
                        try:
                            int(rule['priority'])
                        except (ValueError, TypeError):
                            errors.append(f"Rule {i}: Priority must be an integer")
            
            except Exception as e:
                errors.append(f"Rule {i}: Validation error - {e}")
        
        return errors
    
    def apply(self, input_data: dict) -> dict:
        """Apply rules with RA operations, structure registry, fixpoint iteration, and conflict resolution"""
        # Deep copy to avoid mutating original
        new_state = json.loads(json.dumps(input_data))
        
        # Ensure error/computed fields exist
        new_state.setdefault('computed', {})
        new_state.setdefault('errors', [])
        
        iteration = 0
        changed = True
        total_changes = []
        conflicts = []
        ra_operations_applied = []
        structures_used = []
