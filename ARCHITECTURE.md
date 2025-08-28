# AXIS Architecture

Deterministic JSON math engine built on λ-calculus + relational algebra.  
**Core loop:** Input JSON → Pipeline Engine → RA Executor → Canonicalize → SHA3-256 Receipts; all side effects are isolated behind Adapters, with O(1) joins via the Structure Registry.

---

## System Overview

```text
Input JSON ─▶ Pipeline Engine ─▶ RA Executor ─▶ Canonicalize ─▶ SHA3-256 Receipts
     │                │                │                 │                 │
     │                │                │                 │                 └─► Audit Hash
     │                │                │                 └─► Sorted Keys / Normalized Numbers
     │                │                └─► σ / π / ⨝ / ∪ / − (RA ops)
     │                └─► YAML Config
     └─► Raw Data

                     ▼
            Structure Registry (O(1) joins, sets, queues)
                     ▼
                 Adapters (controlled side effects)
````

AXIS transforms JSON through deterministic pipelines while maintaining cryptographic audit trails. The RA core runs in isolation; Adapters handle all external I/O at the system boundary.

---

## Execution Model

### α-Conversion (Pipeline Rewriting)

Configuration YAML is normalized before execution:

* Field renaming and path resolution
* Structure reference validation
* Operation dependency ordering
* Canonical form generation for hashing

### β-Style Reduction (Rule Application)

The rule engine applies transformations via fixpoint iteration:

* Conditional logic using **safe AST** parsing
* State updates via pure function application
* Conflict detection and priority-based resolution
* Termination when no further changes occur

### Determinism Guarantee

Every computation is reproducible:

1. **Input canonicalization:** Sort dict keys, normalize numbers
2. **Deterministic step ordering:** Fixed pipeline sequence
3. **Stable hashing:** SHA3-256 over canonical JSON
4. **Receipts:** Verifiable proof of computation (input/config/output/op hashes)

---

## Relational Algebra Operations

### Selection (σ) — Filter Records

Keeps records matching a predicate.

```yaml
# σ(age >= 18)
select: "age >= 18"
# Input:  [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 17}]
# Output: [{"name": "Alice", "age": 25}]
```

### Projection (π) — Select Columns

Extracts specified fields.

```yaml
# π(name, age)
project: ["name", "age"]
```

### Join (⨝) — Combine Relations

Merges records on a common field using a prebuilt structure.

```yaml
# R ⨝(dept_id) S
join:
  on: dept_id
  using: departments   # Structure Registry reference
# Produces left_* and right_* prefixed fields
```

### Union (∪) — Combine Sets

Merges datasets, removing duplicates by canonical record hash.

```yaml
union:
  with:
    - { additional: "data" }
```

### Difference (−) — Set Subtraction

Removes records present in the second dataset.

```yaml
difference:
  using: blocked_users   # Prebuilt set reference
```

### Semi-Join (⋉) — Exists Filter

Keeps records where a field value exists in a reference set.

```yaml
# Keep users in admin whitelist
exists_in:
  field: user_id
  using: admin_whitelist
```

### Anti-Join (⋊) — Not-Exists Filter

Keeps records where a field value does **not** exist in a reference set.

```yaml
# Exclude blocked users
not_exists_in:
  field: user_id
  using: blocked_users
```

### Aggregation (γ) — Group Operations *(in development)*

```yaml
aggregate:
  by: department
  op: sum
  field: salary
```

---

## Structure Registry

Pre-materialized structures provide O(1) operations for large datasets.

### AxisHashMap — Keyed Joins

```python
# Materialized from config
departments = AxisHashMap(
    data=[{"dept_id": "eng", "name": "Engineering"}],
    key_field="dept_id"
)
# O(1) lookup in joins
records = departments.get("eng")  # → matching records
```

### AxisSet — Hash-Based Membership

```python
# Exact record membership
admin_set = AxisSet(data=[{"user": "alice", "role": "admin"}])
is_member = admin_set.contains({"user": "alice", "role": "admin"})

# Field-based membership (semi/anti-joins)
has_user = admin_set.contains_field_value("user", "alice")
```

### AxisQueue — Ordered Streams

```python
event_queue = AxisQueue(data=[{"event": "login", "user": "alice"}])
next_events = event_queue.peek(5)  # get next 5 without removing
```

### Structure Materialization (YAML)

```yaml
structures:
  users_by_id:
    type: hashmap
    key: user_id
    materialize: from_data
    data: [{ user_id: "u1", name: "Alice" }]

  external_data:
    type: set
    materialize: from_file
    source: "./data/blocked_users.json"

  live_data:
    type: queue
    materialize: from_adapter
    adapter:
      command: redis_get
      key: user_events
```

---

## Security & Trust Model

### Safe Expression Evaluation

Predicate expressions use AST-only evaluation with restricted grammar.

```python
ALLOWED_OPS = {
  "eq","noteq","gt","lt","gte","lte","in","notin","and","or","not"
}
# Process:
# 1) Parse to AST
# 2) Validate allowed nodes/ops only
# 3) Evaluate against data context (no code execution)
```

### Canonicalization Rules

Deterministic JSON normalization ensures hash stability:

* **Dictionary keys:** sorted alphabetically
* **Numbers:** int/float normalized consistently
* **Recursive:** applied to nested objects/arrays
* **Non-finite:** reject NaN/Inf values

```python
import math

def canonicalize(obj):
    if isinstance(obj, dict):
        return {k: canonicalize(obj[k]) for k in sorted(obj.keys())}
    elif isinstance(obj, list):
        return [canonicalize(v) for v in obj]
    elif isinstance(obj, (int, float)):
        f = float(obj)
        if not math.isfinite(f):
            raise ValueError("Non-finite numbers not allowed")
        return f
    return obj
```

### SHA3-256 Strategy

Cryptographic hashing yields tamper-evident receipts:

* **Input hash:** canonicalized input data
* **Config hash:** canonicalized pipeline/rules
* **Output hash:** canonicalized results
* **Operations hash:** canonicalized sequence of applied ops

### Audit Receipts

Every computation emits a verifiable audit object.

```json
{
  "_pipe_audit": {
    "pipeline_hash": "a1b2c3d4e5f6...",
    "input_hash": "1a2b3c4d5e6f...",
    "output_hash": "f1e2d3c4b5a6...",
    "steps_executed": 3,
    "structures_used": ["departments", "admin_whitelist"],
    "ra_audit": {
      "operations_count": 5,
      "operations_hash": "9z8y7x6w5v..."
    }
  }
}
```

---

## Extensibility

### Adding New RA Operations

```python
class RelationalAlgebra:
    @staticmethod
    def my_operation(data, config):
        # Implement new RA operation
        return data

def apply_ra_operation(data, operation):
    if "my_operation" in operation:
        return RelationalAlgebra.my_operation(data, operation["my_operation"])
```

### Custom Adapters

```python
def _execute_adapter(self, adapter, data, index, structures_used_log):
    command = adapter.get("command")
    if command == "my_custom_adapter":
        return self._handle_custom_adapter(adapter, data)
```

### Enhanced Structure Types

```python
class AxisCustomStructure:
    def __init__(self, data, config, name="anonymous"):
        self.data = data
        self.config = config
        self.name = name
        self._build_custom_index()
        self.structure_hash = self._generate_hash()

    def custom_operation(self, query):
        # Structure-specific logic
        return []
```

### Richer Type Validation

```python
def _validate(self, data, config):
    for field, type_spec in config.items():
        if type_spec == "custom_type":
            # Custom validation rules
            pass
```

---

## Performance Characteristics

### Time Complexity

* **Selection / Projection:** `O(n)` (n = records)
* **Hash Joins:** `O(n + m)` with structures (vs `O(n*m)` naïve)
* **Set Ops:** `O(n + m)` with hash-based structures
* **Pipelines:** `O(steps * records * op_cost)`

### Space Complexity

* **Structures:** `O(unique_records)` for sets; `O(unique_keys * records_per_key)` for maps
* **Canonicalization:** `O(data_size)` temp buffers
* **Audit:** `O(ops + metadata)` minimal overhead

### Optimization Strategies

* Structure reuse: hash-stable caches across runs
* Early filtering: apply **σ** before expensive joins
* Index lookups: O(1) Structure Registry operations
* (Future) Lazy evaluation & query planning via compilation

---

## Future Layers (Out of Scope Here)

* **MNEME (memory):** append-only audit ledger with incremental verification
* **KERN (compilation):** query/plan compilation to WASM/RISC-V targets




