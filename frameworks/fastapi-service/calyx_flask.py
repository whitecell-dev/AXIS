# calyx_flask.py
"""Flask integration for CALYX rules"""
from flask import Flask, request, jsonify, g
from calyx import RuleEngine
import json

def with_calyx_rules(yaml_path):
    """Decorator for Flask routes that apply CALYX rules"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Load rules (cached in Flask's g object)
            if not hasattr(g, 'calyx_engine'):
                g.calyx_engine = RuleEngine(yaml_path)
            
            # Get request data
            if request.method == 'POST':
                input_data = request.get_json() or {}
            else:
                input_data = request.args.to_dict()
            
            # Apply rules
            result = g.calyx_engine.run(input_data)
            
            # Check for errors
            if result.get('errors'):
                return jsonify({'errors': result['errors']}), 400
            
            # Call original function with enriched data
            return func(result, *args, **kwargs)
        
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator

# Example Flask usage:
"""
from calyx_flask import with_calyx_rules

@app.route('/users', methods=['POST'])
@with_calyx_rules('user_validation.yaml')
def create_user(validated_data):
    # validated_data already processed by CALYX rules
    user_id = db.create_user(validated_data)
    return jsonify({'user_id': user_id})
"""
