#!/usr/bin/env python3
"""
AXIS-CORE: Shared primitives and helpers
Central module for canonicalization, hashing, and AST evaluation

This eliminates duplication across axis_pipes.py, axis_rules.py, axis_adapters.py, etc.
All shared functionality lives here to prevent drift and ensure consistency.
"""

import json
import hashlib
import math
import ast
from typing import Any, Dict, List, Union

# ============================================================================
# CANONICALIZATION & HASHING
# ============================================================================

def canonicalize(obj: Any) -> Any:
    """Cross-target deterministic canonicalization"""
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
    """Content addressing for verification across all AXIS components"""
    return hashlib.sha3_256(s.encode("utf-8")).hexdigest()

def generate_content_hash(obj: Any) -> str:
    """Generate hash for any canonicalizable object"""
    canonical = canonicalize(obj)
    content = json.dumps(canonical, sort_keys=True, separators=(',', ':'))
    return sha3_256_hex(content)

# ============================================================================
# SECURE AST EVALUATION
# ============================================================================

ALLOWED_OPS = {
    'eq', 'noteq', 'gt', 'lt', 'gte', 'lte', 'in', 'notin',
    'and', 'or', 'not'
}

def parse_condition_to_ast(condition: str) -> dict:
    """Parse condition string to restricted AST"""
    def _convert(node):
        if isinstance(node, ast.BoolOp):
            op_name = node.op.__class__.__name__.lower()
            if op_name not in ALLOWED_OPS:
                raise ValueError(f"Operation {op_name} not allowed")
            return {
                'type': 'logical',
                'op': op_name,
                'values': [_convert(v) for v in node.values]
            }
        elif isinstance(node, ast.Compare):
            if len(node.ops) != 1:
                raise ValueError("Only single comparisons supported")
            op_name = node.ops[0].__class__.__name__.lower()
            if op_name not in ALLOWED_OPS:
                raise ValueError(f"Operation {op_name} not allowed")
            return {
                'type': 'binary_op',
                'op': op_name,
                'left': _convert(node.left),
                'right': _convert(node.comparators[0])
            }
        elif isinstance(node, ast.UnaryOp):
            op_name = node.op.__class__.__name__.lower()
            if op_name not in ALLOWED_OPS:
                raise ValueError(f"Operation {op_name} not allowed")
            return {
                'type': 'unary_op',
                'op': op_name,
                'operand': _convert(node.operand)
            }
        elif isinstance(node, ast.Name):
            return {'type': 'var', 'name': node.id}
        elif isinstance(node, ast.Constant):
            return {'type': 'literal', 'value': node.value}
        elif isinstance(node, ast.Attribute):
            return {'type': 'var', 'name': _get_full_name(node)}
        else:
            raise ValueError(f"Unsupported node: {ast.dump(node)}")
    
    def _get_full_name(node):
        """Convert ast.Attribute to dot notation"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{_get_full_name(node.value)}.{node.attr}"
        else:
            raise ValueError("Unsupported attribute node")
    
    try:
        parsed = ast.parse(condition, mode='eval')
        return _convert(parsed.body)
    except Exception as e:
        raise ValueError(f"Failed to parse condition '{condition}': {e}")

def evaluate_ast(ast_node: dict, context: dict) -> Any:
    """Evaluate AST against context - pure function"""
    node_type = ast_node['type']
    
    if node_type == 'var':
        name = ast_node['name']
        if '.' in name:
            parts = name.split('.')
            value = context
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return None
            return value
        return context.get(name)
    elif node_type == 'literal':
        return ast_node['value']
    elif node_type == 'binary_op':
        left = evaluate_ast(ast_node['left'], context)
        right = evaluate_ast(ast_node['right'], context)
        op = ast_node['op']
        try:
            if op == 'eq': return left == right
            elif op == 'noteq': return left != right
            elif op == 'gt': return left > right
            elif op == 'lt': return left < right
            elif op == 'gte': return left >= right
            elif op == 'lte': return left <= right
            elif op == 'in': return left in right
            elif op == 'notin': return left not in right
        except TypeError:
            return False
        return False
    elif node_type == 'unary_op':
        operand = evaluate_ast(ast_node['operand'], context)
        if ast_node['op'] == 'not':
            return not operand
        return operand
    elif node_type == 'logical':
        values = [evaluate_ast(v, context) for v in ast_node['values']]
        if ast_node['op'] == 'and':
            return all(values)
        elif ast_node['op'] == 'or':
            return any(values)
    return False

def safe_eval_predicate(predicate: str, context: dict) -> bool:
    """Safely evaluate predicate expressions (used by RA module)"""
    try:
        parsed = ast.parse(predicate, mode='eval')
        return _eval_ast_node(parsed.body, context)
    except Exception as e:
        return False

def _eval_ast_node(node, context: dict) -> Any:
    """Evaluate AST node against context (simplified version for RA)"""
    if isinstance(node, ast.BoolOp):
        op_name = node.op.__class__.__name__.lower()
        if op_name == 'and':
            return all(_eval_ast_node(v, context) for v in node.values)
        elif op_name == 'or':
            return any(_eval_ast_node(v, context) for v in node.values)
    
    elif isinstance(node, ast.Compare):
        left = _eval_ast_node(node.left, context)
        right = _eval_ast_node(node.comparators[0], context)
        op = node.ops[0].__class__.__name__.lower()
        
        try:
            if op == 'eq': return left == right
            elif op == 'noteq': return left != right
            elif op == 'gt': return left > right
            elif op == 'lt': return left < right
            elif op == 'gte': return left >= right
            elif op == 'lte': return left <= right
            elif op == 'in': return left in right
            elif op == 'notin': return left not in right
        except TypeError:
            return False
    
    elif isinstance(node, ast.UnaryOp):
        if node.op.__class__.__name__.lower() == 'not':
            return not _eval_ast_node(node.operand, context)
    
    elif isinstance(node, ast.Name):
        name = node.id
        lname = name.lower()
        if lname == 'true':  return True
        if lname == 'false': return False
        if lname in ('null', 'none'): return None
        return context.get(name)
    
    
    elif isinstance(node, ast.Attribute):
        # Handle dot notation like user.email
        obj = _eval_ast_node(node.value, context)
        if isinstance(obj, dict):
            return obj.get(node.attr)
        return None
    
    elif isinstance(node, ast.Constant):
        return node.value
    
    elif isinstance(node, ast.Str):  # Python < 3.8 compatibility
        return node.s
    
    elif isinstance(node, ast.Num):  # Python < 3.8 compatibility
        return node.n
    
    return None

# ============================================================================
# STRUCTURE REGISTRY HELPERS
# ============================================================================

def uses_structure(config: dict) -> bool:
    """Check if operation references a structure"""
    if 'join' in config and 'using' in config['join']:
        return True
    if 'difference' in config and 'using' in config['difference']:
        return True
    if 'union' in config and 'using' in config['union']:
        return True
    if 'exists_in' in config and 'using' in config['exists_in']:
        return True
    if 'not_exists_in' in config and 'using' in config['not_exists_in']:
        return True
    return False

# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_structure_references(config: dict, registry=None) -> List[str]:
    """Validate that structure references are correct"""
    errors = []
    
    if not registry:
        return errors
    
    # Check join operations
    if 'join' in config and 'using' in config['join']:
        structure_name = config['join']['using']
        if not registry.exists(structure_name):
            errors.append(f"Join references unknown structure: {structure_name}")
        else:
            structure = registry.get(structure_name)
            if structure.to_dict()['type'] != 'hashmap':
                errors.append(f"Join requires hashmap, but {structure_name} is {structure.to_dict()['type']}")
            elif 'on' in config['join']:
                expected_key = structure.key_field if hasattr(structure, 'key_field') else None
                if expected_key and config['join']['on'] != expected_key:
                    errors.append(f"Join key mismatch: using '{config['join']['on']}' but structure expects '{expected_key}'")
    
    # Check set operations
    for op in ['difference', 'union', 'exists_in', 'not_exists_in']:
        if op in config and 'using' in config[op]:
            structure_name = config[op]['using']
            if not registry.exists(structure_name):
                errors.append(f"{op} references unknown structure: {structure_name}")
            else:
                structure = registry.get(structure_name)
                if structure.to_dict()['type'] != 'set':
                    errors.append(f"{op} requires set, but {structure_name} is {structure.to_dict()['type']}")
    
    return errors

# ============================================================================
# UNIFIED JOIN HANDLING
# ============================================================================

def resolve_join_config(join_config: dict, registry=None):
    """Resolve join configuration supporting both 'with' and 'using' patterns"""
    if 'using' in join_config:
        # Structure-backed join
        if not registry:
            raise ValueError("Join with 'using' requires structure registry")
        
        structure_name = join_config['using']
        if not registry.exists(structure_name):
            raise ValueError(f"Structure not found: {structure_name}")
        
        structure = registry.get(structure_name)
        if structure.to_dict()['type'] != 'hashmap':
            raise ValueError(f"Join requires hashmap structure, got {structure.to_dict()['type']}")
        
        return {
            'type': 'structure_join',
            'structure': structure,
            'on_field': join_config['on'],
            'join_type': join_config.get('type', 'inner')
        }
    
    elif 'with' in join_config:
        # Inline data join
        return {
            'type': 'inline_join',
            'right_data': join_config['with'],
            'on_field': join_config['on'],
            'join_type': join_config.get('type', 'inner')
        }
    
    else:
        raise ValueError("Join requires either 'with' (inline data) or 'using' (structure)")

# ============================================================================
# CLI HELPERS
# ============================================================================

def print_audit_summary(audit: dict, component_name: str = ""):
    """Print standardized audit summary across all components"""
    print(f"\nAudit Summary{' - ' + component_name if component_name else ''}:")
    print(f"  Config Hash: {audit.get('pipeline_hash', audit.get('rules_hash', audit.get('config_hash', 'N/A')))[:16]}...")
    print(f"  Input Hash:  {audit.get('input_hash', 'N/A')[:16]}...")
    print(f"  Output Hash: {audit.get('output_hash', 'N/A')[:16]}...")
    
    if 'structures_used' in audit:
        print(f"  Structures:  {len(audit['structures_used'])} used - {audit['structures_used']}")
    
    if 'ra_audit' in audit:
        print(f"  RA Ops:      {audit['ra_audit'].get('operations_count', 0)} applied")
    
    if 'execution_log' in audit:
        print(f"  Effects:     {len(audit.get('execution_log', []))} executed")

def get_timestamp():
    """Get current ISO timestamp"""
    from datetime import datetime
    return datetime.now().isoformat()

# ============================================================================
# DEMO
# ============================================================================

if __name__ == "__main__":
    print("AXIS-CORE: Shared primitives and helpers")
    print("Eliminates duplication across AXIS components\n")
    
    # Test canonicalization
    test_data = {"b": [3, 1, 2], "a": {"z": 1, "x": 2}}
    canonical = canonicalize(test_data)
    hash_val = generate_content_hash(test_data)
    
    print(f"Original:   {test_data}")
    print(f"Canonical:  {canonical}")
    print(f"Hash:       {hash_val[:16]}...")
    
    # Test AST evaluation
    context = {"age": 25, "role": "admin", "user": {"name": "Alice"}}
    
    test_expressions = [
        "age >= 18",
        "role == 'admin'",
        "user.name == 'Alice'",
        "age >= 18 and role == 'admin'"
    ]
    
    print(f"\nAST Evaluation Tests:")
    print(f"Context: {context}")
    
    for expr in test_expressions:
        try:
            ast_node = parse_condition_to_ast(expr)
            result = evaluate_ast(ast_node, context)
            print(f"  '{expr}' → {result}")
        except Exception as e:
            print(f"  '{expr}' → ERROR: {e}")
    
    print(f"\nUsage: Import this module to avoid duplication")
    print(f"  from axis_core import canonicalize, sha3_256_hex, parse_condition_to_ast")
