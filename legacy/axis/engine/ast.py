#!/usr/bin/env python3
"""
Secure AST parser for rule conditions
Only allows whitelisted operations for security
"""

import ast
from typing import Any, Dict

# Security whitelist - only these operations allowed
ALLOWED_OPS = {
    'eq', 'noteq', 'gt', 'lt', 'gte', 'lte', 'in', 'notin',
    'and', 'or', 'not'
}

def parse_condition_to_ast(condition: str) -> dict:
    """
    Parse condition string to restricted AST
    Only supports: ==, !=, >, <, >=, <=, and, or, not, in, not in
    """
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
            raise ValueError(f"Unsupported attribute node")
    
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
            # Handle dot notation (user.role)
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
