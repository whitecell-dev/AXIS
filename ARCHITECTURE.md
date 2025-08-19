# AXIS Architecture

**React for Deterministic Reasoning**

## Philosophy: CALYX-PY

- **Every line of code is a liability until proven otherwise**
- **Keep only what's necessary for YAML → AST → Pure Reducer pipeline**
- **Replace "magic" with explicit, predictable code**
- **The result should be ~400 LOC, readable in one sitting**

## Core Pipeline

```
YAML Rules → AST Parser → Pure Reducer → Cryptographic Hash
     ↑           ↑            ↑              ↑
  Human       Security     React         Verification
 Readable    Validated   Patterns       Mathematical
```

## Package Structure (~400 LOC Total)

```
axis/
├── __init__.py              # Main exports (15 LOC)
├── engine/                  # Pure logic core (150 LOC)
│   ├── rule_engine.py       # Main RuleEngine class (60 LOC)
│   ├── ast.py              # Secure condition parser (50 LOC)
│   ├── reducer.py          # React-style reducer (25 LOC)
│   └── hash.py             # Cryptographic verification (15 LOC)
├── adapters/               # I/O boundaries (100 LOC)
│   ├── database.py         # SQLite adapter (60 LOC)
│   └── http.py            # HTTP client (40 LOC)
├── cli/                   # Simple commands (100 LOC)
│   ├── main.py            # CLI entry point (30 LOC)
│   └── commands/          # Individual commands (70 LOC)
├── integrations/          # Framework bridges (50 LOC)
│   ├── flask.py           # Flask decorator (25 LOC)
│   └── fastapi.py         # FastAPI dependency (25 LOC)
├── testing/               # Golden vectors (50 LOC)
│   └── test_runner.py     # Cross-platform verification
└── utils/                 # Validation helpers (50 LOC)
    └── validator.py       # Type checking/coercion
```

## Key Design Principles

### 1. **Pure Functions Everywhere**
```python
# React-inspired reducer pattern
def apply_rules(rules: List[dict], state: dict, action: dict) -> dict:
    # Always returns new state, never mutates input
    new_state = json.loads(json.dumps(state))  # Deep copy
    # ... apply changes deterministically
    return new_state
```

### 2. **Security-First AST**
```python
# Only whitelisted operations allowed
ALLOWED_OPS = {
    'eq', 'noteq', 'gt', 'lt', 'gte', 'lte', 'in', 'notin',
    'and', 'or', 'not'
}
```

### 3. **Cryptographic Verification**
```python
def canonicalize(obj: Any) -> Any:
    # Deterministic serialization for cross-platform hashing
    if isinstance(obj, dict):
        return {k: canonicalize(obj[k]) for k in sorted(obj.keys())}
    # ...

ir_hash = sha3_256_hex(canonical_json)  # Content addressing
```

### 4. **Zero Dependencies Core**
- Uses only Python stdlib for core functionality
- Optional dependencies for YAML, web frameworks
- Easy to port to other languages

### 5. **Controlled I/O Boundaries**
```python
# Adapters isolate side effects from pure logic
class DatabaseAdapter(ABC):
    @abstractmethod
    def save(self, table: str, data: Dict[str, Any]) -> Any:
        pass
```

## Why This Architecture Works

### **Simplicity**
- Each module has a single, clear responsibility
- No complex inheritance hierarchies or design patterns
- Linear flow: YAML → AST → Reducer → Hash

### **Testability**
- Pure functions are easy to test
- Golden vector testing ensures cross-platform consistency
- Deterministic execution means predictable behavior

### **Portability**
- Minimal code surface area makes porting straightforward
- Clear separation between logic (engine) and I/O (adapters)
- Hash-based verification ensures identical behavior across platforms

### **Security**
- AST whitelist prevents code injection
- No eval() or dynamic execution
- Controlled execution environment

### **Maintainability**
- ~400 LOC total means one person can understand the entire system
- Clear module boundaries
- Self-documenting through minimal, focused code

## Extension Points

### **New Adapters**
```python
class S3Adapter(DatabaseAdapter):
    def save(self, bucket: str, data: Dict[str, Any]) -> str:
        # Implement S3 storage
```

### **New Framework Integrations**
```python
def with_axis_rules_django(yaml_path: str):
    # Django decorator following same pattern as Flask
```

### **New AST Operations**
```python
# Add to ALLOWED_OPS after security review
ALLOWED_OPS.add('startswith')  # String operations
```

## Performance Characteristics

- **Cold start**: ~1ms (minimal imports)
- **Rule execution**: ~10μs per rule (Python)
- **Memory**: ~1MB baseline + rule data
- **Scaling**: Linear with number of rules

## Cross-Platform Verification

```bash
# Generate golden vectors in Python
axis test rules.yaml vectors.json

# Future: Verify in JavaScript, WASM, Rust
# Same hash = mathematically identical behavior
```

This architecture achieves the CALYX-PY goal: **maximum functionality with minimum complexity**, creating a system that's both powerful and comprehensible.
