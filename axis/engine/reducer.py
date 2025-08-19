#!/usr/bin/env python3
"""
Pure reducer function - React-inspired state transitions
Two-phase execution for deterministic results
"""

import json
import os
import sys
from typing import Dict, List, Any
from .ast import parse_condition_to_ast, evaluate_ast

def apply_rules(rules: List[dict], state: dict, action: dict) -> dict:
    """
    Apply rules deterministically - React reducer pattern
    
    Two-phase execution:
    1. Collect all state changes from matching rules
    2. Apply changes in deterministic order (last write wins)
    """
    # Deep copy to avoid mutations (React immutability)
    new_state = json.loads(json.dumps(state))
    context = dict(new_state)
    context.update(action)  # Action data available in conditions
    
    # Clear computed state on each reduction
    new_state.setdefault('computed', {}).clear()
    new_state.setdefault('errors', []).clear()
    
    # Phase 1: Collect all pending changes
    pending_changes = []
    
    for i, rule in enumerate(rules):
        # Evaluate condition if present
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
    
    # Phase 2: Apply changes in deterministic order
    pending_changes.sort(key=lambda x: (x['order'], x['key']))
    
    for change in pending_changes:
        _apply_single_change(new_state, change)
    
    return new_state

def _apply_single_change(state: dict, change: dict):
    """Apply a single state change with merge policy"""
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
