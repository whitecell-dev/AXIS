#!/usr/bin/env python3
"""
Compose command - combine rules from multiple YAML files
"""

from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

def compose_command(args):
    """Execute axis compose command"""
    if not HAS_YAML:
        raise RuntimeError("Compose requires: pip install pyyaml")
    
    composer = RuleComposer()
    composed = composer.compose_rules(args.rules)
    
    if args.output:
        with open(args.output, 'w') as f:
            yaml.dump(composed, f, indent=2)
        print(f"Composed rules written to {args.output}")
    else:
        print(yaml.dump(composed, indent=2))

class RuleComposer:
    """Simple rule composition from includes"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
    
    def compose_rules(self, main_file: str) -> dict:
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
            
            # Combine: included first, then main rules
            all_rules = included_rules + main_rules.get('rules', [])
            main_rules['rules'] = all_rules
            
            # Clean up include directive
            del main_rules['include']
        
        return main_rules
