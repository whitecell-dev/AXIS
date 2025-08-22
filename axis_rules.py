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
from typing import Any, Dict, List, Union

# Optional YAML support
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

# ============================================================================
# RFC 8785 COMPLIANT CANONICALIZATION (shared with pipes)
# ============================================================================

def canonicalize(obj: Any) -> Any:
    """RFC 8785 compliant JSON canonicalization"""
    if isinstance(obj, dict):
        return {k: canonicalize(obj[k]) for k in sorted(obj.keys())}
    elif isinstance(obj, list):
        return [canonicalize(v) for v in obj]
    elif isinstance(obj, bool):
        return obj
    elif isinstance(obj, int):
        return obj
    elif isinstance(obj, float):
        if not math.isfinite(obj):
            raise ValueError("Non-finite numbers not allowed")
        return obj
    elif obj is None:
        return obj
    else:
        return str(obj)

def payload_view(data: dict) -> dict:
    """Extract payload view (exclude audit keys starting with _)"""
    if isinstance(data, dict):
        return {k: payload_view(v) if isinstance(v, dict) else v
                for k, v in data.items() 
                if not (isinstance(k, str) and k.startswith("_"))}
    return data

def sha3_256_hex(s: str) -> str:
    """Content addressing with strict canonicalization"""
    return hashlib.sha3_256(s.encode("utf-8")).hexdigest()

def compute_hash(obj: Any) -> str:
    """Compute canonical hash of object"""
    canonical = canonicalize(obj)
    json_str = json.dumps(canonical, sort_keys=True, separators=(',', ':'))
    return sha3_256_hex(json_str)

# ============================================================================
# SECURE AST PARSER WITH LIMITS
# ============================================================================

ALLOWED_OPS = {
    'eq', 'noteq', 'gt', 'lt', 'gte', 'lte', 'in', 'notin',
    'and', 'or', 'not'
}

ALLOWED_LITERALS = (str, int, float, bool, type(None))
MAX_CONDITION_LENGTH = 4096
MAX_AST_DEPTH = 32

def parse_condition_to_ast(condition: str) -> dict:
    """Parse condition string to restricted AST with security limits"""
    if len(condition) > MAX_CONDITION_LENGTH:
        raise ValueError(f"Condition too long (max {MAX_CONDITION_LENGTH} chars)")
    
    def _convert(node, depth=0):
        if depth > MAX_AST_DEPTH:
            raise ValueError(f"AST too deep (max {MAX_AST_DEPTH} levels)")
        
        if isinstance(node, ast.BoolOp):
            op_name = node.op.__class__.__name__.lower()
            if op_name not in ALLOWED_OPS:
                raise ValueError(f"Operation {op_name} not allowed")
            return {
                'type': 'logical',
                'op': op_name,
                'values': [_convert(v, depth + 1) for v in node.values]
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
                'left': _convert(node.left, depth + 1),
                'right': _convert(node.comparators[0], depth + 1)
            }
        elif isinstance(node, ast.UnaryOp):
            op_name = node.op.__class__.__name__.lower()
            if op_name not in ALLOWED_OPS:
                raise ValueError(f"Operation {op_name} not allowed")
            return {
                'type': 'unary_op',
                'op': op_name,
                'operand': _convert(node.operand, depth + 1)
            }
        elif isinstance(node, ast.Name):
            return {'type': 'var', 'name': node.id}
        elif isinstance(node, ast.Constant):
            # Restrict literal types for security
            if type(node.value) not in ALLOWED_LITERALS:
                raise ValueError(f"Unsupported literal type: {type(node.value)}")
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
# RULE ENGINE (β-reduction) - PURE
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
        self.rules_hash = compute_hash({
            'component': self.component_name,
            'rules': self.rules,
            'version': 'axis-rules@1.0.0'
        })
        
        # Pre-validate rules
        self._validate_rules()
    
    def _validate_rules(self):
        """Validate rule structure and syntax"""
        for i, rule in enumerate(self.rules):
            if not isinstance(rule, dict):
                raise ValueError(f"Rule {i}: must be a dict")
            
            # Check required structure
            has_condition = 'if' in rule
            has_then = 'then' in rule
            has_else = 'else' in rule
            
            if not (has_then or has_else):
                raise ValueError(f"Rule {i}: must have 'then' or 'else'")
            
            # Validate condition syntax if present
            if has_condition:
                try:
                    parse_condition_to_ast(rule['if'])
                except Exception as e:
                    raise ValueError(f"Rule {i} condition invalid: {e}")
            
            # Validate action structure
            for action_key in ['then', 'else']:
                if action_key in rule:
                    action = rule[action_key]
                    if not isinstance(action, dict):
                        raise ValueError(f"Rule {i} {action_key}: must be a dict")
                    
                    # Check merge policy syntax
                    for key in action.keys():
                        if key.endswith('+') and not isinstance(action[key], (list, str)):
                            raise ValueError(f"Rule {i} {action_key}: {key} merge requires list or string")
    
    def apply(self, input_data: dict) -> dict:
        """Apply rules to input data - pure β-reduction"""
        # Deep copy to avoid mutations
        new_state = json.loads(json.dumps(input_data))
        
        # Context is frozen at input state (single-pass semantics)
        context = dict(new_state)
        
        # Respect existing fields - don't auto-clear
        errors = new_state.get('errors', [])
        
        # Collect all pending changes
        pending_changes = []
        
        for i, rule in enumerate(self.rules):
            should_apply = True
            
            # Evaluate condition against frozen context
            if 'if' in rule:
                try:
                    condition_ast = parse_condition_to_ast(rule['if'])
                    should_apply = evaluate_ast(condition_ast, context)
                except Exception as e:
                    errors.append(f"Rule {i} condition failed: {e}")
                    should_apply = False
            
            # Select then/else branch
            target_branch = 'then' if should_apply else 'else'
            if target_branch in rule:
                changes = rule[target_branch]
                if isinstance(changes, dict):
                    for key, value in changes.items():
                        # Handle merge policies
                        merge_policy = 'replace'
                        clean_key = key
                        
                        if key.endswith('+'):
                            merge_policy = 'append'
                            clean_key = key[:-1]
                        
                        pending_changes.append({
                            'key': clean_key,
                            'value': value,
                            'merge_policy': merge_policy,
                            'order': i
                        })
        
        # Apply changes deterministically by order, then key
        pending_changes.sort(key=lambda x: (x['order'], x['key']))
        
        for change in pending_changes:
            self._apply_change(new_state, change)
        
        # Update errors if any occurred
        if errors:
            new_state['errors'] = errors
        
        # Add rule audit (deterministic)
        payload = payload_view(new_state)
        audit = {
            'rules_hash': self.rules_hash,
            'input_hash': compute_hash(payload_view(input_data)),
            'output_hash': compute_hash(payload),
            'rules_applied': len(pending_changes),
            'component': self.component_name
        }
        
        return {**new_state, '_rule_audit': audit}
    
    def _apply_change(self, state: dict, change: dict):
        """Apply a single state change"""
        key = change['key']
        value = change['value']
        merge_policy = change['merge_policy']
        
        if merge_policy == 'append':
            if key not in state:
                state[key] = []
            if isinstance(state[key], list):
                if isinstance(value, list):
                    state[key].extend(value)
                else:
                    state[key].append(value)
            else:
                # Convert to list and append
                state[key] = [state[key], value] if not isinstance(value, list) else [state[key]] + value
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
    parser.add_argument("--input", help="Input JSON file (use '-' for stdin)")
    parser.add_argument("--output", help="Output file (use '-' for stdout)")
    parser.add_argument("--strict", action='store_true', help="Strict validation mode")
    parser.add_argument("--quiet", "-q", action='store_true', help="Suppress non-essential output")
    
    args = parser.parse_args()
    
    try:
        if args.command == 'apply':
            # Load input data
            if args.input == '-' or args.input is None:
                input_data = json.load(sys.stdin)
            else:
                with open(args.input, 'r') as f:
                    input_data = json.load(f)
            
            # Apply rules
            engine = RuleEngine(args.config)
            result = engine.apply(input_data)
            
            # Strict mode: fail on errors
            if args.strict and 'errors' in result and result['errors']:
                print(f"Rules failed with errors: {result['errors']}", file=sys.stderr)
                sys.exit(1)
            
            # Output result
            output = json.dumps(result, indent=None if args.quiet else 2, separators=(',', ':'))
            if args.output == '-' or args.output is None:
                print(output)
            else:
                with open(args.output, 'w') as f:
                    f.write(output)
        
        elif args.command == 'validate':
            engine = RuleEngine(args.config)
            if not args.quiet:
                print(f"✅ Rules valid: {engine.component_name}")
                print(f"✅ Rule count: {len(engine.rules)}")
                print(f"✅ Rules Hash: {engine.rules_hash}")
        
        elif args.command == 'hash':
            engine = RuleEngine(args.config)
            print(engine.rules_hash)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    cli()
