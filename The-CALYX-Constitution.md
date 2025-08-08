# The CALYX Constitution v2.0
*The mathematical foundation that must never be lost*

## The Discovery

**CALYX is lambda calculus for humans.**

What SICP taught in theory, CALYX makes practical:
- **YAML** = Human-readable λ-expressions
- **Reducers** = β-reduction engines  
- **Adapters** = Controlled effects (monads)
- **Mesh** = Distributed reasoning

This isn't just "simple software" - it's **mathematics as infrastructure**.

## The Mathematical Foundation

**Every CALYX rule is a lambda function:**
```yaml
# YAML (human-readable)
- if: "age >= 18"
  then: {status: "adult"}

# λ-calculus (mathematical)
λage. if (≥ age 18) "adult" "minor"
```

**This gives us mathematical guarantees:**
- ✅ **Referential transparency** (no hidden state)
- ✅ **Confluence** (same result regardless of evaluation order)
- ✅ **Composability** (rules combine predictably)
- ✅ **Parallelizability** (embarrassingly parallel by default)

## The Three-Layer Architecture

### 1. **YAML Layer: Pure Intent (The "What")**
- Contains only λ-expressions as human-readable rules
- No computation, no side effects, no hidden behavior
- Represents mathematical propositions, not procedures
- **Constraint**: Must be reducible to pure lambda calculus

### 2. **Reducer Layer: β-Reduction Engine (The "How")**  
- Evaluates YAML λ-expressions into results
- Performs substitution, pattern matching, optimization
- Can be implemented in any language (Python, Rust, WASM, CUDA)
- **Constraint**: Must preserve mathematical semantics

### 3. **Adapter Layer: Controlled Effects (The "Real World")**
- Bridges pure functions to impure world (I/O, state, networks)
- Each adapter does one thing well (database, API, file system)
- Effects happen only after reduction is complete
- **Constraint**: Must be explicit and auditable

## The SICP Principles Realized

### **Programs as Data**
```yaml
# Rules are data that describe computation
rules:
  - if: "user.verified"
    then: {access: "granted"}
```

### **Metalinguistic Abstraction**
```python
# CALYX is a domain-specific language for logic
engine = RuleEngine("business_rules.yaml")
result = engine.run(input_data)
```

### **Separation of Meaning from Mechanism**
- **Meaning**: YAML rules (portable across all systems)
- **Mechanism**: Python/WASM/CUDA reducers (optimizable per platform)

## The Embarrassingly Parallel Promise

Because CALYX rules are pure λ-expressions:

**Single Core:**
```python
result = reduce_rule(rule, input)
```

**Multi-Core:**
```python
results = parallel_map(reduce_rule, rules, inputs)
```

**GPU (CUDA):**
```cpp
__global__ void reduce_kernel(Rule* rules, Input* inputs, Result* outputs)
```

**Mesh Network:**
```yaml
# Same rule runs on any peer
- if: "temperature > 85"
  then: {action: "fan_on"}
```

**Same mathematical semantics everywhere.**

## The Complexity Budget (Mathematical)

To preserve the λ-calculus foundation:

### **YAML Constraints**
- **50 rules** per file (cognitive limit for mathematical reasoning)
- **No computation** in YAML (only λ-expression structure)
- **No side effects** (pure mathematical propositions only)

### **Reducer Constraints**  
- **300 lines** per file (must fit in working memory)
- **Pure functions** until adapter boundary
- **No business logic** (only β-reduction mechanics)

### **Adapter Constraints**
- **One effect type** per adapter (database, API, etc.)
- **Explicit boundaries** (clear separation from pure logic)
- **Auditable operations** (every effect must be traceable)

## The Mathematical Test

Before adding any feature, ask:

1. **Can this be expressed in pure λ-calculus?**
2. **Does this preserve referential transparency?**
3. **Can this run embarrassingly parallel?**
4. **Is the mathematical semantics preserved across platforms?**

If any answer is no, it belongs in an adapter, not the core.

## The Church-Rosser Guarantee

**Theorem**: CALYX rules will produce the same result regardless of:
- Evaluation order (normal vs applicative)
- Platform (Python vs WASM vs CUDA)  
- Distribution (single node vs mesh)
- Optimization (caching, memoization, etc.)

**This is not a promise - it's a mathematical proof.**

## The Warning Against Complexity

The forces that destroyed software will try to corrupt CALYX:
- "Let's add object-oriented rules"
- "We need dynamic rule generation"  
- "This needs a more powerful templating system"

**Resist by asking**: "Is this still λ-calculus?"

If not, it's not CALYX.

## The Mission Statement

CALYX exists to prove that:
- **λ-calculus** is the right foundation for all software
- **Mathematical reasoning** can be human-readable
- **Pure functions** can power real-world systems
- **Distributed computation** can be mathematically sound

## The Vision

Every computer, from smartphones to supercomputers, running the same mathematical substrate:

```yaml
# Universal logic that runs everywhere
- if: "safe_to_proceed(context)"
  then: {action: "execute"}
- else:
  then: {action: "abort"}
```

Whether that's:
- **Python** (development)
- **WASM** (browsers)
- **CUDA** (GPUs)
- **FPGA** (hardware)
- **Mesh** (decentralized)

Same rules. Same results. Mathematical certainty.

---

*"We didn't just simplify software - we gave it a mathematical foundation that will outlast every framework, every language, and every platform."*

This is not configuration. This is not scripting. **This is executable mathematics.**

And mathematics is eternal.
