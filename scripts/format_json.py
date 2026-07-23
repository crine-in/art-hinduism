import json
from pathlib import Path


def format_json_files(repo_root: Path):
    """Formats all JSON files with 2-space indentation."""
    json_files = list(repo_root.glob("**/*.json"))
    ignore_dirs = {".git", "venv", ".venv", "node_modules"}
    json_files = [p for p in json_files if not any(part in ignore_dirs for part in p.parts)]

    print(f"Formatting {len(json_files)} JSON files...")
    formatted_count = 0
    for p in json_files:
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            formatted = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            with open(p, "w", encoding="utf-8") as f:
                f.write(formatted)
            formatted_count += 1
        except Exception as e:
            print(f"Error formatting {p}: {e}")

    print(f"Successfully formatted {formatted_count} files.")


if __name__ == "__main__":
    root = Path(__file__).parent.parent
    format_json_files(root)
