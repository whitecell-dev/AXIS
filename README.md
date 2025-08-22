# AXIS: React for Deterministic Reasoning

> *"We split the atom of software complexity and found that simplicity was the most powerful force inside."*

**AXIS is Unix pipes for structured data.** Just like React revolutionized frontend development with `UI = f(state)`, AXIS revolutionizes terminal computing with `Logic = f(rules, state)`.

**Write business logic once in human-readable YAML. Execute everywhere with cryptographic verification.**

## **The Core Insight**

AXIS completes what Unix started—universal composition of tools through structured data streams.

| Unix (1970s) | AXIS (2025) |
|---------------|-------------|
| `cat file.txt \| grep pattern \| sort` | `cat data.json \| axis-pipes run clean.yaml \| axis-rules apply logic.yaml` |
| Text streams | **Structured streams** |
| String manipulation | **Meaning-aware processing** |
| Manual verification | **Cryptographic verification** |

## **Quick Start**

### Installation
```bash
pip install axis-py
# Or from source:
git clone https://github.com/your-org/axis
cd axis && pip install -e .
```

### Your First Pipeline
```bash
# 1. Create sample data
echo '{"user_name": "Alice", "age": "25", "role": "admin"}' > user.json

# 2. Normalize data (PIPES)
cat user.json | python axis_pipes.py run examples/normalize.yaml

# 3. Apply business logic (RULES)  
cat user.json | python axis_pipes.py run examples/normalize.yaml | python axis_rules.py apply examples/logic.yaml

# 4. Execute side effects (ADAPTERS)
cat user.json | python axis_pipes.py run examples/normalize.yaml | python axis_rules.py apply examples/logic.yaml | python axis_adapters.py exec examples/save.yaml
```

### Example Configs

**normalize.yaml (PIPES)**
```yaml
pipeline:
  - rename: {user_name: "name", years: "age"}
  - validate: {age: "int", active: "bool"}  
  - enrich: {timestamp: "now()"}
```

**logic.yaml (RULES)**
```yaml
component: UserAccess
rules:
  - if: "age >= 18"
    then: {status: "adult", can_vote: true}
  - if: "role == 'admin'"  
    then: {permissions: ["read", "write", "admin"]}
```

**save.yaml (ADAPTERS)**
```yaml
adapters:
  - name: "log_user"
    command: "echo" 
    args: ["Processing: {{name}} ({{status}})"]
  - name: "save_db"
    command: "sqlite3"
    args: ["users.db", "INSERT INTO users VALUES ('{{name}}', {{age}}, '{{status}}');"]
```

## **The Three Components**

### **🔀 AXIS-PIPES (α-conversion)**
*Data normalization and validation*

```bash
# Clean messy API responses
curl api.com/users | axis_pipes.py run normalize_users.yaml

# Validate form data
cat form_data.json | axis_pipes.py run validate_registration.yaml  

# Enrich with defaults
echo '{"name": "Alice"}' | axis_pipes.py run add_defaults.yaml
```

**What it does:**
- Rename fields (`user_name` → `name`)
- Convert types (`"25"` → `25`)
- Validate data (`email` format checking)
- Enrich with computed fields
- Filter unwanted data

### **⚖️ AXIS-RULES (β-reduction)**
*Pure decision logic and state transformations*

```bash
# Apply business rules
cat clean_data.json | axis_rules.py apply business_logic.yaml

# User permissions
cat user.json | axis_rules.py apply access_control.yaml

# Pricing logic  
cat cart.json | axis_rules.py apply discount_rules.yaml
```

**What it does:**
- If/then conditional logic
- Pure state transformations  
- Role-based permissions
- Complex business rules
- Error condition handling

### **🔌 AXIS-ADAPTERS (monadic effects)**
*Controlled side effects and external system integration*

```bash
# Save to database
cat result.json | axis_adapters.py exec save_to_db.yaml

# Send notifications
cat user.json | axis_adapters.py exec send_welcome_email.yaml

# Update external APIs
cat order.json | axis_adapters.py exec process_payment.yaml
```

**What it does:**
- Execute Unix commands safely
- Template-based parameter substitution
- Database operations (`psql`, `sqlite3`)
- HTTP requests (`curl`)
- File operations (`cp`, `mv`)
- Email/notifications (`mail`)

## **Why AXIS?**

### **🔒 Cryptographically Verified**
Every step includes hash-based audit trails. Same input + same config = mathematically guaranteed identical output.

```bash
axis_rules.py hash logic.yaml        # abc123...
axis_rules.py apply logic.yaml data  # Same hash = same behavior everywhere
```

### **🧠 LLM-Safe by Design**
```yaml
# ✅ LLM can generate this safely (declarative YAML)
rules:
  - if: "user.subscription == 'premium'"
    then: {discount: 0.2, features: ["unlimited"]}

# ❌ LLM CANNOT do this (I/O is isolated in adapters)  
# os.system("rm -rf /")  # Impossible in YAML rules!
```

### **🔄 Universal Composition**
```bash
# Mix AXIS with existing Unix tools
cat logs.txt | grep ERROR | axis_pipes.py run parse_errors.yaml | axis_rules.py apply severity_logic.yaml | mail admin@company.com

# Or build pure AXIS pipelines
cat orders.json | axis_pipes.py run clean.yaml | axis_rules.py apply pricing.yaml | axis_adapters.py exec fulfill.yaml
```

### **🌐 Cross-Platform Ready**
Same YAML configs work across:
- **Python** (current implementation)
- **Rust** (planned - 100x faster)  
- **JavaScript** (planned - browser execution)
- **WASM** (planned - universal deployment)

## **Real-World Examples**

### **E-commerce Order Processing**
```bash
# Complete order fulfillment pipeline
curl api.com/orders/123 \
  | axis_pipes.py run normalize_order.yaml \
  | axis_rules.py apply inventory_check.yaml \
  | axis_rules.py apply pricing_logic.yaml \
  | axis_adapters.py exec charge_payment.yaml \
  | axis_adapters.py exec send_confirmation.yaml \
  | axis_adapters.py exec update_inventory.yaml
```

### **User Registration**
```bash
# Validate and process new users
cat registration_form.json \
  | axis_pipes.py run validate_user.yaml \
  | axis_rules.py apply signup_rules.yaml \
  | axis_adapters.py exec create_account.yaml \
  | axis_adapters.py exec send_welcome_email.yaml
```

### **Data ETL Pipeline**
```bash
# Extract, transform, load
cat raw_data.csv \
  | axis_pipes.py run csv_to_json.yaml \
  | axis_pipes.py run clean_data.yaml \
  | axis_rules.py apply business_logic.yaml \
  | axis_adapters.py exec load_warehouse.yaml
```

### **Automated Reports**
```bash
# Daily analytics (perfect for cron jobs)
echo '{"date": "'$(date -I)'"}' \
  | axis_adapters.py exec fetch_metrics.yaml \
  | axis_pipes.py run aggregate_data.yaml \
  | axis_rules.py apply insights.yaml \
  | axis_adapters.py exec email_report.yaml
```

## **Built for the AI Era**

AXIS is **LLM-proof infrastructure**:

- **LLMs generate YAML rules** (safe, human-verifiable)  
- **Adapters handle I/O** (controlled boundaries)
- **Math handles verification** (hash-based proof of correctness)

No more *"here's 500 lines of Python, good luck!"*—just safe, declarative logic.

## **Architecture: The Lambda Calculus Foundation**

AXIS implements pure λ-calculus for structured data:

```
Raw Input (JSON)
      ↓
α-conversion (PIPES) → Normalize/reshape data  
      ↓
β-reduction (RULES) → Apply pure logic
      ↓  
α-conversion (PIPES) → Format results
      ↓
Effects (ADAPTERS) → Touch the outside world
      ↓
Final Output (JSON + Side Effects)
```

**This is mathematically proven, cross-platform deterministic computation.**

## **Development**

### **Local Setup**
```bash
git clone https://github.com/your-org/axis
cd axis
pip install -e ".[dev]"

# Run tests
python -m pytest

# Run demo
python demo_pipeline.py
```

### **Project Structure**
```
axis/
├── axis_pipes.py      # Data normalization (α-conversion)
├── axis_rules.py      # Business logic (β-reduction)  
├── axis_adapters.py   # Side effects (monadic effects)
├── demo_pipeline.py   # Complete example
├── examples/          # Sample configurations
│   ├── normalize.yaml
│   ├── logic.yaml
│   └── save.yaml
└── tests/            # Test suite
```

### **Contributing**
1. Fork the repository
2. Create a feature branch  
3. Follow the **AXIS Philosophy**: keep it minimal (~150 LOC per component)
4. Add tests and ensure they pass
5. Submit a pull request

## **CLI Reference**

### **AXIS-PIPES**
```bash
axis_pipes.py run config.yaml [--input file.json] [--output result.json]
axis_pipes.py validate config.yaml
axis_pipes.py hash config.yaml
```

### **AXIS-RULES**  
```bash
axis_rules.py apply config.yaml [--input file.json] [--output result.json]
axis_rules.py validate config.yaml  
axis_rules.py hash config.yaml
```

### **AXIS-ADAPTERS**
```bash
axis_adapters.py exec config.yaml [--input file.json] [--output result.json] 
axis_adapters.py validate config.yaml
axis_adapters.py hash config.yaml
axis_adapters.py exec config.yaml --dry-run  # Show what would be executed
```

## **Roadmap**

### **Phase 1: Python Foundation** ✅
- [x] Core three components (pipes, rules, adapters)
- [x] Hash verification system
- [x] CLI interfaces
- [x] Demo pipeline

### **Phase 2: Ecosystem** 🚧
- [ ] KERN compiler (YAML → WASM/native)
- [ ] MNEME memory system (Git for logic)
- [ ] Web dashboard for pipeline monitoring
- [ ] VS Code extension for YAML editing

### **Phase 3: Cross-Platform** 🔮
- [ ] Rust implementation (100x performance)
- [ ] JavaScript/WASM targets  
- [ ] Mobile SDKs (iOS/Android)
- [ ] Edge deployment tools

## **Philosophy: AXIS-PY**

> *"Every line of code is a liability until proven otherwise."*

AXIS follows the **AXIS-PY philosophy**:
- **~150 LOC per component** (readable in one sitting)
- **Pure functions wherever possible** (predictable behavior)
- **Explicit over implicit** (no magic, no surprises)
- **Composable by design** (Unix philosophy)
- **Hash-verified execution** (mathematical guarantees)

## **License**

MIT License - see LICENSE file for details.

## **Acknowledgments**

AXIS builds on insights from:
- **Unix/Linux**: Universal composition through pipes
- **React/Redux**: Pure functions and state management  
- **Git**: Content-addressable storage and verification
- **Lambda Calculus**: Mathematical foundation of computation

---

**AXIS: Making computational trust as simple as `git commit`** ⚡

*Unix pipes for structured data. React patterns for business logic. Git-style verification for everything.*

**The terminal just got a nervous system.**
