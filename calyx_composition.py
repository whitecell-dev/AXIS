# calyx_composition.py
"""Rule composition and modular YAML management"""
import yaml
from pathlib import Path
from typing import Dict, Any, List, Union

class RuleComposer:
    """Compose rules from multiple YAML files"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
    
    def compose_rules(self, main_file: str) -> Dict[str, Any]:
        """Compose rules from main file and its includes"""
        main_path = self.base_path / main_file
        
        with open(main_path, 'r') as f:
            main_rules = yaml.safe_load(f)
        
        # Process includes
        if 'include' in main_rules:
            included_rules = []
            
            for include_file in main_rules['include']:
                include_path = self.base_path / include_file
                
                with open(include_path, 'r') as f:
                    included = yaml.safe_load(f)
                    
                    # Extract rules from included file
                    if 'rules' in included:
                        included_rules.extend(included['rules'])
                    elif isinstance(included, list):
                        included_rules.extend(included)
            
            # Combine rules: included first, then main rules
            all_rules = included_rules + main_rules.get('rules', [])
            main_rules['rules'] = all_rules
            
            # Clean up include directive
            del main_rules['include']
        
        return main_rules
    
    def validate_composition(self, main_file: str) -> List[str]:
        """Validate that rule composition is valid"""
        errors = []
        
        try:
            composed = self.compose_rules(main_file)
            
            # Check for required fields
            if 'component' not in composed:
                errors.append("Missing 'component' field")
            
            if 'rules' not in composed:
                errors.append("No rules found after composition")
            
            # Validate individual rules
            for i, rule in enumerate(composed.get('rules', [])):
                if 'if' not in rule and 'else' not in rule:
                    errors.append(f"Rule {i}: missing condition ('if' or 'else')")
                
                if 'then' not in rule:
                    errors.append(f"Rule {i}: missing 'then' action")
        
        except Exception as e:
            errors.append(f"Composition failed: {e}")
        
        return errors
