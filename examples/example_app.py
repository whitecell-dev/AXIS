# example_app.py
"""Complete example showing all integrations"""

def create_complete_example():
    """Create a complete example app using all AXIS features"""
    
    # 1. Create example rules with composition
    base_rules = """
component: UserManagement
include:
  - validation_rules.yaml
  - business_rules.yaml

initial_state:
  users: []
  errors: []

rules:
  - if: "action.type == 'CREATE_USER'"
    then:
      users+: [action.user_data]
  
  - if: "len(errors) > 0"
    then:
      status: "validation_failed"
"""
    
    validation_rules = """
rules:
  - if: "not user_data.get('email')"
    then:
      errors+: ["Email is required"]
  
  - if: "user_data.get('age', 0) < 18"
    then:
      errors+: ["Must be 18 or older"]
"""
    
    business_rules = """
rules:
  - if: "user_data.get('role') == 'admin'"
    then:
      permissions: ["read", "write", "admin"]
  
  - if: "user_data.get('role') == 'user'"
    then:
      permissions: ["read"]
"""
    
    # 2. Example Flask app
    flask_app = """
from flask import Flask, request, jsonify
from AXIS_flask import with_AXIS_rules
from AXIS_adapters.database import SQLiteAdapter

app = Flask(__name__)
db = SQLiteAdapter('users.db')

@app.route('/users', methods=['POST'])
@with_AXIS_rules('user_management.yaml')
def create_user(validated_data):
    if validated_data.get('errors'):
        return jsonify({'errors': validated_data['errors']}), 400
    
    # Save to database using adapter
    user_id = db.save('users', validated_data)
    return jsonify({'user_id': user_id, 'status': 'created'})
"""
    
    # 3. Example React hook
    react_hook = generate_react_hook('user_management.yaml', 'useUserManagement')
    
    # 4. Golden vector test
    golden_test = """
from AXIS_testing.golden_vectors import GoldenVectorGenerator

# Generate test vectors
generator = GoldenVectorGenerator('user_management.yaml')

generator.add_test_case(
    {'user_data': {'email': 'test@example.com', 'age': 25, 'role': 'user'}},
    'Valid user creation'
)

generator.add_test_case(
    {'user_data': {'age': 16}},
    'Invalid user - missing email and underage'
)

generator.save_vectors('user_management_tests.json')
"""
    
    return {
        'base_rules': base_rules,
        'validation_rules': validation_rules,
        'business_rules': business_rules,
        'flask_app': flask_app,
        'react_hook': react_hook,
        'golden_test': golden_test
    }
