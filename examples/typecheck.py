from AXIS.core import typecheck

@typecheck({"x": "int", "y": "int"})
def add(data):
    return data["x"] + data["y"]

print("Sum:", add({"x": 5, "y": 3}))

