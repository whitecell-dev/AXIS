# AXIS Architecture

**React for Deterministic Reasoning**

## **Core Philosophy: CALYX-PY**

> *"Every line of code is a liability until proven otherwise"*

AXIS follows the **CALYX-PY philosophy**:
- **Every line of code is a liability until proven otherwise**
- **Keep only what's essential for YAML → AST → IR → Pure Reducer pipeline**
- **Replace "magic" with explicit, predictable code**
- **~300-400 LOC total** (readable by a single person)
- **Mathematical guarantees over clever abstractions**
- **Zero core dependencies** (pure Python stdlib)

## **The Three-Layer Architecture**

```
🔥 Raw Input (JSON/YAML)
         ↓
🔀 AXIS-PIPES (α-conversion)
    Data normalization, validation, reshaping
         ↓  
⚖️ AXIS-RULES (β-reduction)
    Pure decision logic, state transformations
         ↓
🔌 AXIS-ADAPTERS (monadic effects)
    Controlled side effects, external integration
         ↓
📤 Final Output (JSON + Side Effects)
```

**Each layer is a pure function with cryptographic verification.**

## **Determinism Guarantees**

### **Strict Determinism Requirements**

- **PIPES and RULES are pure functions** - no side effects, no I/O, no time dependencies
- **Time injection via adapters only** - use `clock.yaml` adapter to inject timestamps
- **RFC 8785 compliant canonicalization** - identical JSON serialization across platforms
- **Payload-view hashing** - exclude audit trails from determinism calculations
- **Single-pass rule semantics** - rules evaluate against frozen input context

### **Hash Chain Verification**

```python
input_hash = sha3_256(canonicalize(payload_view(input)))
output_hash = sha3_256(canonicalize(payload_view(output)))
config_hash = sha3_256(canonicalize(config))

# Each component provides mathematical proof:
# Same config + same input = same output hash (always)
```

## **Component Breakdown**

### **1. AXIS-PIPES (~200 LOC)**
*Alpha-conversion for structured data*

**Purpose**: Transform any input into clean, normalized JSON  
**Guarantees**: Pure function, deterministic, hash-verified

```python
def run(self, input_data: dict) -> dict:
    # α-conversion: rename, reshape, validate, enrich (deterministic only)
    return normalized_data
```

**Operations:**
- **extract**: Pull specific fields/paths from nested data
- **rename**: Change field names (`user_name` → `name`)  
- **validate**: Type checking and coercion (`"25"` → `25`)
- **filter**: Remove unwanted data based on conditions
- **enrich**: Add computed fields (deterministic values only)
- **transform**: Template-based field generation

**Security**: Pure functions only, no file I/O, no network access, no time dependencies

### **2. AXIS-RULES (~200 LOC)**
*Beta-reduction for business logic*

**Purpose**: Apply if/then logic to transform state deterministically  
**Guarantees**: Pure functions, no side effects, cryptographically verified

```python
def apply(self, input_data: dict) -> dict:
    # β-reduction: evaluate conditions, apply transformations
    return new_state
```

**Features:**
- **Secure AST parsing**: Only whitelisted operations (`==`, `>`, `and`, etc.)
- **Length and depth limits**: Max 4KB conditions, 32 AST depth levels
- **Dot notation access**: `user.role`, `order.total`
- **Conditional logic**: `if: "age >= 18"` then: `{adult: true}`
- **Merge policies**: `errors+: ["message"]` (append to arrays)
- **Single-pass semantics**: Rules evaluated against frozen input context

**Security**: No `eval()`, no dynamic code execution, restricted AST whitelist, resource limits

### **3. AXIS-ADAPTERS (~200 LOC)**
*Monadic effects for external systems*

**Purpose**: Execute side effects safely with full audit trail  
**Guarantees**: Command allowlist, injection prevention, resource limits, execution logging

```python
def exec(self, input_data: dict) -> dict:
    # Execute commands with secure template substitution
    return execution_results
```

**Security Features:**
- **Command allowlist**: Only pre-approved commands (`sqlite3`, `curl`, `mail`, etc.)
- **Injection prevention**: Template filters (`{{field|sql}}`, `{{field|sharg}}`)
- **Resource limits**: CPU, memory, file size, process count limits
- **Template sanitization**: Reject unsafe characters in unfiltered substitution
- **Execution isolation**: Subprocess sandboxing, restricted environment

**Template Filters:**
- `{{data|json}}` - JSON encode
- `{{field|sharg}}` - Shell argument quoting  
- `{{field|sql}}` - SQL single-quote escaping
- `{{field|url}}` - URL encoding
- `{{field|b64}}` - Base64 encoding

## **Security Model**

### **Attack Surface Minimization**

```
Component       Attack Vectors           Mitigations
---------       --------------           -----------
PIPES           Malformed JSON           Strict JSON validation
                Type confusion           Explicit type coercion
                
RULES           Code injection           AST whitelist, no eval()
                Logic bombs              Pure functions only
                AST bombs                Length/depth limits
                
ADAPTERS        Command injection        Template filters required
                Path traversal           Command allowlist
                Resource exhaustion      CPU/memory/file limits
```

### **Command Allowlist Security**

```python
DEFAULT_COMMAND_ALLOWLIST = {
    'echo', 'cat', 'date', 'wc', 'head', 'tail', 'sort', 'uniq',
    'sqlite3', 'psql', 'mysql', 'curl', 'wget', 'mail', 'sendmail',
    'jq', 'grep', 'sed', 'awk', 'tr', 'cut', 'base64'
}
```

**Security Rules:**
- No absolute paths (`/bin/sh` rejected)
- No shell metacharacters in commands
- Sensitive commands require template filters
- `--unsafe` flag required to bypass (development only)

### **Template Injection Prevention**

```yaml
# ❌ Unsafe - will be rejected
adapters:
  - name: vulnerable
    command: sqlite3
    args: ["db.sqlite", "SELECT * FROM users WHERE name = '{{name}}'"]

# ✅ Safe - uses SQL filter
adapters:
  - name: secure
    command: sqlite3
    args: ["db.sqlite", "SELECT * FROM users WHERE name = '{{name|sql}}'"]
```

## **Mathematical Foundation**

### **Lambda Calculus Implementation**

AXIS implements pure λ-calculus for structured data:

```
λ-term                  AXIS Component
------                  --------------
α-conversion           AXIS-PIPES (rename variables)
β-reduction            AXIS-RULES (apply functions)  
η-conversion           (not needed - explicit over implicit)
Church encoding        AXIS-ADAPTERS (effects as data)
```

### **RFC 8785 Cryptographic Verification**

Every component generates content-addressable hashes:

```python
def compute_hash(obj: Any) -> str:
    canonical = canonicalize(obj)  # RFC 8785 compliant
    json_str = json.dumps(canonical, sort_keys=True, separators=(',', ':'))
    return sha3_256(json_str).hexdigest()
```

**Hash Properties:**
- **Deterministic**: Same config = same hash (mathematically guaranteed)
- **Collision-resistant**: SHA3-256 cryptographic strength
- **Cross-platform**: Identical across Python, Rust, JS, WASM
- **Verifiable**: Can prove two systems have identical logic
- **Payload-focused**: Audit trails excluded from determinism calculations

## **Data Flow Architecture**

### **Pipeline Execution Model**

```bash
# Terminal pipeline
cat input.json \
  | axis-pipes run normalize.yaml \
  | axis-rules apply logic.yaml \  
  | axis-adapters exec effects.yaml

# Each step:
# 1. Reads JSON from stdin
# 2. Loads YAML config
# 3. Applies transformations
# 4. Outputs JSON to stdout
# 5. Includes hash audit trail
```

### **State Transitions with Proof Chain**

```
Raw Data → Clean Data → Logic Data → Effect Results
   ↓           ↓           ↓            ↓
Hash A      Hash B      Hash C       Hash D

# Hash chain proves entire execution path
# Any tampering breaks the cryptographic proof
```

### **Error Handling as Data**

```python
# Errors are data, not exceptions
{
    "user": "alice",
    "age": 25,
    "errors": ["Invalid email format"],  # Errors accumulate
    "_pipe_audit": {"hash": "abc123...", "input_hash": "def456..."},
    "_rule_audit": {"hash": "789abc...", "rules_applied": 3}
}
```

## **Time and Determinism**

### **Problem: Non-Deterministic Time**

```yaml
# ❌ This breaks determinism
pipeline:
  - enrich: {timestamp: "now()"}  # Different on every run!
```

### **Solution: Time Injection via Adapters**

```yaml
# ✅ Deterministic time injection
# 1. Use clock adapter first:
adapters:
  - name: inject_time
    command: date
    args: ["+%Y-%m-%dT%H:%M:%SZ"]
    
# 2. Then use in pipes:
pipeline:
  - enrich: {timestamp: "{{_axis.clock}}"}
```

**For Testing with Fixed Time:**

```bash
echo '{"_time_override": "2024-01-01T00:00:00Z"}' | axis-adapters exec clock.yaml
```

## **Cross-Platform Strategy**

### **Current: Python Reference Implementation**

```
axis_pipes.py     ~200 LOC  Pure Python, stdlib only
axis_rules.py     ~200 LOC  AST parser, hash verification  
axis_adapters.py  ~200 LOC  Secure subprocess management
Total:            ~600 LOC  Readable by one person
```

### **Future: Multi-Language Targets**

```
Language    Performance    Use Case
--------    -----------    --------
Python      1x (baseline)  Development, prototyping
Rust        100x           Production servers, CLI tools
JavaScript  10x            Frontend, Node.js, serverless  
WASM        50x            Browser, edge, universal deployment
Go          20x            Microservices, cloud native
C           200x           Embedded systems, IoT
```

**Key Insight**: The ~600 LOC core is simple enough to port to any language while maintaining identical behavior (verified by hash).

## **Testing and Verification**

### **Golden Master Test Vectors**

```json
{
  "canonicalization_tests": [...],
  "pipes_tests": [...],
  "rules_tests": [...],
  "adapters_tests": [...],
  "security_tests": [...],
  "determinism_tests": [...]
}
```

**Cross-Platform Verification:**
- Same input + same config = same hash across all implementations
- Test vectors ensure mathematical equivalence
- Security tests verify injection prevention

### **Property-Based Testing**

- **Canonicalization idempotence**: `canonicalize(canonicalize(x)) == canonicalize(x)`
- **Hash determinism**: Multiple runs produce identical hashes
- **Rule commutativity**: Rule order doesn't affect final state (within single pass)
- **Security boundaries**: Command injection always prevented

## **Performance Characteristics**

### **Python Implementation (Baseline)**

```
Operation           Time        Memory      Notes
---------           ----        ------      -----
PIPES processing    ~1ms        ~1MB        Per 1KB JSON
RULES evaluation    ~0.5ms      ~0.5MB      Per 10 rules  
ADAPTERS execution  ~10ms       ~2MB        Per command (subprocess overhead)
Hash generation     ~0.1ms      ~0.1MB      SHA3-256
JSON canonicalize   ~0.2ms      ~1MB        RFC 8785 compliant
```

### **Scaling Properties**

- **Linear with data size**: O(n) where n = JSON size
- **Linear with rule count**: O(r) where r = number of rules
- **Constant memory overhead**: ~5MB baseline per process
- **Parallel execution**: Each component can run on different cores
- **Horizontal scaling**: Stateless, no shared state between executions

## **Integration Patterns**

### **Web Framework Integration**

```python
# Flask with AXIS
@app.route('/process', methods=['POST'])
def process_request():
    data = request.get_json()
    
    # AXIS pipeline with hash verification
    pipes_result = pipes_engine.run(data)
    rules_result = rules_engine.apply(pipes_result)  
    effects_result = adapters_engine.exec(rules_result)
    
    return jsonify({
        'result': effects_result,
        'proof_chain': [
            pipes_result['_pipe_audit']['output_hash'],
            rules_result['_rule_audit']['output_hash'],
            effects_result['_adapter_audit']['config_hash']
        ]
    })
```

### **Cron Job Automation**

```bash
# /etc/cron.d/daily-reports
0 9 * * * cat /data/daily.json | \
  axis-adapters exec clock.yaml | \
  axis-pipes run clean.yaml | \
  axis-rules apply analysis.yaml | \
  axis-adapters exec email.yaml
```

### **CI/CD Pipeline Integration**

```yaml
# .github/workflows/deploy.yml
- name: Process deployment data with verification
  run: |
    HASH_CHAIN=""
    cat deploy_config.json \
      | axis-pipes run validate_config.yaml \
      | tee >(jq -r '._pipe_audit.output_hash' >> hashes.txt) \
      | axis-rules apply deployment_logic.yaml \
      | tee >(jq -r '._rule_audit.output_hash' >> hashes.txt) \
      | axis-adapters exec deploy_to_k8s.yaml
    
    # Verify hash chain for deployment proof
    echo "Deployment hash chain:" && cat hashes.txt
```

## **Security Model Deep Dive**

### **Trust Boundaries**

```
Trusted:        YAML configs (version controlled, reviewed)
                JSON data (validated by pipes)
                Hash verification system
                Command allowlist

Semi-trusted:   Template substitution (filtered parameter injection)
                Subprocess execution (isolated, logged, limited)

Untrusted:      Raw user input (must pass through pipes)
                External command output (treated as opaque data)
                Network responses (via curl/wget adapters)
```

### **Adapter Security Architecture**

```python
# Security layers in adapters:
1. Command allowlist check
2. Template filter requirement for sensitive commands
3. Resource limits (CPU, memory, file size)
4. Environment variable restriction
5. Subprocess isolation
6. Execution timeout
7. Full audit logging
```

**Example Secure SQL Adapter:**

```yaml
adapters:
  - name: safe_user_query
    command: sqlite3
    args: ["{{db_file}}", "SELECT * FROM users WHERE role = '{{role|sql}}' LIMIT {{limit|int}}"]
    timeout: 10
    env_allowlist: ["HOME"]
```

## **Future Architecture Evolution**

### **KERN Compiler Layer**

```
YAML Rules → KERN IR → Target Code
             ↓
         [WASM Binary]
         [Native Code]  
         [JavaScript]
         [Rust Code]
```

**Purpose**: Compile AXIS YAML to native code for maximum performance while preserving determinism

### **MNEME Memory Layer**

```
Git-like Version Control for Logic
├── rules/
│   ├── HEAD → refs/heads/main
│   ├── objects/
│   │   ├── abc123... (rule content)
│   │   └── def456... (rule content)
│   └── refs/heads/main
```

**Purpose**: Version control, rollback, and audit trail for business logic with cryptographic integrity

### **Distributed Execution with Proof**

```
Load Balancer
     ↓
[AXIS Node 1] [AXIS Node 2] [AXIS Node 3]
     ↓             ↓             ↓
Hash=abc123   Hash=abc123   Hash=abc123

# Hash verification ensures consistency across nodes
# Any node producing different hash is automatically flagged
```

## **Design Principles (CALYX-PY)**

### **1. Liability Minimization**
- **~600 LOC total** enforces focus on essentials
- **Zero core dependencies** reduces attack surface
- **Explicit over implicit** makes behavior predictable
- **Pure functions preferred** - side effects isolated to adapters

### **2. Mathematical Guarantees**
- **RFC 8785 canonicalization** provides cross-platform determinism
- **SHA3-256 hashing** gives cryptographic verification
- **Single-pass rule semantics** ensures predictable evaluation
- **Payload-view hashing** separates business logic from audit trails

### **3. Security by Design**
- **Command allowlist** prevents arbitrary code execution
- **Template filters** prevent injection attacks
- **Resource limits** prevent DoS via resource exhaustion
- **AST restrictions** prevent parser bombs and code injection

### **4. Composability Over Monoliths**  
- **Three focused components** instead of one large system
- **Unix pipe compatibility** leverages existing ecosystem
- **JSON as universal interface** enables any-to-any composition
- **Hash chains** provide end-to-end verification

This architecture creates a **computational substrate for the AI era**—simple enough for humans to understand, powerful enough to run any logic, secure enough to trust with sensitive data, and verified enough to prove correctness mathematically.

**AXIS: The nervous system for deterministic computation.** 🚀
