from pathlib import Path
p = Path("scripts/verify_goal_markets.py")

s = p.read_text(encoding="utf-8")

s = s.replace(
    "def evaluate_binary(results, probability_key, actual_key):",
    "def evaluate_binary(results, probability_key, actual_function):"
)

s = s.replace(
    "actual = r[actual_key]",
    "actual = actual_function(r)"
)

p.write_text(s, encoding="utf-8")
print("FIX APPLIED")
