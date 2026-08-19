import json
from pathlib import Path


JSON_FILE = Path("storage/snapshots/atp/livematches.json")


def explore(obj, indent=0, max_items=3):

    prefix = "    " * indent

    if isinstance(obj, dict):

        for key, value in obj.items():

            print(f"{prefix}- {key}: {type(value).__name__}")

            if isinstance(value, (dict, list)):
                explore(value, indent + 1, max_items)

    elif isinstance(obj, list):

        print(f"{prefix}[Lista con {len(obj)} elementi]")

        if obj:

            print(f"{prefix}Primo elemento:")

            explore(obj[0], indent + 1, max_items)


def main():

    if not JSON_FILE.exists():

        print("Snapshot non trovato.")
        return

    with open(JSON_FILE, "r", encoding="utf-8") as f:

        data = json.load(f)

    print("\n========================================")
    print("JSON STRUCTURE")
    print("========================================\n")

    explore(data)


if __name__ == "__main__":

    main()