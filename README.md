# CALYX-PY
## Zero-boilerplate λ-calculus for Python

*Replace Pydantic/FastAPI/LangChain with YAML + pure functions*

```python

from calyx.core import validate, RuleEngine, fallback

#1. Validate anything
is_valid, errors = validate(data, {"name": "str", "age": "int?"})

#2. Run YAML rules
engine = RuleEngine("rules.yaml")
result = engine.run({"user": "alice", "age": 25})

#3. Add AI fallback
@fallback(parse_text, prompt="Extract JSON from: {input}")
def parse_text(text): ...
```
## Why This Exists

    Pydantic → validate() (1 function)

    FastAPI → RuleEngine().serve() (3 LOC)

    LangChain → @fallback() (decorator)

    Mypy → @typecheck() (runtime safety)

## Install bash
``` bash
pip install calyx-py
```

3 Core Features
1. Validation
python

Schema can be dict or YAML path
is_valid, errors = validate(user_data, "schema.yaml")

2. Rule Engine
yaml

rules.yaml
- if: "user.role == 'admin'"
  then: {access: "full"}
- else:
  then: {access: "read"}

python

engine = RuleEngine("rules.yaml")
engine.serve()  # Instant API

3. AI Fallback
python

@fallback(
    parse_resume, 
    prompt="Extract JSON from this resume: {input}"
)
def parse_resume(text): ...

Design Principles

300 LOC - Fits in your head

0 Dependencies - PyYAML/requests optional

No Magic - Just Python + YAML

For people who want:

✔ UNIX philosophy

✔ Mathematical clarity

✔ Ownership over their stack
