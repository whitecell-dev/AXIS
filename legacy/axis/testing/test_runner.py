# AXIS_testing/golden_vectors.py
"""Golden vector testing for cross-platform verification"""
import json
from typing import List, Dict, Any
from AXIS import RuleEngine
import hashlib

class GoldenVectorGenerator:
    """Generate test vectors for AXIS rules"""
    
    def __init__(self, rules_path: str):
        self.engine = RuleEngine(rules_path)
        self.vectors = []
    
    def add_test_case(self, input_data: Dict[str, Any], description: str = ""):
        """Add a test case and capture the expected output"""
        result = self.engine.run(input_data)
        
        vector = {
            'description': description,
            'input': input_data,
            'expected_output': {k: v for k, v in result.items() if k != '_audit'},
            'ir_hash': result['_audit']['ir_hash'],
            'output_hash': result['_audit']['output_hash']
        }
        
        self.vectors.append(vector)
        return vector
    
    def save_vectors(self, filename: str):
        """Save test vectors to JSON file"""
        with open(filename, 'w') as f:
            json.dump({
                'component': self.engine.component_name,
                'vectors': self.vectors
            }, f, indent=2)
    
    def load_vectors(self, filename: str):
        """Load test vectors from JSON file"""
        with open(filename, 'r') as f:
            data = json.load(f)
            self.vectors = data['vectors']

class GoldenVectorRunner:
    """Run golden vector tests for verification"""
    
    def __init__(self, rules_path: str):
        self.engine = RuleEngine(rules_path)
    
    def run_tests(self, vectors_file: str) -> Dict[str, Any]:
        """Run all test vectors and return results"""
        with open(vectors_file, 'r') as f:
            test_data = json.load(f)
        
        results = {
            'total': len(test_data['vectors']),
            'passed': 0,
            'failed': 0,
            'failures': []
        }
        
        for i, vector in enumerate(test_data['vectors']):
            try:
                result = self.engine.run(vector['input'])
                actual_output = {k: v for k, v in result.items() if k != '_audit'}
                
                # Compare outputs
                if actual_output == vector['expected_output']:
                    results['passed'] += 1
                else:
                    results['failed'] += 1
                    results['failures'].append({
                        'test_index': i,
                        'description': vector.get('description', ''),
                        'expected': vector['expected_output'],
                        'actual': actual_output
                    })
                
                # Verify IR hash consistency
                if result['_audit']['ir_hash'] != vector['ir_hash']:
                    results['failures'].append({
                        'test_index': i,
                        'error': 'IR hash mismatch - rules may have changed'
                    })
            
            except Exception as e:
                results['failed'] += 1
                results['failures'].append({
                    'test_index': i,
                    'error': str(e)
                })
        
        return results

