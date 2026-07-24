import json
import sys
from pathlib import Path
import jsonschema


def validate_schemas(repo_root: Path) -> bool:
    """Validates JSON schemas in schemas/ and validates dataset files against schemas."""
    all_valid = True
    schemas_dir = repo_root / "schemas"

    schema_files = list(schemas_dir.glob("*.schema.json"))
    print(f"Validating {len(schema_files)} JSON schemas...")
    schemas = {}
    for sf in schema_files:
        try:
            with open(sf, "r", encoding="utf-8") as f:
                schema_data = json.load(f)
            jsonschema.Draft202012Validator.check_schema(schema_data)
            schemas[sf.name] = schema_data
        except Exception as e:
            print(f"❌ Invalid JSON Schema {sf.name}: {e}")
            all_valid = False

    if not all_valid:
        return False

    # Validate translation files against translation.schema.json
    trans_schema = schemas.get("translation.schema.json")
    if trans_schema:
        translation_validator = jsonschema.Draft202012Validator(trans_schema)
        translation_files = list((repo_root / "data").glob("**/translations/**/*.json"))
        if translation_files:
            print(f"Validating {len(translation_files)} translation file(s) against translation.schema.json...")
            for tf in translation_files:
                try:
                    with open(tf, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    translation_validator.validate(data)
                except Exception as e:
                    print(f"❌ Schema validation failed for translation file {tf.relative_to(repo_root)}: {e}")
                    all_valid = False

    if all_valid:
        print("✅ Schema validation completed successfully.")
    return all_valid


if __name__ == "__main__":
    root = Path(__file__).parent.parent
    success = validate_schemas(root)
    sys.exit(0 if success else 1)
