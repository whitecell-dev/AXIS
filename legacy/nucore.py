#!/usr/bin/env python3
"""
AXIS: React for Deterministic Reasoning
Zero-boilerplate Python library for hash-verified, cross-platform logic

Pipeline: YAML → AST → Pure Reducer → Cryptographic Audit
- Canonical IR with SHA3-256 hashing  
- Security-first AST validation
- Cross-platform determinism (Python ↔ JS ↔ WASM)
- Zero framework dependencies

"We split the atom of software complexity and found that simplicity was the most powerful force inside."
"""

import json
import math
import hashlib
import os
import sys
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Optional imports
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    requests = None

# ============================================================================
# AST PARSER (INLINED - NO EXTERNAL DEPENDENCIES)
# ============================================================================

def parse_condition_to_ast(condition: str) -> dict:
    """
    Parse simple boolean condition string to a very restricted AST
    Supports: ==, !=, >, <, >=, <=, and, or, not, in, not in
    """
    import ast
    
    def _convert(node):
        if isinstance(node, ast.BoolOp):
            return {
                'type': 'logical',
                'op': node.op.__class__.__name__.lower(),
                'values': [_convert(v) for v in node.values]
            }
        elif isinstance(node, ast.BinOp):
            raise ValueError("Binary arithmetic not allowed")
        elif isinstance(node, ast.Compare):
            left = _convert(node.left)
            comparators = [_convert(c) for c in node.comparators]
            if len(node.ops) != 1:
                raise ValueError("Only single comparisons supported")
            op = node.ops[0].__class__.__name__
            return {
                'type': 'binary_op',
                'op': op.lower(),
                'left': left,
                'right': comparators[0]
            }
        elif isinstance(node, ast.UnaryOp):
            return {
                'type': 'unary_op',
                'op': node.op.__class__.__name__.lower(),
                'operand': _convert(node.operand)
            }
        elif isinstance(node, ast.Name):
            return {'type': 'var', 'name': node.id}
        elif isinstance(node, ast.Constant):
            return {'type': 'literal', 'value': node.value}
        elif isinstance(node, ast.Attribute):
            # Handle dot notation like user.role
            return {'type': 'var', 'name': _get_full_name(node)}
        else:
            raise ValueError(f"Unsupported node: {ast.dump(node)}")
    
    def _get_full_name(node):
        """Convert ast.Attribute to dot notation string"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{_get_full_name(node.value)}.{node.attr}"
        else:
            raise ValueError(f"Unsupported attribute node: {ast.dump(node)}")
    
    try:
        parsed = ast.parse(condition, mode='eval')
        return _convert(parsed.body)
    except Exception as e:
        raise ValueError(f"Failed to parse condition '{condition}': {e}")

def evaluate_ast(ast_node: dict, context: dict) -> Any:
    """Evaluate the restricted AST against the given context"""
    if ast_node['type'] == 'var':
        # Handle dot notation (user.role)
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
    
    elif ast_node['type'] == 'literal':
        return ast_node['value']
    
    elif ast_node['type'] == 'binary_op':
        left = evaluate_ast(ast_node['left'], context)
        right = evaluate_ast(ast_node['right'], context)
        op = ast_node['op']
        
        # Handle comparison operators
        if op == 'eq':
            return left == right
        elif op == 'noteq':
            return left != right
        elif op == 'gt':
            return left > right
        elif op == 'lt':
            return left < right
        elif op == 'gte':
            return left >= right
        elif op == 'lte':
            return left <= right
        elif op == 'in':
            return left in right
        elif op == 'notin':
            return left not in right
        else:
            return False
    
    elif ast_node['type'] == 'unary_op':
        operand = evaluate_ast(ast_node['operand'], context)
        if ast_node['op'] == 'not':
            return not operand
        return operand
    
    elif ast_node['type'] == 'logical':
        values = [evaluate_ast(v, context) for v in ast_node['values']]
        if ast_node['op'] == 'and':
            return all(values)
        elif ast_node['op'] == 'or':
            return any(values)
        else:
            return False
    
    return False

# ============================================================================
# DETERMINISM CORE - CRYPTOGRAPHIC VERIFICATION
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
    """Content addressing for IR"""
    return hashlib.sha3_256(s.encode("utf-8")).hexdigest()

# ============================================================================
# PURE REDUCER ENGINE (REACT-INSPIRED)
# ============================================================================

def apply_rules(rules: List[dict], state: dict, action: dict) -> dict:
    """
    Apply rules deterministically - inspired by React's reducer pattern
    
    Two-phase execution:
    1. Collect all state changes from matching rules
    2. Apply changes in deterministic order
    """
    # Deep copy to avoid mutations (like React's immutability)
    new_state = json.loads(json.dumps(state))
    context = dict(new_state)
    context.update(action)  # Action data available in conditions
    
    # Clear computed state on each reduction
    new_state.setdefault('computed', {}).clear()
    new_state.setdefault('errors', []).clear()
    
    pending_changes = []
    
    for i, rule in enumerate(rules):
        # Evaluate condition (if present)
        should_apply = True
        if 'if' in rule:
            try:
                condition_ast = parse_condition_to_ast(rule['if'])
                should_apply = evaluate_ast(condition_ast, context)
            except Exception as e:
                if os.getenv('AXIS_DEBUG'):
                    print(f"Rule {i} condition failed: {e}", file=sys.stderr)
                should_apply = False
        
        # Select then/else branch
        target_branch = 'then' if should_apply else 'else'
        if target_branch in rule:
            changes = rule[target_branch]
            if isinstance(changes, dict):
                for key, value in changes.items():
                    # Handle merge policies (like errors+)
                    merge_policy = 'replace'
                    clean_key = key
                    
                    if key.endswith('+'):
                        merge_policy = 'append'
                        clean_key = key[:-1]
                    
                    pending_changes.append({
                        'key': clean_key,
                        'value': value,
                        'merge_policy': merge_policy,
                        'order': i  # Deterministic ordering
                    })
    
    # Apply changes in deterministic order
    pending_changes.sort(key=lambda x: (x['order'], x['key']))
    
    for change in pending_changes:
        key = change['key']
        value = change['value']
        merge_policy = change['merge_policy']
        
        if merge_policy == 'append' and isinstance(new_state.get(key), list):
            if isinstance(value, list):
                new_state[key].extend(value)
            else:
                new_state[key].append(value)
        else:  # replace (default)
            new_state[key] = value
    
    return new_state

# ============================================================================
# RULE ENGINE - THE "REACT COMPONENT" FOR LOGIC
# ============================================================================

class RuleEngine:
    """
    YAML-based rule engine - like a React component for business logic
    """
    
    def __init__(self, rules: Union[dict, str, List[dict]]):
        """Initialize with rules dict, YAML file path, or list of rules"""
        
        if isinstance(rules, str):
            # Load from YAML file
            if not HAS_YAML:
                raise RuntimeError("YAML support requires: pip install pyyaml")
            with open(rules, 'r') as f:
                self.rules_data = yaml.safe_load(f)
        elif isinstance(rules, dict):
            self.rules_data = rules
        elif isinstance(rules, list):
            self.rules_data = {'rules': rules}
        else:
            raise ValueError("Rules must be dict, list, or YAML file path")
        
        # Extract rules list
        if 'rules' in self.rules_data:
            self.rules = self.rules_data['rules']
        elif isinstance(self.rules_data, list):
            self.rules = self.rules_data
        else:
            raise ValueError("Rules must contain 'rules' key or be a list")
        
        # Store metadata
        self.component_name = self.rules_data.get('component', 'anonymous')
        self.initial_state = self.rules_data.get('initial_state', {})
        
        # Generate IR hash for verification
        self.ir_hash = self._generate_ir_hash()
    
    def _generate_ir_hash(self) -> str:
        """Generate cryptographic hash of the canonical rules"""
        canonical_rules = canonicalize({
            'component': self.component_name,
            'rules': self.rules,
            'compiler_version': 'AXIS-atomic@1.0.0'
        })
        ir_json = json.dumps(canonical_rules, sort_keys=True, separators=(',', ':'))
        return sha3_256_hex(ir_json)
    
    def run(self, input_data: dict, action: dict = None) -> dict:
        """
        Execute rules against input data - like calling a React component
        
        Returns: new state with audit trail
        """
        if action is None:
            action = {'type': 'RULE_CHECK'}
        
        # Apply rules to get new state
        new_state = apply_rules(self.rules, input_data, action)
        
        # Add audit trail
        audit_entry = {
            'ir_hash': self.ir_hash,
            'input_hash': sha3_256_hex(json.dumps(canonicalize(input_data), sort_keys=True)),
            'output_hash': sha3_256_hex(json.dumps(canonicalize(new_state), sort_keys=True)),
            'action': action,
            'timestamp': None  # Could add time if needed
        }
        
        # Include audit in response (non-mutating)
        return {
            **new_state,
            '_audit': audit_entry
        }
    
    def create_reducer(self):
        """
        Create a Redux-style reducer function
        
        Returns: (state, action) -> new_state
        """
        def reducer(state: dict, action: dict) -> dict:
            return self.run(state, action)
        
        return reducer

# ============================================================================
# VALIDATION & UTILITIES
# ============================================================================

def validate(data: dict, schema: Union[dict, str]) -> Tuple[bool, List[str]]:
    """
    Validate data against schema (dict or YAML path)
    
    Schema format: {"name": "str", "age": "int", "email": "str?"}
    Returns: (is_valid, list_of_errors)
    """
    # Load schema from YAML if path provided
    if isinstance(schema, str):
        if not HAS_YAML:
            return False, ["YAML support requires: pip install pyyaml"]
        try:
            with open(schema, 'r') as f:
                schema = yaml.safe_load(f)
        except Exception as e:
            return False, [f"Failed to load schema: {e}"]
    
    errors = []
    
    # Validate each field
    for field, type_spec in schema.items():
        # Handle optional fields (ending with ?)
        is_optional = type_spec.endswith('?')
        if is_optional:
            type_spec = type_spec[:-1]
        
        # Check if field exists
        if field not in data:
            if not is_optional:
                errors.append(f"Missing required field: {field}")
            continue
        
        value = data[field]
        
        # Type checking and coercion
        if type_spec == "str":
            if not isinstance(value, str):
                try:
                    data[field] = str(value)
                except Exception:
                    errors.append(f"{field}: expected str, got {type(value).__name__}")
        
        elif type_spec == "int":
            if not isinstance(value, int):
                try:
                    data[field] = int(value)
                except Exception:
                    errors.append(f"{field}: expected int, got {type(value).__name__}")
        
        elif type_spec == "float":
            if not isinstance(value, (int, float)):
                try:
                    data[field] = float(value)
                except Exception:
                    errors.append(f"{field}: expected float, got {type(value).__name__}")
        
        elif type_spec == "bool":
            if not isinstance(value, bool):
                # Coerce common bool representations
                if isinstance(value, str):
                    if value.lower() in ('true', '1', 'yes', 'on'):
                        data[field] = True
                    elif value.lower() in ('false', '0', 'no', 'off'):
                        data[field] = False
                    else:
                        errors.append(f"{field}: expected bool, got {value}")
                else:
                    errors.append(f"{field}: expected bool, got {type(value).__name__}")
        
        else:
            errors.append(f"{field}: unknown type {type_spec}")
    
    return len(errors) == 0, errors

def typecheck(schema: dict):
    """Decorator that validates function arguments against schema"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(data: dict, *args, **kwargs):
            is_valid, errors = validate(data, schema)
            if not is_valid:
                raise TypeError(f"Validation failed: {'; '.join(errors)}")
            return func(data, *args, **kwargs)
        return wrapper
    return decorator

# ============================================================================
# CLI INTERFACE
# ============================================================================

def cli():
    """Simple CLI for running AXIS rules"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AXIS: React for Deterministic Reasoning")
    parser.add_argument("command", choices=['run', 'validate', 'hash'], help="Command to execute")
    parser.add_argument("rules", help="Path to YAML rules file")
    parser.add_argument("input", nargs='?', help="JSON input as string or @file.json")
    parser.add_argument("--output", help="Output file for results")
    
    args = parser.parse_args()
    
    try:
        if args.command == 'run':
            if not args.input:
                print("Error: input required for 'run' command", file=sys.stderr)
                sys.exit(1)
            
            # Load input
            if args.input.startswith("@"):
                with open(args.input[1:], 'r') as f:
                    input_data = json.load(f)
            else:
                input_data = json.loads(args.input)
            
            # Run rules
            engine = RuleEngine(args.rules)
            result = engine.run(input_data)
            
            # Output result
            output = json.dumps(result, indent=2)
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
                print(f"Result written to {args.output}")
            else:
                print(output)
        
        elif args.command == 'validate':
            # Just validate that rules can be loaded
            engine = RuleEngine(args.rules)
            print(f"✓ Rules valid: {engine.component_name}")
            print(f"✓ Rule count: {len(engine.rules)}")
            print(f"✓ IR Hash: {engine.ir_hash}")
        
        elif args.command == 'hash':
            # Show the IR hash
            engine = RuleEngine(args.rules)
            print(engine.ir_hash)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
# ============================================================================
# CLI EXTENSIONS
# ============================================================================

def extended_cli():
    """Extended CLI with all new features"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="AXIS Complete Ecosystem")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Original commands
    run_parser = subparsers.add_parser('run', help='Run rules')
    run_parser.add_argument('rules', help='Rules file')
    run_parser.add_argument('input', help='Input JSON')
    
    # New commands
    compose_parser = subparsers.add_parser('compose', help='Compose rules from includes')
    compose_parser.add_argument('main_file', help='Main YAML file with includes')
    compose_parser.add_argument('--output', help='Output composed rules to file')
    
    test_parser = subparsers.add_parser('test', help='Run golden vector tests')
    test_parser.add_argument('rules', help='Rules file')
    test_parser.add_argument('vectors', help='Test vectors file')
    
    generate_parser = subparsers.add_parser('generate', help='Generate integrations')
    generate_parser.add_argument('type', choices=['react', 'flask', 'fastapi'])
    generate_parser.add_argument('rules', help='Rules file')
    generate_parser.add_argument('--output', help='Output file')
    
    args = parser.parse_args()
    
    if args.command == 'compose':
        composer = RuleComposer()
        composed = composer.compose_rules(args.main_file)
        
        if args.output:
            import yaml
            with open(args.output, 'w') as f:
                yaml.dump(composed, f, indent=2)
        else:
            import yaml
            print(yaml.dump(composed, indent=2))
    
    elif args.command == 'test':
        runner = GoldenVectorRunner(args.rules)
        results = runner.run_tests(args.vectors)
        
        print(f"Tests: {results['total']}")
        print(f"Passed: {results['passed']}")
        print(f"Failed: {results['failed']}")
        
        if results['failures']:
            print("\nFailures:")
            for failure in results['failures']:
                print(f"  - {failure}")
    
    elif args.command == 'generate':
        if args.type == 'react':
            hook_code = generate_react_hook(args.rules)
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(hook_code)
            else:
                print(hook_code) 
# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def load_rules(path: str) -> RuleEngine:
    """Load rules from YAML file"""
    return RuleEngine(path)

def quick_validate(data: dict, **types) -> dict:
    """Quick validation with keyword arguments"""
    is_valid, errors = validate(data, types)
    if not is_valid:
        raise ValueError(f"Validation failed: {'; '.join(errors)}")
    return data

# ============================================================================
# DEMO & TESTING
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli()
        extended_cli()

    else:
        # Demo mode
        print("AXIS: React for Deterministic Reasoning\n")
        
        # Example 1: Simple validation
        print("1. Validation Example:")
        data = {"name": "Alice", "age": "25"}
        is_valid, errors = validate(data, {"name": "str", "age": "int"})
        print(f"   Valid: {is_valid}, Data: {data}\n")
        
        # Example 2: Rule engine
        print("2. Rule Engine Example:")
        rules = {
            "component": "UserAccess",
            "rules": [
                {"if": "age >= 18", "then": {"status": "adult", "can_vote": True}},
                {"if": "age < 18", "then": {"status": "minor", "can_vote": False}},
                {"if": "not email", "then": {"errors+": ["Email required"]}}
            ]
        }
        
        engine = RuleEngine(rules)
        result = engine.run({"age": 25, "email": "alice@example.com"})
        
        print(f"   Input: age=25, email=alice@example.com")
        print(f"   Output: {json.dumps({k: v for k, v in result.items() if k != '_audit'}, indent=4)}")
        print(f"   IR Hash: {result['_audit']['ir_hash'][:16]}...")
        
        print(f"\n3. Available CLI commands:")
        print(f"   AXIS run rules.yaml '{{\"age\": 17}}'")
        print(f"   AXIS validate rules.yaml")
        print(f"   AXIS hash rules.yaml")
        
        print(f"\nReact for Deterministic Reasoning is ready! ")
