# AXIS: Deterministic JSON Math Engine

> **“LLMs guess; AXIS proves.”**

AXIS is a deterministic “left brain” that executes human-readable **YAML/JSON pipelines** using **relational algebra** and **λ-calculus** principles. While LLMs excel at probabilistic creativity, AXIS provides the mathematical certainty needed to collapse fuzziness into verifiable facts. Every computation produces **cryptographic receipts (SHA3-256)** for full audit trails.

Built on relational algebra primitives (**σ** selection, **π** projection, **⨝** joins, **∪** union, **−** difference) with controlled side-effects through adapters, AXIS transforms JSON data streams **deterministically** while maintaining **Unix composability**.

---

## Table of Contents

- [Why Now?](#why-now)
- [How It Works](#how-it-works)
  - [Data Model](#data-model)
  - [Core Guarantees](#core-guarantees)
- [Quickstart](#quickstart)
  - [Demo 1: Selection (σ) + Projection (π)](#demo-1-selection-σ--projection-π)
  - [Demo 2: Join (⨝)](#demo-2-join-)
- [CLI Commands](#cli-commands)
  - [Pipeline Engine](#pipeline-engine)
  - [Rule Engine](#rule-engine)
  - [Adapters (Controlled Side Effects)](#adapters-controlled-side-effects)
  - [Structure Registry](#structure-registry)
- [Capabilities & Roadmap](#capabilities--roadmap)
- [Safety & Sandboxing](#safety--sandboxing)
  - [Expression Security](#expression-security)
  - [Adapter Isolation](#adapter-isolation)
- [Design Principles](#design-principles)
- [Installation](#installation)
- [License](#license)
- [FAQ](#faq)

---

## Why Now?

Stacking probability on probability is fragile. Modern AI workflows need a deterministic foundation that can:

- **Verify LLM outputs** with mathematical certainty  
- **Audit complex data transformations** with cryptographic receipts  
- **Compose reliably** across systems and time  
- **Scale reasoning** beyond what fits in context windows  

AXIS provides this mathematical substrate while remaining **human-readable** and **LLM-authorable**.

---

## How It Works

### Data Model

- **Input/Output**: JSON streams (single objects or arrays)  
- **Pipelines**: Human-readable YAML configurations  
- **Operations**: Relational algebra primitives + functional transformations  
- **Receipts**: SHA3-256 hashes of canonicalized computations

### Core Guarantees

- **Deterministic**: Same input + pipeline ⇒ same output + hash  
- **Auditable**: Every operation produces verifiable receipts  
- **Safe**: AST-based predicate evaluation with sandboxed expressions  
- **Composable**: Unix pipes + JSON = universal interface

---

## Quickstart

> The examples below assume the `axis_*` modules are in your Python path. Adjust paths as needed for your repo layout.

### Demo 1: Selection (σ) + Projection (π)

**1) Create `examples/adults.yaml`:**
```yaml
pipeline:
  - select: "age >= 18"       # σ: keep adults
  - project: ["name", "age"]  # π: keep specific fields
````

**2) Run with sample data:**

```bash
echo '[{"name":"Alice","age":25},{"name":"Bob","age":17}]' | \
python -m axis_pipes run examples/adults.yaml
```

**Expected output (truncated for brevity):**

```json
{
  "data": [{"name": "Alice", "age": 25}],
  "_pipe_audit": {
    "pipeline_hash": "a1b2c3...",
    "input_hash": "d4e5f6...",
    "output_hash": "g7h8i9...",
    "ra_audit": { "operations_count": 2 }
  }
}
```

---

### Demo 2: Join (⨝)

**1) Create `examples/user_departments.yaml`:**

```yaml
structures:
  departments:
    type: hashmap
    key: dept_id
    materialize: from_data
    data:
      - { dept_id: "eng",   dept_name: "Engineering" }
      - { dept_id: "sales", dept_name: "Sales" }

pipeline:
  - join:
      on: dept_id
      using: departments      # ⨝ via prebuilt hashmap
  - project: ["left_user", "right_dept_name"]
```

**2) Run with sample data:**

```bash
echo '[{"user":"alice","dept_id":"eng"}]' | \
python -m axis_pipes run examples/user_departments.yaml
```

**Expected output (data section):**

```json
[
  { "left_user": "alice", "right_dept_name": "Engineering" }
]
```

---

## CLI Commands

### Pipeline Engine

```bash
# Run data transformation pipeline
python -m axis_pipes run config.yaml [--input file.json] [--output result.json]

# Validate pipeline without execution
python -m axis_pipes validate config.yaml

# Generate pipeline configuration hash
python -m axis_pipes hash config.yaml

# Dry run (show what would execute)
python -m axis_pipes run config.yaml --dry-run
```

### Rule Engine

```bash
# Apply logical rules with fixpoint iteration
python -m axis_rules apply rules.yaml [--input facts.json]

# Validate rule configuration
python -m axis_rules validate rules.yaml

# Show rule configuration hash
python -m axis_rules hash rules.yaml
```

### Adapters (Controlled Side Effects)

```bash
# Execute external commands with RA pre-filtering
python -m axis_adapters exec adapters.yaml [--input data.json]

# Validate adapter configuration
python -m axis_adapters validate adapters.yaml

# Show what commands would execute
python -m axis_adapters exec adapters.yaml --dry-run
```

### Structure Registry

```bash
# Materialize prebuilt data structures
python -m axis_structures materialize config.yaml

# Show structure information
python -m axis_structures info config.yaml [--structure name]

# Validate structure references
python -m axis_structures validate config.yaml --operations pipeline.yaml
```

---

## Capabilities & Roadmap

### ✅ Ready for Production

* **Relational Algebra**: σ (select), π (project), ⨝ (join), ∪ (union), − (difference)
* **Enhanced Operations**: Semi-join (`exists_in`), anti-join (`not_exists_in`)
* **Structure Registry**: Prebuilt hashmaps, sets, queues with O(1) operations
* **Pipeline Engine**: Multi-step transformations with audit trails
* **Rule Engine**: Conditional logic with fixpoint iteration scaffolding
* **Adapters**: Controlled side effects with timeouts and sandboxing
* **Canonicalization**: Deterministic JSON normalization + SHA3-256 hashing

### 🚧 In Development

* **Aggregation Grammar**: `GROUP BY`, `SUM`, `COUNT`, `AVG` operations
* **Advanced Conflict Resolution**: Priority-based rule application
* **Schema Validation**: Rich type checking and constraints
* **Performance Optimization**: Query planning and index usage

### 🔮 Future (MNEME/KERN Layers)

* Append-only audit ledger with incremental verification
* Query compilation to WASM/RISC-V targets

---

## Safety & Sandboxing

### Expression Security

* **AST-only evaluation**: No `eval()` or dynamic code injection
* **Restricted grammar**: Comparison, logical, and field access operations
* **Safe operators**: `==`, `!=`, `>`, `<`, `>=`, `<=`, `in`, `and`, `or`, `not`

### Adapter Isolation

* **No shell injection**: `shell=False` for all subprocess calls
* **Timeout protection**: 30-second default limits
* **Template safety**: Parameterized substitution prevents injection
* **Audit trails**: Every external command logged with arguments

---

## Design Principles

* **Deterministic Core**: Same input always produces same output (and hash)
* **Human-Readable**: YAML configs readable by both humans and LLMs
* **RA as Periodic Table**: Minimal, complete operator set
* **Unix Philosophy**: JSON streams enable universal composability
* **Verifiable by Default**: Cryptographic receipts for every computation
* **Side-Effect Isolation**: Pure RA core + controlled adapters at edges

---

## Installation

```bash
# Install from PyPI (coming soon)
pip install axis
```

```bash
# Install from source
git clone https://github.com/example/axis.git
cd axis
pip install -e .
```

```bash
# With development dependencies
pip install -e ".[dev,test]"
```

---

## License

MIT License — see `LICENSE` for details.

---

## FAQ

**How does AXIS complement LLMs?**
LLMs excel at pattern recognition and creative synthesis but struggle with logical consistency. AXIS provides a deterministic substrate where LLM outputs can be verified, composed, and audited. Think of it as adding a *mathematical proof checker* to your AI workflow.

**How do I extend the structure registry?**
Create new structure types by inheriting from base classes in `axis_structures.py`. Each structure must implement `to_dict()`, generate deterministic hashes, and support the required RA operations for its type (sets for ∪/−, hashmaps for ⨝).

**How do I test determinism?**
Run the same pipeline multiple times and verify identical output hashes:

```bash
python -m axis_pipes hash config.yaml  # Pipeline config hash
echo '{"test": true}' | python -m axis_pipes run config.yaml | jq '._pipe_audit.output_hash'
```

**Performance characteristics?**
AXIS prioritizes correctness over speed. Expect \~1K–10K records/second for complex pipelines. The structure registry provides O(1) joins for large datasets. A future compilation layer will target high-performance backends.

**Can I use this in production?**
The RA engine and pipeline components are production-ready. Rule engine fixpoint iteration is scaffolded but needs conflict resolution policies for complex scenarios. Adapters should be carefully audited for your security requirements.




