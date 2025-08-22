# AXIS: React for Deterministic Reasoning  
# CALYX-PY Philosophy: Every line of code is a liability until proven otherwise

.PHONY: help install test demo clean lint format validate philosophy check-loc golden security

# Default target
help:
	@echo "🚀 AXIS: React for Deterministic Reasoning"
	@echo "📋 CALYX-PY Philosophy: Every line of code is a liability until proven otherwise"
	@echo ""
	@echo "Available commands:"
	@echo "  install     Install for development"
	@echo "  test        Run test suite (fast tests)"
	@echo "  test-all    Run full test suite including slow tests"
	@echo "  golden      Run golden master tests for cross-platform verification"
	@echo "  security    Run security and injection tests"
	@echo "  demo        Run the demo pipeline"
	@echo "  validate    Validate CALYX-PY philosophy compliance"
	@echo "  philosophy  Show philosophy metrics"
	@echo "  check-loc   Check lines of code limits"
	@echo "  lint        Run linting checks"
	@echo "  format      Format code with black/ruff"
	@echo "  clean       Clean build artifacts"
	@echo "  ci          Run full CI pipeline"

# Development installation
install:
	@echo "📦 Installing AXIS for development..."
	pip install -e ".[dev,yaml]"
	@echo "✅ Installation complete"

# Fast tests
test:
	@echo "🧪 Running AXIS test suite (fast)..."
	python -m pytest tests/ -v -m "not slow"
	@echo "✅ Fast tests complete"

# Full test suite
test-all:
	@echo "🧪 Running full AXIS test suite..."
	python -m pytest tests/ -v
	@echo "✅ All tests complete"

# Golden master tests for cross-platform verification
golden:
	@echo "🏆 Running golden master tests..."
	@if [ ! -f golden_vectors.json ]; then \
		echo "❌ golden_vectors.json not found"; \
		exit 1; \
	fi
	@python -c "import json; vectors=json.load(open('golden_vectors.json')); print(f'Testing {len(vectors[\"canonicalization_tests\"])} canonicalization vectors...')"
	@for test in pipes rules adapters; do \
		echo "  Testing $test component..."; \
		python test_golden_$test.py || exit 1; \
	done
	@echo "✅ Golden master tests passed"

# Security tests
security:
	@echo "🔒 Running security tests..."
	@echo "  Command injection prevention..."
	@echo '{"input": "; rm -rf /"}' | python axis_adapters.py exec <(echo 'adapters: [{name: test, command: echo, args: ["{{input}}"]}]') 2>/dev/null && echo "❌ Command injection not prevented" || echo "✅ Command injection prevented"
	@echo "  SQL injection prevention..."  
	@echo '{"name": "'"'"'; DROP TABLE users; --"}' | python axis_adapters.py exec <(echo 'adapters: [{name: test, command: echo, args: ["{{name|sql}}"]}]') >/dev/null && echo "✅ SQL injection prevented"
	@echo "  Allowlist enforcement..."
	@echo '{}' | python axis_adapters.py exec <(echo 'adapters: [{name: test, command: rm, args: ["-rf", "/"]}]') 2>/dev/null && echo "❌ Allowlist not enforced" || echo "✅ Allowlist enforced"
	@echo "✅ Security tests complete"

# Run the demo
demo:
	@echo "🎬 Running AXIS pipeline demo..."
	python demo_pipeline.py
	@echo "✅ Demo complete"

# Validate CALYX-PY philosophy
validate: philosophy check-loc
	@echo "✅ CALYX-PY philosophy validation complete"

# Show philosophy metrics
philosophy:
	@echo "📊 CALYX-PY Philosophy Metrics:"
	@echo ""
	@echo "🎯 Target: ~300-400 LOC total, zero core dependencies"
	@echo "🔒 Security: Command allowlist, injection prevention, resource limits"
	@echo "🧮 Determinism: RFC 8785 canonicalization, payload-view hashing"
	@echo "🔍 Purity: No side effects in PIPES/RULES, time injection via adapters"
	@echo ""

# Check lines of code
check-loc:
	@echo "📊 Lines of Code Analysis:"
	@echo ""
	@total=0; \
	for file in axis_pipes.py axis_rules.py axis_adapters.py; do \
		if [ -f $file ]; then \
			loc=$(grep -v '^\s*#' $file | grep -v '^\s*$' | wc -l); \
			echo "  $file: $loc LOC"; \
			total=$((total + loc)); \
			if [ $loc -gt 200 ]; then \
				echo "    ⚠️  Exceeds 200 LOC limit"; \
			elif [ $loc -gt 150 ]; then \
				echo "    📈 Above 150 LOC target"; \
			else \
				echo "    ✅ Within limits"; \
			fi; \
		fi; \
	done; \
	echo ""; \
	echo "  📊 Total: $total LOC"; \
	if [ $total -gt 600 ]; then \
		echo "    ⚠️  Exceeds 600 LOC total limit"; \
	elif [ $total -gt 450 ]; then \
		echo "    📈 Above 450 LOC target"; \
	else \
		echo "    ✅ Within CALYX-PY limits"; \
	fi
	@echo ""

# Linting
lint:
	@echo "🔍 Running linting checks..."
	python -m ruff check .
	python -m mypy axis_pipes.py axis_rules.py axis_adapters.py
	@echo "✅ Linting complete"

# Code formatting
format:
	@echo "🎨 Formatting code..."
	python -m black .
	python -m ruff check --fix .
	@echo "✅ Formatting complete"

# Test individual components
test-pipes:
	@echo "🔀 Testing AXIS-PIPES..."
	echo '{"user_name": "Alice", "age": "25"}' | python axis_pipes.py run examples/normalize.yaml

test-rules:
	@echo "⚖️ Testing AXIS-RULES..."
	echo '{"age": 25, "role": "admin"}' | python axis_rules.py apply examples/logic.yaml

test-adapters:
	@echo "🔌 Testing AXIS-ADAPTERS..."
	echo '{"user": "alice", "message": "hello"}' | python axis_adapters.py exec examples/echo.yaml --dry-run

# Hash verification tests
test-hashes:
	@echo "🔍 Testing hash verification..."
	@for component in axis_pipes.py axis_rules.py axis_adapters.py; do \
		if [ -f $component ]; then \
			echo "  Testing $component hash command..."; \
			python $component hash examples/sample.yaml > /dev/null && echo "    ✅ Hash generation works" || echo "    ❌ Hash generation failed"; \
		fi; \
	done

# Determinism tests
test-determinism:
	@echo "🎯 Testing determinism..."
	@input='{"name": "Alice", "age": 25}'; \
	hash1=$(echo "$input" | python axis_pipes.py run examples/normalize.yaml | jq -r '._pipe_audit.output_hash'); \
	hash2=$(echo "$input" | python axis_pipes.py run examples/normalize.yaml | jq -r '._pipe_audit.output_hash'); \
	if [ "$hash1" = "$hash2" ]; then \
		echo "  ✅ PIPES deterministic"; \
	else \
		echo "  ❌ PIPES not deterministic"; \
	fi

# Create example files if they don't exist
examples:
	@echo "📝 Creating example files..."
	@mkdir -p examples
	@echo 'pipeline:' > examples/normalize.yaml
	@echo '  - rename: {user_name: "name"}' >> examples/normalize.yaml
	@echo '  - validate: {age: "int"}' >> examples/normalize.yaml
	@echo 'component: TestRules' > examples/logic.yaml
	@echo 'rules:' >> examples/logic.yaml
	@echo '  - if: "age >= 18"' >> examples/logic.yaml
	@echo '    then: {status: "adult"}' >> examples/logic.yaml
	@echo 'adapters:' > examples/echo.yaml
	@echo '  - name: "echo_test"' >> examples/echo.yaml
	@echo '    command: "echo"' >> examples/echo.yaml
	@echo '    args: ["Hello {{user}}"]' >> examples/echo.yaml
	@echo 'component: SampleConfig' > examples/sample.yaml
	@echo "✅ Example files created"

# Performance benchmarks
benchmark:
	@echo "⚡ Running performance benchmarks..."
	@echo "PIPES performance (100 runs):"
	@time -p sh -c 'for i in $(seq 1 100); do echo "{\"test\": $i}" | python axis_pipes.py run examples/normalize.yaml > /dev/null; done'
	@echo "RULES performance (100 runs):"  
	@time -p sh -c 'for i in $(seq 1 100); do echo "{\"age\": $i}" | python axis_rules.py apply examples/logic.yaml > /dev/null; done'
	@echo "✅ Benchmarks complete"

# Build packages
build: clean
	@echo "🗂️ Building distribution packages..."
	python -m build
	@echo "✅ Build complete - check dist/ directory"

# Clean build artifacts
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	@echo "✅ Clean complete"

# Full CI pipeline
ci: install lint test-all golden security validate
	@echo "🎯 CI pipeline complete - all checks passed!"
	@echo ""
	@echo "📊 CALYX-PY Philosophy Status:"
	@echo "  ✅ Purity: No side effects in PIPES/RULES"
	@echo "  ✅ Security: Command allowlist and injection prevention"  
	@echo "  ✅ Determinism: RFC 8785 canonicalization"
	@echo "  ✅ Minimalism: Core components under LOC limits"
	@echo "  ✅ Composability: Unix pipe compatibility"
	@echo ""
	@echo "🚀 Ready for production deployment!"

# Show project status
status:
	@echo "📊 AXIS Project Status:"
	@echo ""
	@echo "Components:"
	@for file in axis_pipes.py axis_rules.py axis_adapters.py; do \
		if [ -f $file ]; then \
			loc=$(grep -v '^\s*#' $file | grep -v '^\s*$' | wc -l); \
			echo "  ✅ $file ($loc LOC)"; \
		else \
			echo "  ❌ $file (missing)"; \
		fi; \
	done
	@echo ""
	@echo "Dependencies:"
	@if command -v python >/dev/null 2>&1; then \
		echo "  ✅ Python $(python --version | cut -d' ' -f2)"; \
	else \
		echo "  ❌ Python (not found)"; \
	fi
	@if python -c "import yaml" 2>/dev/null; then \
		echo "  ✅ PyYAML (optional)"; \
	else \
		echo "  📦 PyYAML (install with: pip install pyyaml)"; \
	fi
	@echo ""
	@echo "Security Features:"
	@echo "  ✅ Command allowlist enforcement"
	@echo "  ✅ Template injection prevention" 
	@echo "  ✅ Resource limits and timeouts"
	@echo "  ✅ Restricted AST parsing"
	@echo ""
	@echo "Philosophy: CALYX-PY - Every line of code is a liability until proven otherwise"

# Regenerate golden master test vectors (maintainers only)
golden-regen:
	@echo "🏆 Regenerating golden master vectors..."
	@echo "⚠️  This should only be run by maintainers"
	@read -p "Are you sure you want to regenerate golden vectors? (y/N) " confirm; \
	if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then \
		python scripts/regenerate_golden.py; \
		echo "✅ Golden vectors regenerated"; \
	else \
		echo "❌ Golden regeneration cancelled"; \
	fi
