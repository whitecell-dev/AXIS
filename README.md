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

Tags: yaml validation LLM reasoning cli minimal
