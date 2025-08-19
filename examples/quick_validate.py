from AXIS.core import quick_validate

data = {"name": "Alice", "age": "30", "email": "alice@example.com"}
validated = quick_validate(data, name="str", age="int", email="str?")
print("Validated:", validated)

