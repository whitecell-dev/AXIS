from calyx.core import RuleEngine

engine = RuleEngine("rules.yaml")
result = engine.run({"age": 25, "score": 0.9})
print("Decision:", result)

