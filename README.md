# AXIS

**React for Deterministic Reasoning**

> *"We split the atom of software complexity and found that simplicity was the most powerful force inside."*

AXIS is a zero-boilerplate Python library that brings React's functional programming paradigm to any deterministic system. Write business logic once in human-readable YAML, execute it everywhere with cryptographic verification.

## **Core Insight**

Just like React separated UI concerns (`HTML + CSS + JavaScript`), AXIS separates system logic:

- **YAML** = Intent (human-readable λ-terms)
- **Reducers** = Pure Logic (deterministic state transitions)  
- **Adapters** = Side Effects (controlled I/O operations)

## **Quick Start**

### Installation
```bash
pip install axis-py
# or: pip install pyyaml  # for YAML support
```

### Your First Rules
```yaml
# user_rules.yaml
component: UserValidation
rules:
  - if: "age >= 18"
    then: { status: "adult", can_vote: true }
  - if: "not email"
    then: { errors+: ["Email required"] }
  - if: "role == 'admin'"
    then: { permissions: ["read", "write", "admin"] }
```

### Run Anywhere
```python
from axis import RuleEngine

# Load and execute rules
engine = RuleEngine('user_rules.yaml')
result = engine.run({
    'age': 25, 
    'email': 'alice@example.com', 
    'role': 'admin'
})

print(result)
# {
#   'status': 'adult',
#   'can_vote': True, 
#   'permissions': ['read', 'write', 'admin'],
#   '_audit': { 'ir_hash': 'sha3:abc123...', ... }
# }
```

##  **Why AXIS?**

### ** Cryptographically Verified**
Every execution includes a hash-based audit trail. Same input + same rules = mathematically guaranteed identical output across all platforms.

### ** Universal Portability** 
Write logic once, run everywhere:
- Python (development)
- JavaScript (frontend)  
- WebAssembly (browsers)
- Native code (embedded systems)

### ** Human-Readable Logic**
Non-programmers can read, edit, and approve business rules written in YAML.

### ** Zero-Trust Verification**
```bash
axis test user_rules.yaml test_vectors.json
#  Tests: 10, Passed: 10, Failed: 0
# All platforms produce identical results
```

##  **Framework Integrations**

### Flask
```python
from axis_flask import with_axis_rules

@app.route('/users', methods=['POST'])
@with_axis_rules('user_validation.yaml')
def create_user(validated_data):
    if validated_data.get('errors'):
        return jsonify({'errors': validated_data['errors']}), 400
    return jsonify({'status': 'created', 'user': validated_data})
```

### FastAPI
```python
from axis_fastapi import create_axis_dependency

user_validator = create_axis_dependency('user_rules.yaml')

@app.post("/users")
async def create_user(data: dict, validated: dict = Depends(user_validator)):
    return {"user": validated, "status": "created"}
```

### React (Auto-Generated Hooks)
```bash
axis generate react user_rules.yaml --output useUserRules.ts
```
```typescript
import { useUserRules } from './useUserRules';

function UserForm() {
  const { state, updateState, errors } = useUserRules();
  
  const handleSubmit = (userData) => {
    const result = updateState(userData);
    // Same validation logic as backend!
  };
}
```

## 🔌 **Adapter System**

Keep side effects isolated and testable:

```python
from axis_adapters.database import SQLiteAdapter
from axis_adapters.http import HTTPAdapter

# Database operations
db = SQLiteAdapter('users.db')
user_id = db.save('users', validated_data)

# HTTP requests  
api = HTTPAdapter('https://api.example.com')
response = api.post('notifications', {'user_id': user_id})
```

##  **Rule Composition**

Build complex logic from simple, reusable modules:

```yaml
# main.yaml
component: UserManagement
include:
  - validation_rules.yaml
  - business_rules.yaml
  - permission_rules.yaml

rules:
  - if: "all_validations_passed"
    then: { status: "approved" }
```

```bash
axis compose main.yaml --output composed_rules.yaml
```

##  **Golden Vector Testing**

Verify your rules work identically across all platforms:

```python
from axis_testing import GoldenVectorGenerator

# Generate test cases
generator = GoldenVectorGenerator('user_rules.yaml')
generator.add_test_case(
    {'age': 25, 'email': 'test@example.com'}, 
    'Valid adult user'
)
generator.save_vectors('test_vectors.json')
```

```bash
axis test user_rules.yaml test_vectors.json
# Verifies Python, JavaScript, WASM all produce identical results
```

##  **CLI Reference**

```bash
# Run rules with input data
axis run rules.yaml '{"age": 25, "email": "test@example.com"}'

# Validate rule syntax
axis validate rules.yaml

# Get cryptographic hash of rules
axis hash rules.yaml

# Compose modular rules
axis compose main.yaml --output final_rules.yaml

# Run cross-platform tests
axis test rules.yaml vectors.json

# Generate framework integrations
axis generate react rules.yaml --output useRules.ts
axis generate flask rules.yaml --output app.py
```

##  **Architecture**

### **Functional Programming as Infrastructure**
AXIS applies React's core insight—pure functions + immutable state—to any deterministic system:

```
YAML Rules → AST → Pure Reducer → Cryptographic Audit
     ↑            ↑         ↑              ↑
  Intent      Security   Logic        Verification
```

### **The Three Layers**
1. **Rules (YAML)**: Human-readable business logic
2. **Reducers (Pure Functions)**: Deterministic state transitions  
3. **Adapters (Controlled I/O)**: Database, API, file operations

### **Trust Through Mathematics**
- **Canonical IR**: Deterministic intermediate representation
- **SHA3-256 Hashing**: Cryptographic verification of execution
- **Cross-Platform Verification**: Same hash = same behavior everywhere

## 🤖 **LLM Integration**

AXIS is designed for the age of AI:

- **LLMs generate YAML rules** (declarative, human-verifiable)
- **Humans debug adapters** (imperative I/O code)
- **Mathematics handles verification** (hash-based audit trails)

```yaml
# LLM can generate this reliably
rules:
  - if: "user.subscription == 'premium'"
    then: { features: ["unlimited", "priority"], rate_limit: 10000 }
  - if: "user.subscription == 'free'"
    then: { features: ["basic"], rate_limit: 100 }
```

##  **Examples**

### User Access Control
```yaml
component: AccessControl
rules:
  - if: "user.role == 'admin'"
    then: { access: "full", permissions: ["read", "write", "delete"] }
  - if: "user.role == 'editor'"  
    then: { access: "limited", permissions: ["read", "write"] }
  - if: "user.active == false"
    then: { access: "denied", permissions: [] }
```

### E-commerce Pricing
```yaml
component: PricingEngine
rules:
  - if: "cart.total > 100 and user.vip"
    then: { discount: 0.2, shipping: "free" }
  - if: "cart.total > 50"
    then: { discount: 0.1, shipping: "standard" }
  - if: "user.first_purchase"
    then: { discount: 0.15, welcome_bonus: 10 }
```

### Content Moderation
```yaml
component: ContentFilter
rules:
  - if: "text_length > 1000"
    then: { status: "requires_review", priority: "low" }
  - if: "contains_profanity or spam_score > 0.8"
    then: { status: "blocked", reason: "policy_violation" }
  - if: "user.reputation > 100"
    then: { status: "auto_approved", fast_track: true }
```

## 🔧 **Development**

### Local Development
```bash
git clone https://github.com/your-org/axis
cd axis
pip install -e .

# Run tests
python -m pytest

# Run examples
python examples/flask_app.py
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality  
4. Ensure all tests pass
5. Submit a pull request

##  **License**

MIT License - see LICENSE file for details.

##  **Acknowledgments**

AXIS builds on insights from:
- **React/Redux**: Functional state management patterns
- **Git**: Content-addressable storage and hashing
- **WebAssembly**: Universal compilation targets
- **Kubernetes**: Declarative configuration as code

## 🔗 **Links**

- [Documentation](https://axis-docs.example.com)
- [Examples](https://github.com/whitecell-dev/axis/tree/main/examples)
- [Community](https://discord.gg/axis)
- [Issues](https://github.com/whitecell-dev/axis/issues)

---

**AXIS: React for Deterministic Reasoning**  
*Making computational trust as simple as `git commit`* ⚡
