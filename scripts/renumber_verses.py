import json
import sys
from pathlib import Path


def renumber_verses(file_path: Path):
    """Renumbers externalId and verse fields sequentially."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print(f"Error: {file_path} does not contain a verse list.")
        return

    for idx, verse in enumerate(data, start=1):
        verse["externalId"] = idx
        verse["verse"] = idx
        ch = verse.get("chapter", 1)
        verse["citation"] = f"{ch}.{idx}"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Renumbered {len(data)} verses in {file_path}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        renumber_verses(Path(sys.argv[1]))
    else:
        print("Usage: python renumber_verses.py <path_to_json>")
