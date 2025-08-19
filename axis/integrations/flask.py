#!/usr/bin/env python3
"""
Flask integration for AXIS rules
Decorator pattern for route validation
"""

from functools import wraps
from ..engine.rule_engine import RuleEngine

def with_axis_rules(yaml_path: str):
    """Decorator for Flask routes that apply AXIS rules"""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                from flask import request, jsonify, g
            except ImportError:
                raise RuntimeError("Flask integration requires: pip install flask")
            
            # Load rules (cached in Flask's g object)
            if not hasattr(g, 'axis_engine'):
                g.axis_engine = RuleEngine(yaml_path)
            
            # Get request data
            if request.method == 'POST':
                input_data = request.get_json() or {}
            else:
                input_data = request.args.to_dict()
            
            # Apply rules
            result = g.axis_engine.run(input_data)
            
            # Check for errors
            if result.get('errors'):
                return jsonify({'errors': result['errors']}), 400
            
            # Call original function with validated data
            return func(result, *args, **kwargs)
        
        return wrapper
    return decorator

# Example usage:
"""
from axis.integrations.flask import with_axis_rules

@app.route('/users', methods=['POST'])
@with_axis_rules('user_validation.yaml')
def create_user(validated_data):
    # validated_data already processed by AXIS rules
    user_id = db.save('users', validated_data)
    return jsonify({'user_id': user_id})
"""
