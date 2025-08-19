from AXIS.core import typecheck

@typecheck({"x": "int", "y": "int"})
def multiply(data):
    return data["x"] * data["y"]

print(multiply({"x": "3", "y": "7"}))

