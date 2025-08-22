#!/usr/bin/env python3
"""
AXIS-RULES: β-reduction for JSON  
Pure decision logic and state transformations

Pipeline: JSON → Logic → New JSON
- If/then conditional logic
- Pure state transformations
- Deterministic rule application
- Cryptographic verification

Usage:
    echo '{"age": 25, "role": "admin"}' | python axis_rules.py apply logic.yaml
"""

import json
import sys
import argparse
import hashlib
import math
import ast
import os
from typing import Any, Dict, List, Union

# Optional YAML support
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

# ============================================================================
# CANONICALIZATION & HASHING (from AXIS core)
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
    """Content addressing for rule verification"""
    return hashlib.sha3_256(s.encode("utf-8")).hexdigest()

# ============================================================================
# SECURE AST PARSER (from AXIS core)
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

# ============================================================================
# RULE ENGINE (β-reduction)
# ============================================================================

class RuleEngine:
    """Apply pure logic rules to JSON state"""
    
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
        self.rules_hash = self._generate_rules_hash()
    
    def _generate_rules_hash(self) -> str:
        """Generate hash of rules configuration"""
        canonical_rules = canonicalize({
            'component': self.component_name,
            'rules': self.rules,
            'version': 'axis-rules@1.0.0'
        })
        rules_json = json.dumps(canonical_rules, sort_keys=True, separators=(',', ':'))
        return sha3_256_hex(rules_json)
    
    def apply(self, input_data: dict) -> dict:
        """Apply rules with fixpoint iteration, priority resolution, and conflict logging."""
        # Deep copy to avoid mutating original
        new_state = json.loads(json.dumps(input_data))

        # Ensure error/computed fields exist
        new_state.setdefault('computed', {})
        new_state.setdefault('errors', [])

        iteration = 0
        max_iterations = 50
        changed = True
        total_changes = []
        conflicts = []

        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            context = dict(new_state)
            pending_changes = []

            for i, rule in enumerate(self.rules):
                should_apply = True

                # Evaluate condition
                if 'if' in rule:
                    try:
                        condition_ast = parse_condition_to_ast(rule['if'])
                        should_apply = evaluate_ast(condition_ast, context)
                    except Exception as e:
                        if os.getenv('AXIS_DEBUG'):
                            print(f"Rule {i} condition failed: {e}", file=sys.stderr)
                        should_apply = False

                # Select branch
                target_branch = 'then' if should_apply else 'else'
                if target_branch in rule:
                    changes = rule[target_branch]
                    if isinstance(changes, dict):
                        for key, value in changes.items():
                            merge_policy = 'replace'
                            clean_key = key
                            if key.endswith('+'):
                                merge_policy = 'append'
                                clean_key = key[:-1]

                            priority = rule.get('priority', 0)

                            pending_changes.append({
                                'key': clean_key,
                                'value': value,
                                'merge_policy': merge_policy,
                                'order': i,
                                'priority': priority,
                                'rule_index': i
                            })

            # Sort by priority, then order, then key
            pending_changes.sort(key=lambda x: (-x['priority'], x['order'], x['key']))

            for change in pending_changes:
                key = change['key']
                value = change['value']
                merge_policy = change['merge_policy']
                priority = change['priority']
                rule_index = change['rule_index']

                old_value = new_state.get(key)

                if merge_policy == 'append':
                    if not isinstance(new_state.get(key), list):
                        new_state[key] = []
                    if isinstance(value, list):
                        for v in value:
                            if v not in new_state[key]:
                                new_state[key].append(v)
                                changed = True
                    else:
                        if value not in new_state[key]:
                            new_state[key].append(value)
                            changed = True

                else:  # replace (default)
                    if old_value is None:
                        new_state[key] = value
                        changed = True
                    elif old_value != value:
                        # Conflict: different value already set
                        conflicts.append({
                            "field": key,
                            "old": old_value,
                            "new": value,
                            "priority": priority,
                            "rule": rule_index
                        })
                        # Only overwrite if new rule has strictly higher priority
                        # Otherwise, keep old value
                        prev_priority = 0
                        for c in total_changes:
                            if c['key'] == key:
                                prev_priority = c['priority']
                        if priority > prev_priority:
                            new_state[key] = value
                            changed = True

                total_changes.append(change)

        if iteration >= max_iterations:
            new_state.setdefault('errors', []).append(
                "RuleEngine: max iterations reached (possible loop)"
            )

        # Add conflict logs to errors
        for conflict in conflicts:
            new_state.setdefault('errors', []).append(
                f"Conflict on '{conflict['field']}': {conflict['old']} → {conflict['new']} (rule {conflict['rule']}, priority {conflict['priority']})"
            )

        # Add audit info
        audit = {
            'rules_hash': self.rules_hash,
            'input_hash': sha3_256_hex(json.dumps(canonicalize(input_data), sort_keys=True)),
            'output_hash': sha3_256_hex(json.dumps(canonicalize(new_state), sort_keys=True)),
            'rules_applied': len(total_changes),
            'iterations': iteration,
            'conflicts': len(conflicts)
        }

        return {**new_state, '_rule_audit': audit}
           
    def _apply_change(self, state: dict, change: dict):
        """Apply a single state change"""
        key = change['key']
        value = change['value']
        merge_policy = change['merge_policy']
        
        if merge_policy == 'append' and isinstance(state.get(key), list):
            if isinstance(value, list):
                state[key].extend(value)
            else:
                state[key].append(value)
        else:  # replace (default)
            state[key] = value

# ============================================================================
# CLI INTERFACE
# ============================================================================

def cli():
    """CLI for AXIS-RULES"""
    parser = argparse.ArgumentParser(description="AXIS-RULES: Pure decision logic")
    parser.add_argument("command", choices=['apply', 'validate', 'hash'], help="Command to execute")
    parser.add_argument("config", help="Rules configuration file")
    parser.add_argument("--input", help="Input JSON file (default: stdin)")
    parser.add_argument("--output", help="Output file (default: stdout)")
    
    args = parser.parse_args()
    
    try:
        if args.command == 'apply':
            # Load input data
            if args.input:
                with open(args.input, 'r') as f:
                    input_data = json.load(f)
            else:
                input_data = json.load(sys.stdin)
            
            # Apply rules
            engine = RuleEngine(args.config)
            result = engine.apply(input_data)
            
            # Output result
            output = json.dumps(result, indent=2)
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
            else:
                print(output)
        
        elif args.command == 'validate':
            engine = RuleEngine(args.config)
            print(f"✓ Rules valid: {engine.component_name}")
            print(f"✓ Rule count: {len(engine.rules)}")
            print(f"✓ Rules Hash: {engine.rules_hash}")
        
        elif args.command == 'hash':
            engine = RuleEngine(args.config)
            print(engine.rules_hash)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

# ============================================================================
# DEMO & EXAMPLES
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli()
    else:
        print("⚖️ AXIS-RULES: β-reduction for JSON")
        print("Pure decision logic and state transformations\n")
        
        # Demo rules
        sample_data = {"age": 25, "role": "admin", "active": True}
        sample_config = {
            "component": "UserAccess",
            "rules": [
                {"if": "age >= 18", "then": {"status": "adult", "can_vote": True}},
                {"if": "role == 'admin'", "then": {"permissions": ["read", "write", "admin"]}},
                {"if": "not active", "then": {"errors+": ["Account disabled"]}}
            ]
        }
        
        engine = RuleEngine(sample_config)
        result = engine.apply(sample_data)
        clean_result = {k: v for k, v in result.items() if k != '_rule_audit'}
        
        print(f"Input:  {sample_data}")
        print(f"Output: {clean_result}")
        print(f"Hash:   {result['_rule_audit']['rules_hash'][:16]}...")
        
        print(f"\nUsage:")
        print(f"  echo '{json.dumps(sample_data)}' | python axis_rules.py apply config.yaml")
        print(f"  python axis_rules.py validate config.yaml")
        print(f"  python axis_rules.py hash config.yaml")
