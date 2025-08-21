#!/usr/bin/env python3
"""
AXIS Pipeline Demo
Shows pipes → rules → adapters working together

This demonstrates the complete AXIS workflow:
1. PIPES: Normalize messy input data (α-conversion)
2. RULES: Apply business logic (β-reduction)  
3. ADAPTERS: Execute side effects (monadic effects)

Usage:
    python demo_pipeline.py
"""

import json
import tempfile
import os
import subprocess
from pathlib import Path

def run_axis_pipeline():
    """Demonstrate complete AXIS pipeline"""
    print("🚀 AXIS Pipeline Demo")
    print("Pipes → Rules → Adapters\n")
    
    # Sample messy input data
    messy_data = {
        "usr": "alice", 
        "mail": "alice@example.com",
        "years": "25",
        "role": "admin",
        "is_active": "true"
    }
    
    print(f"📥 Input Data (messy):")
    print(json.dumps(messy_data, indent=2))
    
    # Create temp directory for configs
    with tempfile.TemporaryDirectory() as tmpdir:
        
        # 1. PIPES CONFIG - Normalize the data
        pipes_config = {
            "pipeline": [
                {"rename": {"usr": "user", "mail": "email", "years": "age"}},
                {"validate": {"age": "int", "is_active": "bool"}},
                {"enrich": {"timestamp": "now()", "source": "demo"}}
            ]
        }
        
        pipes_file = os.path.join(tmpdir, "normalize.yaml")
        with open(pipes_file, 'w') as f:
            import yaml
            yaml.dump(pipes_config, f)
        
        # 2. RULES CONFIG - Apply business logic  
        rules_config = {
            "component": "UserProcessor",
            "rules": [
                {"if": "age >= 18", "then": {"status": "adult", "can_vote": True}},
                {"if": "age < 18", "then": {"status": "minor", "can_vote": False}},
                {"if": "role == 'admin'", "then": {"permissions": ["read", "write", "admin"]}},
                {"if": "not is_active", "then": {"errors+": ["Account disabled"]}}
            ]
        }
        
        rules_file = os.path.join(tmpdir, "logic.yaml")
        with open(rules_file, 'w') as f:
            yaml.dump(rules_config, f)
        
        # 3. ADAPTERS CONFIG - Execute effects
        adapters_config = {
            "adapters": [
                {
                    "name": "log_processing",
                    "command": "echo",
                    "args": ["Processing user: {{user}} ({{email}})"]
                },
                {
                    "name": "save_result",
                    "command": "echo",
                    "args": ["Saving: {{status}} user with {{permissions|length}} permissions"]
                },
                {
                    "name": "audit_log",
                    "command": "echo",
                    "args": ["AUDIT: {{user}} processed at {{timestamp}}"]
                }
            ]
        }
        
        adapters_file = os.path.join(tmpdir, "effects.yaml")
        with open(adapters_file, 'w') as f:
            yaml.dump(adapters_config, f)
        
        # Create input file
        input_file = os.path.join(tmpdir, "input.json")
        with open(input_file, 'w') as f:
            json.dump(messy_data, f)
        
        print(f"\n🔀 Step 1: PIPES (normalize data)")
        
        # Run pipes
        result = subprocess.run([
            'python', 'axis_pipes.py', 'run', pipes_file, '--input', input_file
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Pipes failed: {result.stderr}")
            return
        
        pipes_output = json.loads(result.stdout)
        clean_pipes_output = {k: v for k, v in pipes_output.items() if k != '_pipe_audit'}
        
        print(json.dumps(clean_pipes_output, indent=2))
        print(f"Hash: {pipes_output['_pipe_audit']['pipeline_hash'][:16]}...")
        
        # Save pipes output
        pipes_output_file = os.path.join(tmpdir, "pipes_output.json")
        with open(pipes_output_file, 'w') as f:
            json.dump(pipes_output, f)
        
        print(f"\n⚖️ Step 2: RULES (apply logic)")
        
        # Run rules
        result = subprocess.run([
            'python', 'axis_rules.py', 'apply', rules_file, '--input', pipes_output_file
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Rules failed: {result.stderr}")
            return
        
        rules_output = json.loads(result.stdout)
        clean_rules_output = {k: v for k, v in rules_output.items() if k not in ['_pipe_audit', '_rule_audit']}
        
        print(json.dumps(clean_rules_output, indent=2))
        print(f"Hash: {rules_output['_rule_audit']['rules_hash'][:16]}...")
        
        # Save rules output
        rules_output_file = os.path.join(tmpdir, "rules_output.json")
        with open(rules_output_file, 'w') as f:
            json.dump(rules_output, f)
        
        print(f"\n🔌 Step 3: ADAPTERS (execute effects)")
        
        # Run adapters
        result = subprocess.run([
            'python', 'axis_adapters.py', 'exec', adapters_file, '--input', rules_output_file
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Adapters failed: {result.stderr}")
            return
        
        adapters_output = json.loads(result.stdout)
        
        print("Effects executed:")
        for result in adapters_output['results']:
            if result['status'] == 'success':
                print(f"  ✅ {result['adapter_name']}: {result.get('stdout', {}).get('output', '').strip()}")
            else:
                print(f"  ❌ {result['adapter_name']}: {result.get('stderr', '')}")
        
        print(f"Hash: {adapters_output['_adapter_audit']['config_hash'][:16]}...")
        
        print(f"\n🎯 Pipeline Complete!")
        print(f"   📥 Messy input → 🔀 Clean data → ⚖️ Business logic → 🔌 Side effects")
        print(f"   All steps hash-verified and auditable")
        
        # Show the one-liner equivalent
        print(f"\n💡 This pipeline as a one-liner:")
        print(f"   cat input.json | axis_pipes.py run normalize.yaml | axis_rules.py apply logic.yaml | axis_adapters.py exec effects.yaml")

if __name__ == "__main__":
    try:
        run_axis_pipeline()
    except FileNotFoundError as e:
        print(f"❌ Missing dependency: {e}")
        print(f"Make sure axis_pipes.py, axis_rules.py, and axis_adapters.py are in the current directory")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
