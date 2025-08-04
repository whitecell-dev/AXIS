from calyx.core import fallback

@fallback
def risky_fn(data):
    # Simulate failure
    return None

result = risky_fn({"text": "Unstructured input"})
print("Fallback result:", result)

