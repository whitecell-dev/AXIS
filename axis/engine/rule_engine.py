#!/usr/bin/env python3
"""
Core rule engine - like a React component for business logic
Minimal, focused on YAML → AST → Reducer pipeline
"""

import json
from typing import Union, List, Dict, Any
from .reducer import apply_rules
from .hash import generate_ir_hash, sha3_256_hex, canonicalize

# Optional YAML support
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

class RuleEngine:
    """
    YAML-based rule engine - React component for business logic
    Focuses on the essential: YAML → AST → Pure Reducer
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
        self.ir_hash = generate_ir_hash(self.rules, self.component_name)
    
    def run(self, input_data: dict, action: dict = None) -> dict:
        """
        Execute rules against input data
        Returns: new state with cryptographic audit trail
        """
        if action is None:
            action = {'type': 'RULE_CHECK'}
        
        # Apply rules to get new state
        new_state = apply_rules(self.rules, input_data, action)
        
        # Add audit trail for verification
        audit_entry = {
            'ir_hash': self.ir_hash,
            'input_hash': sha3_256_hex(json.dumps(canonicalize(input_data), sort_keys=True)),
            'output_hash': sha3_256_hex(json.dumps(canonicalize(new_state), sort_keys=True)),
            'action': action
        }
        
        # Return state with audit (non-mutating)
        return {
            **new_state,
            '_audit': audit_entry
        }
    
    def create_reducer(self):
        """
        Create Redux-style reducer function
        Returns: (state, action) -> new_state
        """
        def reducer(state: dict, action: dict) -> dict:
            return self.run(state, action)
        return reducer
