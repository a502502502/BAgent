import json
from pathlib import Path

path = Path("reports/snai/italia-turchia.json")
with open(path, encoding="utf-8") as f:
    d = json.load(f)

print(f"File: {path.name}")
print("Top-level type:", type(d))

if isinstance(d, dict):
    print("Keys:", list(d.keys()))
    for k in list(d.keys())[:8]:
        val = d[k]
        if isinstance(val, (dict, list)):
            print(f"  Key '{k}': type {type(val)}, len {len(val)}")
            if isinstance(val, list) and val:
                print(f"    Sample item in '{k}':", val[0])
            elif isinstance(val, dict) and val:
                print(f"    Sample keys in '{k}':", list(val.keys())[:5])
        else:
            print(f"  Key '{k}': {val}")
elif isinstance(d, list):
    print(f"List length: {len(d)}")
    if d:
        print("Sample element 0 keys:", list(d[0].keys()) if isinstance(d[0], dict) else type(d[0]))
        print("Sample element 0:", d[0])
