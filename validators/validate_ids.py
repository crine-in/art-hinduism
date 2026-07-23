import json
import sys
from pathlib import Path


def validate_ids(repo_root: Path) -> bool:
    """Verifies identifier uniqueness across master registries in metadata/."""
    all_valid = True
    metadata_dir = repo_root / "metadata"

    registries = ["religions.json", "collections.json", "languages.json", "scripts.json", "licenses.json"]
    for registry in registries:
        reg_path = metadata_dir / registry
        if not reg_path.exists():
            continue

        with open(reg_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        seen_ids = set()
        for idx, item in enumerate(data):
            identifier = item.get("id") or item.get("code")
            if not identifier:
                print(f"❌ Missing identifier in {registry} item #{idx}")
                all_valid = False
            elif identifier in seen_ids:
                print(f"❌ Duplicate identifier '{identifier}' in {registry}")
                all_valid = False
            else:
                seen_ids.add(identifier)

    if all_valid:
        print("✅ Unique ID validation completed successfully.")
    return all_valid


if __name__ == "__main__":
    root = Path(__file__).parent.parent
    success = validate_ids(root)
    sys.exit(0 if success else 1)
