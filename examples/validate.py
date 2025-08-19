from AXIS.core import validate

data = {"name": "Alice", "age": "25", "email": "alice@example.com"}
schema = {"name": "str", "age": "int", "email": "str?"}

is_valid, errors = validate(data, schema)

if is_valid:
    print("✓ Valid data:", data)
else:
    print("❌ Errors:", errors)

