```markdown
# ARCHITECTURE.md

# AXIS Architecture

## System Overview

Input JSON → Pipeline Engine → RA Executor → Canonicalize → SHA3-256 Receipts
↓              ↓              ↓              ↓              ↓
Raw Data    YAML Config    σ/π/⨝/∪/−     Sorted Keys    Audit Hash
↓
Structure Registry (O(1) joins)
↓
Adapters (Controlled Side Effects)

AXIS transforms JSON data through deterministic pipelines while maintaining cryptographic audit trails. The core engine applies relational algebra operations in isolation, with adapters handling all external interactions at the system boundary.

## Execution Model

### α-Conversion: Pipeline Rewriting
Configuration YAML undergoes normalization before execution:
- Field renaming and path resolution
- Structure reference validation  
- Operation dependency ordering
- Canonical form generation for hashing

### β-Style Reduction: Rule Application
The rule engine applies transformations through fixpoint iteration:
- Conditional logic evaluation using safe AST parsing
- State updates through pure function application
- Conflict detection and priority-based resolution
- Termination when no further changes occur

### Determinism Guarantee
Every computation is reproducible:
1. **Input canonicalization**: Sort dictionary keys, normalize numbers
2. **Operation ordering**: Deterministic pipeline step sequence
3. **Hash stability**: SHA3-256 over canonical JSON representation
4. **Receipt generation**: Auditable proof of computation

## Relational Algebra Operations

### Selection (σ) - Filter Records
Keeps records matching a predicate condition.

```yaml
# σ(age >= 18)
select: "age >= 18"

# Against JSON: [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 17}]
# Returns: [{"name": "Alice", "age": 25}]

Projection (π) - Select Columns
Extracts specified fields from records.

# π(name, age)
project: ["name", "age"]

Join (⨝) - Combine Relations
Merges records from two datasets on a common field.
# R ⨝(dept_id) S  
join:
  on: dept_id
  using: departments  # Structure registry reference

Produces records with left_* and right_* prefixed fields from joined datasets.
Union (∪) - Combine Sets
Merges two datasets eliminating duplicates based on record hashes.

union:
  with: [{"additional": "data"}]

Difference (−) - Set Subtraction
Removes records present in the second dataset from the first.

difference:  
  using: blocked_users  # Remove using prebuilt set

Semi-Join (⋉) - Exists Filter
Keeps records where a field value exists in a reference set.

# Keep users in admin whitelist
exists_in:
  field: user_id
  using: admin_whitelist

Anti-Join (⋊) - Not Exists Filter
Keeps records where a field value does NOT exist in a reference set.

# Exclude blocked users
not_exists_in:
  field: user_id  
  using: blocked_users

Aggregation (γ) - Group Operations
Groups records and applies aggregate functions (in development).

# Future syntax
aggregate:
  by: department
  op: sum
  field: salary

Structure Registry
Pre-materialized data structures provide O(1) operations for large datasets.
AxisHashMap
Indexed key-value storage for fast joins.

# Materialized from config
departments = AxisHashMap(
    data=[{"dept_id": "eng", "name": "Engineering"}],
    key_field="dept_id"
)

# O(1) lookup in joins
records = departments.get("eng")  # Returns matching records

AxisSet
Hash-based set operations with field indexing.

# Exact record membership
admin_set = AxisSet(data=[{"user": "alice", "role": "admin"}])
is_member = admin_set.contains({"user": "alice", "role": "admin"})

# Field-based membership for semi/anti-joins  
has_user = admin_set.contains_field_value("user", "alice")

AxisQueue
Ordered data for streaming operations.

event_queue = AxisQueue(data=[{"event": "login", "user": "alice"}])
next_events = event_queue.peek(5)  # Get next 5 without removing

Structure Materialization
Structures are built from various sources:

structures:
  users_by_id:
    type: hashmap
    key: user_id
    materialize: from_data  # Inline data
    data: [{"user_id": "u1", "name": "Alice"}]
    
  external_data:
    type: set
    materialize: from_file  # External JSON file
    source: "./data/blocked_users.json"
    
  live_data:
    type: queue  
    materialize: from_adapter  # Via external command
    adapter:
      command: redis_get
      key: user_events

Security & Trust Model
Safe Expression Evaluation
Predicate expressions use AST-only evaluation with restricted grammar:

# Allowed operations
ALLOWED_OPS = {'eq', 'noteq', 'gt', 'lt', 'gte', 'lte', 'in', 'notin', 'and', 'or', 'not'}

# Safe evaluation process:  
# 1. Parse to AST using Python's ast module
# 2. Validate only allowed node types and operations
# 3. Evaluate against data context without code execution

Canonicalization Rules
Deterministic JSON normalization ensures hash stability:

Dictionary key ordering: Sort keys alphabetically
Number normalization: Convert int/float to consistent float representation
Recursive application: Apply to nested objects and arrays
Non-finite handling: Reject NaN, Infinity values

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

SHA3-256 Strategy
Cryptographic hashing provides tamper-evident receipts:

Input hash: Canonicalized input data
Config hash: Canonicalized pipeline/rule configuration
Output hash: Canonicalized computation results
Operations hash: Canonicalized sequence of applied operations

Audit Receipts
Every computation produces verifiable audit trails:

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

Extensibility
Adding New RA Operations
Extend the RelationalAlgebra class with new primitives:

class RelationalAlgebra:
    @staticmethod
    def my_operation(data, config):
        # Implement new RA operation
        pass

# Register in apply_ra_operation dispatcher
def apply_ra_operation(data, operation):
    if 'my_operation' in operation:
        return RelationalAlgebra.my_operation(data, operation['my_operation'])

Custom Adapters
Create new adapter types for external system integration:

def _execute_adapter(self, adapter, data, index, structures_used_log):
    command = adapter.get('command')
    
    if command == 'my_custom_adapter':
        # Implement custom external interaction
        return self._handle_custom_adapter(adapter, data)

Enhanced Structure Types
Add new structure implementations:

class AxisCustomStructure:
    def __init__(self, data, config, name="anonymous"):
        self.data = data
        self.config = config
        self.name = name
        self._build_custom_index()
        self.structure_hash = self._generate_hash()
    
    def custom_operation(self, query):
        # Implement structure-specific operations
        pass

Richer Type Validation
Extend validation rules in pipeline engine:
def _validate(self, data, config):
    for field, type_spec in config.items():
        if type_spec == "custom_type":
            # Add custom validation logic
            pass

Performance Characteristics
Time Complexity

Selection/Projection: O(n) where n = record count
Hash-based joins: O(n + m) with structure registry, O(n*m) without
Set operations: O(n + m) with hash-based structures
Pipeline execution: O(steps * records * complexity_per_operation)

Space Complexity

Structure registry: O(unique_records) for sets, O(unique_keys * records_per_key) for hashmaps
Canonicalization: O(data_size) temporary storage during normalization
Audit trails: O(operations + metadata) - minimal overhead

Optimization Strategies

Structure reuse: Hash-stable structures cached across pipeline runs
Early filtering: Apply σ operations before expensive joins
Index-based lookups: O(1) structure registry operations
Lazy evaluation: Future KERN compilation will enable query optimization

Future layers (MNEME memory, KERN compilation) will add append-only audit ledgers and compiled query execution for high-performance scenarios.




