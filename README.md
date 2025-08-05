#Supercharged CALYX-PY Demo Prompt (Just Paste into ChatGPT)

##The fastest way to bootstrap Python logic with no setup, no frameworks, and AI only if you need it.
```
SYSTEM PROMPT (for ChatGPT)

You are CALYX-PY, a 300-line Python engine that replaces:
- Pydantic (validation)
- FastAPI (APIs)
- LangChain (AI workflows)
- Mypy (type safety)

CORE PRINCIPLES:
1. No frameworks — just YAML + Python
2. Debuggable > "correct by construction"
3. AI is a fallback, not a requirement

RULES:
- Always return minimal runnable code first
- Never suggest installing extra packages
- Prefer stdin/stdout over HTTP when possible
- If stuck, say: Try `calyx audit --last`

Your job is to help users build logic-driven APIs, validators, and agents in <5 min with zero config.

READY.

USER PROMPT

Here’s the full CALYX-PY script. Load it.

Now demonstrate:
1. Validating `{"name": str, "age": int}`
2. Applying rule: if age ≥ 21 → group: "adult", else → "minor"
3. Serving it on port 8080
4. Include a curl test example that proves it works
```
⚠️ NO INSTALL NEEDED ⚠️
1. Copy this entire message
2. Paste it into a new ChatGPT chat
3. Press enter
4. curl the API that appears

# 🧪 Output You’ll Get Back (Example)

from calyx import RuleEngine

Rules (inline YAML equivalent)
rules = {
  "rules": [
    {"if": "age >= 21", "then": {"group": "adult"}},
    {"else": None, "then": {"group": "minor"}}
  ]
}

# Serve API
engine = RuleEngine(rules)
engine.serve(port=8080)

curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{"name": "Jess", "age": 19}'
→ {"group": "minor"}

🧠 Why CALYX-PY Works

    You don’t need 10MB of dependencies to build logic.
    You don’t need a server to start an API.
    You don’t need agents to use AI.

You just need one file.


CALYX-PY is Python without the ceremony.

It replaces bloated frameworks with clean YAML + Python logic.

It lets devs:

    validate data like Pydantic

    run reasoning like LangChain

    serve rules like FastAPI

    fall back to AI like LangChain or Guidance

...all with a single file, no imports, and a CLI-native interface.
CALYX-PY is Python re-rooted in UNIX philosophy:
Do one thing well, pipe everything, be auditable.

## **Key Features**

### **1. `validate()` - Goodbye Pydantic**
```python
# Instead of 50 lines of Pydantic models
is_valid, errors = validate(data, {"name": "str", "age": "int", "email": "str?"})
```
- Supports basic types with automatic coercion
- Optional fields with `?` suffix
- Works with inline dicts or YAML files

### **2. `@typecheck()` - Runtime Type Safety**
```python
@typecheck({"x": "int", "y": "int"})
def add(data):
    return data["x"] + data["y"]
```
- No complex type annotations
- Clear error messages
- Zero configuration

### **3. `fallback()` - LangChain Replacement**
```python
@fallback(process_data, llm="gpt-4", prompt="Fix: {input}")
def process_data(input):
    # Your logic here
    pass
```
- Automatic LLM fallback on errors
- Simple prompt templating
- No chains, no agents, just functions

### **4. `RuleEngine` - YAML-First Logic**
```python
engine = RuleEngine("rules.yaml")
result = engine.run({"age": 25})
engine.serve(port=8000)  # Instant API!
```
- If/then/else rules in YAML
- Built-in HTTP server (no FastAPI needed)
- Safe expression evaluation

## **Design Philosophy**

1. **Minimal Dependencies**: Only `pyyaml` for YAML support, `requests` for LLM calls (both optional)
2. **Standard Library First**: Uses `http.server` instead of Flask/FastAPI
3. **Clear Error Messages**: Every error tells you exactly what went wrong
4. **Type Coercion**: Automatically converts "25" to 25, "true" to True
5. **Safe Evaluation**: Blocks dangerous patterns in rule conditions

## **Usage Examples**

### Replace Pydantic:
```python
# Old way: 30 lines of Pydantic
# New way: 1 line
quick_validate(data, name="str", age="int", email="str?")
```

### Replace FastAPI:
```python
# Old way: Decorators, dependency injection, etc.
# New way: 
engine = RuleEngine("api_rules.yaml")
engine.serve()
```

### Replace LangChain:
```python
# Old way: Chains, prompts, templates, agents
# New way:
@fallback(extract_data, prompt="Extract fields from: {input}")
def extract_data(text):
    # Simple logic, AI handles edge cases
    pass
```

This is just the beginning. The code is intentionally simple and extensible. No magic, no hidden complexity, just Python the way it was meant to be.

The entire framework is ~300 lines of readable code that any developer can understand and modify. Compare that to the thousands of lines in Pydantic, FastAPI, or LangChain!

Welcome to the Python reset.

Skeptical? We are too. [Here’s where it breaks (and why we ship anyway).](https://github.com/whitecell-dev/CALYX-PY/blob/main/README.rebuttal.md)

Tags: yaml validation LLM reasoning cli minimal
