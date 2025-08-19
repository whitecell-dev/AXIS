# AXIS: React for Deterministic Reasoning
# Simple development workflow

.PHONY: install test demo clean lint format

# Install for development
install:
	pip install -e .
	pip install -e ".[yaml,dev]"

# Run tests
test:
	python -m pytest tests/ -v
	python -c "import axis; print('✓ Core import works')"

# Generate and run golden vectors  
test-vectors:
	python -c "
from axis.testing import GoldenVectorGenerator
gen = GoldenVectorGenerator('examples/user_rules.yaml')
gen.add_test_case({'age': 25, 'email': 'test@example.com', 'role': 'admin'}, 'Valid admin')
gen.add_test_case({'age': 16}, 'Missing email, underage')
gen.save_vectors('examples/generated_vectors.json')
print('✓ Generated test vectors')
"
	axis test examples/user_rules.yaml examples/generated_vectors.json

# Run demo
demo:
	python demo.py

# Run Flask example
flask-demo:
	cd examples && python flask_app.py

# CLI examples
cli-demo:
	@echo "🚀 AXIS CLI Demo"
	@echo "1. Validate rules:"
	axis validate examples/user_rules.yaml
	@echo -e "\n2. Run rules with input:"
	axis run examples/user_rules.yaml '{"age": 25, "email": "alice@example.com", "role": "admin"}'
	@echo -e "\n3. Get IR hash:"
	axis hash examples/user_rules.yaml

# Code formatting
format:
	black axis/ examples/ tests/ demo.py setup.py

# Linting
lint:
	python -m py_compile axis/**/*.py
	@echo "✓ Syntax check passed"

# Clean up
clean:
	rm -rf build/ dist/ *.egg-info/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -delete
	rm -f examples/users.db examples/generated_vectors.json

# Package for PyPI
package:
	python setup.py sdist bdist_wheel
	@echo "✓ Package built in dist/"

# Check package structure
check-structure:
	@echo "📁 AXIS Package Structure:"
	@find axis/ -name "*.py" | head -20
	@echo "📊 Line counts:"
	@find axis/ -name "*.py" -exec wc -l {} + | tail -1
	@echo "✓ Meets CALYX-PY philosophy: minimal, focused, readable"

# Development workflow
dev: install test demo cli-demo
	@echo "🎯 AXIS development environment ready!"
