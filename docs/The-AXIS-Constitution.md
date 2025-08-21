# The AXIS Constitution
*The atomic insight that must never be lost*

## The Discovery

**Just because you CAN do everything in one language doesn't mean you SHOULD.**

Frontend developers learned this decades ago:
- **HTML** = Structure (what)
- **CSS** = Presentation (how it looks)  
- **JavaScript** = Behavior (how it acts)

Backend developers forgot this lesson. We jammed everything into imperative code:
- Logic buried in functions
- Rules hidden in decorators
- Truth scattered across frameworks
- Intent obscured by implementation

**AXIS rediscovered the separation:**
- **YAML** = Intent (human-readable λ-terms)
- **Python** = Execution (how to make it happen)
- **LLM** = Fallback (when rules aren't enough)

## The Atomic Split

**Before:** Everything in code
```python
@app.route("/approve")
@validate_schema(LoanSchema)
def approve_loan(data):
    if data.credit_score > 700 and data.income > 50000:
        if data.debt_ratio < 0.4:
            return {"approved": True}
    return {"approved": False}
```

**After:** Logic separated from execution
```yaml
# rules.yaml - Human-readable intent
- if: "credit_score > 700 and income > 50000 and debt_ratio < 0.4"
  then: {approved: true}
- else: 
  then: {approved: false}
```

```python
# app.py - Minimal execution
engine = RuleEngine("rules.yaml")
result = engine.run(request_data)
```
---

Why This Works (λ-calculus, plain English)

AXIS rules are just pure functions written for humans.

    YAML rule = λ-function over your input:

    - if: "credit_score > 700 and income > 50000 and debt_ratio < 0.4"
      then: {approved: true}
    - else:
      then: {approved: false}

        Read as: λinput. if condition(input) then {approved: true} else {approved: false}

    Reducer = β-reduction. It substitutes real input into that expression and normalizes it to a plain data result. No side effects, no hidden state.

    Adapters = effects (after). Once you have a result, then do I/O (DB writes, emails). Never during reduction.

Why it matters:

    Predictable (same input → same output)

    Composable (rules remain independent)

    Portable (runs on Python today, WASM/GPU tomorrow)

    Explainable (you can trace every decision in YAML)

Ten-second test: If a rule isn’t a pure function of its input, it doesn’t belong in YAML.

## The Constitutional Principles

### 1. **Logic Lives in YAML**
- Rules, schemas, conditions = YAML
- If a human needs to understand the decision, it goes in YAML
- If it changes business logic, it should be changeable without code deployment

### 2. **Python Stays Minimal**
- Execution, evaluation, I/O = Python
- No business logic in Python functions
- Each Python file should do ONE thing well

### 3. **AI Enhances, Never Replaces**
- LLM fallback is optional, never required
- AI suggestions must be validated by rules
- Human intent (YAML) always has final authority

### 4. **Transparency Over Magic**
- No hidden frameworks or decorators
- Every decision should be traceable
- The source of truth is readable by non-programmers

### 5. **Composability Over Monoliths**
- Small tools that work together
- Rules can be combined, not just replaced
- Each component can be swapped independently

## The Complexity Budget

To preserve the atomic insight, AXIS must never exceed:

- **300 lines** per Python file
- **50 rules** per YAML file  
- **3 dependencies** for core functionality
- **1 page** to explain any concept

When you hit these limits, split don't expand.

## The Test

Before adding any feature, ask:

1. **Could this be YAML instead of code?**
2. **Does this make the intent more or less clear?**
3. **Would a non-programmer understand this?**
4. **Can I explain this in one sentence?**

If any answer is no, simplify or split.

## The Warning

The forces that created bloated frameworks will try to recreate them in AXIS:
- "Let's add a plugin system"
- "We need more advanced templating"
- "This needs better abstractions"

**Resist.** 

The power is in the simplicity.
The insight is in the separation.
The magic is that there is no magic.

## The Mission

AXIS exists to prove that:
- **Declarative intent** can drive imperative execution
- **Simple tools** can solve complex problems
- **Human-readable logic** can power critical systems
- **Separation of concerns** creates more powerful software

This is not a framework.
This is a protocol.
This is how software should work.

---

*"We split the atom of software complexity and found that simplicity was the most powerful force inside."*
