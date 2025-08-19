#!/usr/bin/env python3
"""
Example Flask app using AXIS rules
Demonstrates rule-based validation and business logic
"""

from flask import Flask, request, jsonify
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from axis.integrations.flask import with_axis_rules
from axis.adapters.database import SQLiteAdapter

app = Flask(__name__)

# Initialize database adapter
db = SQLiteAdapter('users.db')

# Create users table if it doesn't exist
try:
    db.conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            age INTEGER,
            role TEXT,
            active BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db.conn.commit()
except Exception as e:
    print(f"Database setup error: {e}")

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'axis-flask-example'})

@app.route('/users', methods=['POST'])
@with_axis_rules('user_rules.yaml')
def create_user(validated_data):
    """Create user with AXIS rule validation"""
    
    # If we get here, validation passed
    if not validated_data.get('valid', False):
        return jsonify({
            'error': 'Validation failed',
            'errors': validated_data.get('errors', [])
        }), 400
    
    # Extract user data (exclude AXIS metadata)
    user_data = {
        'name': validated_data.get('name'),
        'email': validated_data.get('email'),
        'age': validated_data.get('age'),
        'role': validated_data.get('role', 'viewer'),
        'active': validated_data.get('active', True)
    }
    
    try:
        # Save to database
        user_id = db.save('users', user_data)
        
        return jsonify({
            'user_id': user_id,
            'status': 'created',
            'permissions': validated_data.get('permissions', []),
            'access_level': validated_data.get('access_level', 'readonly'),
            'audit_hash': validated_data.get('_audit', {}).get('output_hash', '')[:16]
        }), 201
    
    except Exception as e:
        return jsonify({'error': f'Database error: {e}'}), 500

@app.route('/users', methods=['GET'])
def list_users():
    """List all users"""
    try:
        users = db.find('users')
        return jsonify({'users': users, 'count': len(users)})
    except Exception as e:
        return jsonify({'error': f'Database error: {e}'}), 500

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get specific user"""
    try:
        users = db.find('users', {'id': user_id})
        if not users:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'user': users[0]})
    except Exception as e:
        return jsonify({'error': f'Database error: {e}'}), 500

if __name__ == '__main__':
    print("Starting AXIS Flask Example")
    print("Try:")
    print("  curl -X POST http://localhost:5000/users \\")
    print("       -H 'Content-Type: application/json' \\")
    print("       -d '{\"name\":\"Alice\", \"email\":\"alice@example.com\", \"age\":25, \"role\":\"admin\"}'")
    print("")
    app.run(debug=True, port=5000)
