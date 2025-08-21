# AXIS: React for Deterministic Reasoning
# Development workflow automation

.PHONY: help install test demo clean lint format validate philosophy check-loc build publish

# Default target
help:
	@echo "🚀 AXIS: React for Deterministic Reasoning"
	@echo ""
	@echo "Available commands:"
	@echo "  install     Install for development"
	@echo "  test        Run test suite"
	@echo "  demo        Run the demo pipeline"
	@echo "  validate    Validate AXIS-PY philosophy compliance"
	@echo "  philosophy  Show philosophy metrics"
	@echo "  check-loc   Check lines of code limits"
	@echo "  lint        Run linting checks"
	@echo "  format      Format code with black/ruff"
	@echo "  build       Build distribution packages"
	@echo "  clean       Clean build artifacts"
	@echo "  publish     Publish to PyPI (maintainers only)"

# Development installation
install:
	@echo "📦 Installing AXIS for development..."
	pip install -e ".[dev,yaml]"
	@echo "✅ Installation complete"

# Run tests
test:
	@echo "🧪 Running AXIS test suite..."
	python -m pytest tests/ -v
	@echo "✅ Tests complete"

# Run the demo
demo:
	@echo "🎬 Running AXIS pipeline demo..."
	python demo_pipeline.py
	@echo "✅ Demo complete"

# Validate AXIS-PY philosophy
validate: philosophy check-loc
	@echo "✅ AXIS-PY philosophy validation complete"

# Show philosophy metrics
philosophy:
	@echo "📏 AXIS-PY Philosophy Metrics:"
	@echo ""
	@python setup.py --validate
	@echo ""
	@echo "🎯 Target: ~150 LOC per component, zero core dependencies"

# Check lines of code
check-loc:
	@echo "📊 Lines of Code Analysis:"
	@echo ""
	@for file in axis_pipes.py axis_rules.py axis_adapters.py; do \
		if [ -f $$file ]; then \
			loc=$$(grep -v '^\s*#' $$file | grep -v '^\s*$$' | wc -l); \
			echo "  $$file: $$loc LOC"; \
			if [ $$loc -gt 200 ]; then \
				echo "    ⚠️  Exceeds 200 LOC limit"; \
			elif [ $$loc -gt 150 ]; then \
				echo "    📈 Above 150 LOC target"; \
			else \
				echo "    ✅ Within limits"; \
			fi; \
		fi; \
	done
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
	@echo "🔐 Testing hash verification..."
	@for component in axis_pipes.py axis_rules.py axis_adapters.py; do \
		if [ -f $$component ]; then \
			echo "  Testing $$component hash command..."; \
			python $$component hash examples/sample.yaml > /dev/null && echo "    ✅ Hash generation works" || echo "    ❌ Hash generation failed"; \
		fi; \
	done

# Create example files if they don't exist
examples:
	@echo "📁 Creating example files..."
	@mkdir -p examples
	@echo 'pipeline:\n  - rename: {user_name: "name"}\n  - validate: {age: "int"}' > examples/normalize.yaml
	@echo 'component: TestRules\nrules:\n  - if: "age >= 18"\n    then: {status: "adult"}' > examples/logic.yaml  
	@echo 'adapters:\n  - name: "echo_test"\n    command: "echo"\n    args: ["Hello {{user}}"]' > examples/echo.yaml
	@echo 'component: SampleConfig' > examples/sample.yaml
	@echo "✅ Example files created"

# Performance benchmarks
benchmark:
	@echo "⚡ Running performance benchmarks..."
	@echo "Pipes performance:"
	@time -p sh -c 'for i in $$(seq 1 100); do echo "{\"test\": $$i}" | python axis_pipes.py run examples/normalize.yaml > /dev/null; done'
	@echo "Rules performance:"  
	@time -p sh -c 'for i in $$(seq 1 100); do echo "{\"age\": $$i}" | python axis_rules.py apply examples/logic.yaml > /dev/null; done'
	@echo "✅ Benchmarks complete"

# Build packages
build: clean
	@echo "🏗️ Building distribution packages..."
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

# Publish to PyPI (maintainers only)
publish: build
	@echo "🚀 Publishing to PyPI..."
	@echo "⚠️  This should only be run by maintainers"
	@read -p "Are you sure you want to publish? (y/N) " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		python -m twine upload dist/*; \
		echo "✅ Published to PyPI"; \
	else \
		echo "❌ Publish cancelled"; \
	fi

# Generate documentation
docs:
	@echo "📚 Generating documentation..."
	mkdocs build
	@echo "✅ Documentation generated in site/"

# Serve documentation locally
docs-serve:
	@echo "🌐 Serving documentation locally..."
	mkdocs serve

# Full CI pipeline
ci: install lint test validate
	@echo "🎯 CI pipeline complete - all checks passed!"

# Show project status
status:
	@echo "📊 AXIS Project Status:"
	@echo ""
	@echo "Components:"
	@for file in axis_pipes.py axis_rules.py axis_adapters.py; do \
		if [ -f $$file ]; then \
			loc=$$(grep -v '^\s*#' $$file | grep -v '^\s*$$' | wc -l); \
			echo "  ✅ $$file ($$loc LOC)"; \
		else \
			echo "  ❌ $$file (missing)"; \
		fi; \
	done
	@echo ""
	@echo "Dependencies:"
	@if command -v python >/dev/null 2>&1; then \
		echo "  ✅ Python $$(python --version | cut -d' ' -f2)"; \
	else \
		echo "  ❌ Python (not found)"; \
	fi
	@if python -c "import yaml" 2>/dev/null; then \
		echo "  ✅ PyYAML (optional)"; \
	else \
		echo "  📦 PyYAML (install with: pip install pyyaml)"; \
	fi
	@echo ""
	@echo "Philosophy: AXIS-PY - Every line of code is a liability until proven otherwise"
