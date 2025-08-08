## CALYX-PY

### *Zero-boilerplate λ-calculus for Python*

***Replace Pydantic / FastAPI / LangChain with YAML + pure functions.***

```python
from calyx.core import validate, RuleEngine, fallback, typecheck
```

### Install
```bash
pip install calyx-py
```

### 60-Second Quickstart

__1) Validate anything__
```python
is_valid, errors = validate(data, {"name": "str", "age": "int?"})
```

__2) Run YAML rules__
```yaml
# rules.yaml
- if: "user.role == 'admin'"
  then: {access: "full"}
- else:
  then: {access: "read"}
```

```python
engine = RuleEngine("rules.yaml")
result = engine.run({"user": {"role": "admin"}})
# {"access": "full"}
```

__3) Add AI fallback (optional)__
```python
@fallback(parse_text, prompt="Extract JSON from: {input}")
def parse_text(text): ...
```

Need an API?
```python
engine.serve()  # Instant HTTP server
```

### Why This Exists

***Pydantic → validate() (one function)***

***FastAPI → RuleEngine().serve() (3 LOC)***

***LangChain → @fallback() (decorator)***

***Mypy → @typecheck() (runtime safety)***

Design Principles

+ 300 LOC — fits in your head

+ 0 hard deps — PyYAML/requests are optional

+ No magic — just Python + YAML

+ Pure reducers — no side effects in logic

+ No eval — safe by default

### For builders who want

✔ UNIX philosophy
✔ Mathematical clarity
✔ Ownership over their stack

***Write the rule in YAML. Solve it in Python. Do effects after.***
