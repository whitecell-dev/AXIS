# AXIS

**React for Deterministic Reasoning**

> *"We split the atom of software complexity and found that simplicity was the most powerful force inside."*

Just like React revolutionized frontend development with `UI = f(state)`, AXIS revolutionizes backend logic with `Logic = f(rules, state)`.

**Write business logic once in human-readable YAML. Execute with cryptographic verification.**

## **The Core Insight**

Just like React separated UI concerns, AXIS separates system logic:

| React (Frontend) | AXIS (Backend) |
|------------------|----------------|
| `UI = f(state)` | `Logic = f(rules, state)` |
| Virtual DOM | Secure AST |
| Components | Rules |
| JSX | YAML |
| Pure Functions | Pure Reducers |
| Props → Render | Input → Transform |

## **Built for the Age of AI**

AXIS is **LLM-proof infrastructure**:
- **✅ LLMs generate YAML rules** (safe, human-verifiable)
- **✅ Adapters handle I/O** (controlled boundaries)  
- **✅ Math handles verification** (hash-based proof of correctness)

No more *"here's 500 lines of Python, good luck!"* Just:

```yaml
# user_rules.yaml - LLM can generate this safely
component: UserAccess
rules:
  - if: "age >= 18"
    then: { status: "adult", can_vote: true }
  - if: "role == 'admin'"
    then: { permissions: ["read", "write", "admin"] }
  - if: "not email"
    then: { errors+: ["Email required"] }
```

## **Quick Start**

### Installation
```bash
pip install axis-py
# Optional: pip install "axis-py[yaml]" for YAML support
```

### Your First Rules
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

## **Why AXIS?**

### **🔒 Cryptographically Verified**
Every execution includes a hash-based audit trail. Same input + same rules = mathematically guaranteed identical output.

```python
result = engine.run(user_data)
# Always includes cryptographic proof:
# - IR hash (rules fingerprint)
# - Input hash (data fingerprint)  
# - Output hash (result fingerprint)
```

### **🛡️ LLM-Safe by Design**
```yaml
# ✅ LLM can generate this (safe YAML rules)
- if: "user.subscription == 'premium'"
  then: { discount: 0.2, features: ["unlimited"] }

# ❌ LLM CANNOT do this (I/O is isolated in adapters)
# db.execute("DROP TABLE users")  # Impossible!
```

### **🧠 Human-Readable Logic**
Non-programmers can read, edit, and approve business rules written in YAML.

### **🔄 Pure Functions Everywhere**
React-inspired reducer pattern ensures predictable, testable logic:
```python
# Always returns new state, never mutates input
new_state = apply_rules(rules, old_state, action)
```

## **Framework Integrations**

### Flask
```python
from axis.integrations.flask import with_axis_rules

@app.route('/users', methods=['POST'])
@with_axis_rules('user_validation.yaml')
def create_user(validated_data):
    if validated_data.get('errors'):
        return jsonify({'errors': validated_data['errors']}), 400
    return jsonify({'status': 'created', 'user': validated_data})
```

### FastAPI
```python
from axis.integrations.fastapi import create_axis_dependency

user_validator = create_axis_dependency('user_rules.yaml')

@app.post("/users")
async def create_user(data: dict, validated: dict = Depends(user_validator)):
    return {"user": validated, "status": "created"}
```

## **Controlled I/O Boundaries**

Keep side effects isolated and testable:

```python
from axis.adapters import SQLiteAdapter, HTTPAdapter

# Database operations
db = SQLiteAdapter('users.db')
user_id = db.save('users', validated_data)

# HTTP requests  
api = HTTPAdapter('https://api.example.com')
response = api.post('notifications', {'user_id': user_id})
```

## **Rule Composition**

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

## **Golden Vector Testing**

Verify your rules work consistently:

```python
from axis.testing import GoldenVectorGenerator

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
# ✓ Tests: 10, Passed: 10, Failed: 0
```

## **CLI Reference**

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
```

## **Architecture: The CALYX-PY Philosophy**

AXIS follows the principle: **"Every line of code is a liability until proven otherwise."**

```
YAML Rules → AST → Pure Reducer → Cryptographic Hash
     ↑          ↑         ↑              ↑
  Intent    Security   Logic        Verification
```

**~400 lines of code total.** Readable in one sitting. Easy to port to other languages.

### **The Three Layers**
1. **Rules (YAML)**: Human-readable business logic
2. **Reducers (Pure Functions)**: Deterministic state transitions  
3. **Adapters (Controlled I/O)**: Database, API, file operations

### **Security First**
- **Whitelisted AST operations only** (no eval, no dynamic execution)
- **I/O isolated in adapters** (rules can't perform side effects)
- **Cryptographic verification** (hash-based audit trails)

## **Cross-Platform Vision**

*Current: Python implementation with cryptographic verification*

*Future: Same YAML → Multiple runtimes with identical behavior*

```bash
# Vision (not yet implemented)
axis compile rules.yaml --target python    # ✅ Current
axis compile rules.yaml --target js        # 🚧 Planned  
axis compile rules.yaml --target wasm      # 🚧 Planned
axis compile rules.yaml --target rust      # 🚧 Planned

# Same hash = mathematically identical behavior
```

The foundation is built for cross-platform determinism. The YAML → AST → Reducer pipeline is language-agnostic by design.

## **Examples**

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

## **Why This Matters Now**

In the age of AI, we need **trustworthy infrastructure** for LLM-generated logic:

1. **LLMs generate rules**, not code (safer, auditable)
2. **Humans debug adapters** (traditional imperative code)  
3. **Mathematics handles verification** (hash-based proof)

AXIS is the **missing layer** between AI and production systems.

## **Development**

### Local Setup
```bash
git clone https://github.com/your-org/axis
cd axis
pip install -e ".[dev]"
make test demo
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Follow the CALYX-PY philosophy: **keep it minimal**
4. Add tests and ensure they pass
5. Submit a pull request

## **License**

MIT License - see LICENSE file for details.

## **Philosophy**

> *"Split the atom of software complexity and find that simplicity is the most powerful force inside."*

AXIS proves that the most powerful abstractions are often the simplest ones. By focusing on the essential 20% that delivers 80% of the value, we've created something that's both more powerful and more comprehensible than what came before.

---

**AXIS: Making computational trust as simple as `git commit`** ⚡

*React for Deterministic Reasoning*
