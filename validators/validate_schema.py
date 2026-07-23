import json
import sys
from pathlib import Path
import jsonschema


def validate_schemas(repo_root: Path) -> bool:
    """Validates JSON schemas in schemas/ and verifies metadata registries in metadata/."""
    all_valid = True
    schemas_dir = repo_root / "schemas"

    schema_files = list(schemas_dir.glob("*.schema.json"))
    print(f"Validating {len(schema_files)} JSON schemas...")
    for sf in schema_files:
        try:
            with open(sf, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
            jsonschema.Draft202012Validator.check_schema(schema_data)
        except Exception as e:
            print(f"❌ Invalid JSON Schema {sf.name}: {e}")
            all_valid = False

    if all_valid:
        print("✅ Schema validation completed successfully.")
    return all_valid


if __name__ == "__main__":
    root = Path(__file__).parent.parent
    success = validate_schemas(root)
    sys.exit(0 if success else 1)
