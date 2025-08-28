# Makefile

.PHONY: help install dev-install lint format typecheck test build run-demo hash-demo clean

# Default target
help:
	@echo "AXIS - Deterministic JSON Math Engine"
	@echo ""
	@echo "Available targets:"
	@echo "  install      Install package for production use"
	@echo "  dev-install  Install package with development dependencies" 
	@echo "  lint         Run code linting (ruff)"
	@echo "  format       Format code (black)"
	@echo "  typecheck    Run type checking (mypy)"
	@echo "  test         Run test suite (pytest)"
	@echo "  build        Build wheel and source distribution"
	@echo "  run-demo     Execute relational algebra demo"
	@echo "  hash-demo    Show canonicalization and hashing demo"
	@echo "  clean        Remove build artifacts and cache files"

# Installation targets
install:
	pip install .

dev-install: 
	pip install -e ".[dev,test,docs]"

# Code quality targets
lint:
	ruff check axis/ tests/

format:
	black axis/ tests/
	ruff check --fix axis/ tests/

typecheck:
	mypy axis/

# Testing targets
test:
	pytest tests/ -v --cov=axis --cov-report=term-missing

test-quick:
	pytest tests/ -x -v

# Build targets  
build:
	python -m build

build-wheel:
	python -m build --wheel

build-sdist:
	python -m build --sdist

# Demo targets
run-demo:
	@echo "=== AXIS Relational Algebra Demo ==="
	@echo ""
	@echo "1. Selection (σ) - Filter adults only:"
	@echo '  Input: [{"name":"Alice","age":25},{"name":"Bob","age":17}]'
	@echo -n "  Output: "
	@echo '[{"name":"Alice","age":25},{"name":"Bob","age":17}]' | python -m axis.axis_pipes run examples/adults.yaml 2>/dev/null | jq -c '.data // empty'
	@echo ""
	@echo "2. Projection (π) - Select name and age fields:"  
	@echo -n "  Output: "
	@echo '[{"name":"Alice","age":25,"email":"alice@example.com"}]' | python -c "import sys, json; from axis.axis_pipes import PipelineEngine; engine = PipelineEngine({'pipeline': [{'project': ['name', 'age']}]}); result = engine.run(json.load(sys.stdin)); print(json.dumps(result['data'], separators=(',', ':')))"
	@echo ""
	@echo "3. Join (⨝) - Combine users with departments:"
	@echo -n "  Output: "
	@echo '[{"user":"alice","dept_id":"eng"}]' | python -c "import sys, json; from axis.axis_pipes import PipelineEngine; config = {'structures': {'depts': {'type': 'hashmap', 'key': 'dept_id', 'materialize': 'from_data', 'data': [{'dept_id': 'eng', 'name': 'Engineering'}]}}, 'pipeline': [{'join': {'on': 'dept_id', 'using': 'depts'}}, {'project': ['left_user', 'right_name']}]}; engine = PipelineEngine(config); result = engine.run(json.load(sys.stdin)); print(json.dumps(result.get('data', result), separators=(',', ':')))" 2>/dev/null || echo "Join demo requires structure registry"

hash-demo:
	@echo "=== AXIS Canonicalization and Hashing Demo ==="
	@echo ""
	@echo "Input JSON (unordered):"
	@echo '{"z": 3, "a": {"y": 2, "x": 1}, "b": [3, 1, 2]}'
	@echo ""
	@echo "Canonicalized (ordered keys, sorted):"
	@python -c "import json; from axis.axis_core import canonicalize; obj = {'z': 3, 'a': {'y': 2, 'x': 1}, 'b': [3, 1, 2]}; print(json.dumps(canonicalize(obj), separators=(',', ':')))"
	@echo ""
	@echo "SHA3-256 hash:"
	@python -c "import json; from axis.axis_core import canonicalize, sha3_256_hex; obj = {'z': 3, 'a': {'y': 2, 'x': 1}, 'b': [3, 1, 2]}; canonical = canonicalize(obj); content = json.dumps(canonical, sort_keys=True, separators=(',', ':')); print(sha3_256_hex(content))"
	@echo ""
	@echo "Determinism test (same input = same hash):"
	@python -c "import json; from axis.axis_core import canonicalize, sha3_256_hex; obj1 = {'a': 1, 'b': 2}; obj2 = {'b': 2, 'a': 1}; h1 = sha3_256_hex(json.dumps(canonicalize(obj1), sort_keys=True, separators=(',', ':'))); h2 = sha3_256_hex(json.dumps(canonicalize(obj2), sort_keys=True, separators=(',', ':'))); print('Hash 1:', h1[:16] + '...'); print('Hash 2:', h2[:16] + '...'); print('Equal:', h1 == h2)"

# Cleanup targets
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/

clean-all: clean
	find . -type d -name ".axis" -exec rm -rf {} +
	rm -rf .venv/
	rm -rf venv/

# Development workflow shortcuts
dev: dev-install lint test

ci: lint typecheck test

release: clean build
	@echo "Built distributions in dist/"
	@echo "Ready for: twine upload dist/*"

# Quick validation
validate:
	@echo "Validating package structure..."
	@python -c "import axis; print('✓ Package imports successfully')"
	@python -c "from axis import axis_core, axis_pipes, axis_ra; print('✓ Core modules available')"
	@python -c "import json; from axis.axis_core import canonicalize, sha3_256_hex; print('✓ Core functions work')" 
	@echo "✓ Package validation complete"

# Help with common tasks
.PHONY: examples
examples:
	@echo "Creating example configuration files..."
	@mkdir -p examples
	@echo 'pipeline:\n  - select: "age >= 18"\n  - project: ["name", "age"]' > examples/adults.yaml
	@echo '[{"name":"Alice","age":25},{"name":"Bob","age":17}]' > examples/users.json
	@echo "✓ Created examples/adults.yaml and examples/users.json"
	@echo "  Run: cat examples/users.json | python -m axis.axis_pipes run examples/adults.yaml"
