import hashlib
import json
from pathlib import Path


def generate_checksums(repo_root: Path):
    """Calculates SHA-256 checksums for verse texts in dataset files."""
    json_files = list(repo_root.glob("data/**/*.json"))

    print(f"Generating SHA-256 checksums for {len(json_files)} datasets...")
    for p in json_files:
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                for verse in data:
                    if isinstance(verse, dict) and "text" in verse:
                        text_str = verse["text"].strip()
                        verse["checksum"] = hashlib.sha256(text_str.encode("utf-8")).hexdigest()
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error generating checksums for {p}: {e}")


if __name__ == "__main__":
    root = Path(__file__).parent.parent
    generate_checksums(root)
