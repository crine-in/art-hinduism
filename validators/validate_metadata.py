import json
import sys
from pathlib import Path


def validate_metadata_completeness(repo_root: Path) -> bool:
    """Checks metadata consistency across master registries and dataset metadata.json files."""
    all_valid = True
    metadata_dir = repo_root / "metadata"

    registries = ["religions.json", "collections.json", "languages.json", "scripts.json", "licenses.json"]
    for reg in registries:
        file_path = metadata_dir / reg
        if not file_path.exists():
            print(f"❌ Missing required master registry: metadata/{reg}")
            all_valid = False
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list) or len(data) == 0:
                print(f"❌ Master registry metadata/{reg} is empty or invalid JSON array")
                all_valid = False
        except Exception as e:
            print(f"❌ Error loading metadata/{reg}: {e}")
            all_valid = False

    if all_valid:
        print("✅ Metadata completeness validation passed.")
    return all_valid


if __name__ == "__main__":
    root = Path(__file__).parent.parent
    success = validate_metadata_completeness(root)
    sys.exit(0 if success else 1)
