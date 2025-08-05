# ⚡ CALYX-PY: Python Without the Ceremony

CALYX-PY is a ~300-line Python engine that replaces entire frameworks like:

| Framework     | Replaced By            |
|---------------|------------------------|
| ✅ Pydantic    | `validate()`           |
| ✅ FastAPI     | `RuleEngine().serve()` |
| ✅ LangChain   | `@fallback()`          |
| ✅ Mypy        | `@typecheck()`         |

It brings **UNIX philosophy** to modern Python:
> *Do one thing well. Pipe everything. Be auditable.*
---
# 💎 Why ChatGPT Plus Subscribers Should Use CALYX-PY in Every Project

If you have a ChatGPT Plus plan, you already have a full Python IDE in your browser — you just didn’t realize it.

CALYX-PY is the unlock.

✅ What You Get When You Paste core.py into ChatGPT:
|Capability|With CALYX-PY|	Without CALYX-PY|
|----------|-------------|------------------|
|Validate input|	validate()|	Manually, error-prone|
|Run decision logic|	RuleEngine()|	Prompt spaghetti|
|Serve an API|	.serve()|	Not possible
|Fix broken functions|	@fallback()|	Trial-and-error|
|Enforce types|	@typecheck()|	Hope and prayer|

    One file turns ChatGPT from a chatbot into a dev environment.

Why It’s Like Docker (But for Reasoning)

Docker said:

    "Here’s a Dockerfile. Run this app anywhere."

CALYX-PY says:

    "Here’s core.py. Run this logic anywhere — even inside GPT."

Both are:

    Self-contained

    Portable

    Deterministic

    Developer-first

But CALYX-PY is even easier to share — because it runs in a paste box, not a container runtime.

🔌 Use CALYX-PY in Your Own GPT Projects

If you’re building your own ChatGPT GPTs or assistants:

    Add core.py as a preloaded file

    Let users paste YAML or JSON

    Use RuleEngine to run logic and fallback() to handle errors

You’ve just created a logic-based GPT app — without a backend.

✨ Why This Is Different

| Feature              | ChatGPT Alone | ChatGPT + CALYX-PY     |
|----------------------|----------------|--------------------------|
| Static analysis      | ❌             | ✅ `@typecheck()`        |
| Input validation     | ❌             | ✅ `validate()`          |
| Rule-based logic     | ❌             | ✅ `RuleEngine()`        |
| HTTP APIs            | ❌             | ✅ `.serve()`            |
| Self-healing logic   | ❌             | ✅ `@fallback()`         |


You’re not just pasting code.
You’re extending ChatGPT’s core capabilities.

🧩 Use CALYX-PY in:

    GPTs that make decisions from user inputs

    Internal tools that need logic trees or fallback

    Shared prompts that validate + explain answers

    Education projects that teach YAML-based thinking

    Offline AI kits that work without cloud

🛠 How to Add CALYX-PY to Your Project

    Add /calyx/core.py to your GPT or repo

    Let users paste it into any GPT thread

    Share logic via YAML + JSON

    Call .serve() or @fallback() as needed

That’s it.

    Every ChatGPT Plus user now has a programmable reasoning engine.
    CALYX-PY is the bootloader.

---

## ✅ Turn ChatGPT Into a Live IDE — Right Now

You can **run CALYX-PY entirely inside ChatGPT**. No terminal. No pip. No VS Code. Just paste and go.

### 🧪 Try it:

1. Copy the full `core.py` (in `/calyx/`)
2. Paste it into a new ChatGPT thread
3. Then paste this prompt:

````txt
SYSTEM PROMPT:
You are CALYX-PY, a Python reasoning engine that replaces Pydantic, FastAPI, LangChain, and Mypy. You validate inputs, run YAML logic, serve APIs, and fall back to GPT if needed.

USER PROMPT:
Here’s CALYX-PY (pasted above). Now:
1. Validate: {"name": str, "age": int}
2. Apply: if age ≥ 21 → "adult", else → "minor"
3. Serve on port 8080
4. Give a curl test

💡 Output You'll Get:

from calyx import RuleEngine

rules = {
  "rules": [
    {"if": "age >= 21", "then": {"group": "adult"}},
    {"else": None, "then": {"group": "minor"}}
  ]
}

engine = RuleEngine(rules)
engine.serve(port=8080)

curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{"name": "Jess", "age": 19}'
# → {"group": "minor"}
````
Why CALYX-PY Works

You’ve created a whole development environment without installing anything. Why?

Because it’s built on a magic loop:

    Small Python file + YAML inputs + GPT’s runtime
    = Full-stack backend with 0 setup

This is not a trick. It’s a new programming model:

    🧱 Python becomes the logic kernel

    🧠 GPT becomes the executor and fallback

    🧾 YAML becomes the programming language

Key Features
### 1. validate() — Goodbye, Pydantic

    is_valid, errors = validate(data, {"name": "str", "age": "int", "email": "str?"})

Supports optional fields (?)

Auto-coerces types

Works with inline dicts or YAML files

### 2. @typecheck() — Runtime Type Safety

    @typecheck({"x": "int", "y": "int"})
    def add(data): return data["x"] + data["y"]

Lightweight and strict

Great for mini-pipelines and agents

### 3. @fallback() — AI Auto-Fix When Needed

    @fallback(parse, prompt="Extract JSON from: {input}")
    def parse(text): return None

GPT is only called if your function fails

Prompt templating built-in

### 4. RuleEngine() — YAML Logic as Code

    engine = RuleEngine("rules.yaml")
    print(engine.run({"age": 25}))
    engine.serve(port=8000)  # Instant API!

If/then/else rules with safe evaluation

JSON/YAML in, JSON out

No decorators, no boilerplate

Replace This: 

|Old Way (Framework)|New Way (CALYX-PY)|
------------------------------------------
|30 lines of Pydantic|validate(...)|
|Flask/FastAPI route|serve()|
|LangChain chains|@fallback()|
|MyPy/Typescript|@typecheck()|

🛡️ Design Principles

    🧼 Minimal Dependencies (pyyaml, requests optional)

    📦 Standard Library First (http.server)

    🧪 Clear Error Messages

    🔐 Safe Eval (blocks import, __, etc.)

    📋 Self-contained: no class bloat, no black magic

🚀 Ready to Play?

    Want to skip the manual paste?

Try the official CALYX-PY Bootloader GPT Paste your rules, data, or logic — and build from there.

🤔 Skeptical? We are too.So we wrote [README.rebuttal.md](https://github.com/whitecell-dev/CALYX-PY/blob/main/README.rebuttal.md)

...and the 95 Theses of CALYX — [as nailed to the Wittenberg Door of modern Python.](https://github.com/whitecell-dev/CALYX-PY/blob/main/The95ThesesofCALYX-PY.md)

Tags: yaml validation AI no-install cli minimal agent logic reasoning
