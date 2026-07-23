import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from validate_json import validate_json_syntax
from validate_schema import validate_schemas
from validate_ids import validate_ids
from validate_utf8 import validate_utf8_and_newlines
from validate_filenames import validate_filename_conventions
from validate_metadata import validate_metadata_completeness


def main():
    repo_root = Path(__file__).parent.parent
    print("=" * 60)
    print("   ART TEMPLATE - REPOSITORY VALIDATION SUITE          ")
    print("   CRINE (www.crine.in)                                ")
    print("=" * 60 + "\n")

    results = []

    print("[1/6] Validating JSON Syntax...")
    results.append(validate_json_syntax(repo_root))
    print()

    print("[2/6] Validating JSON Schemas & Registries...")
    results.append(validate_schemas(repo_root))
    print()

    print("[3/6] Validating Master Identifier Uniqueness...")
    results.append(validate_ids(repo_root))
    print()

    print("[4/6] Validating UTF-8 Encoding...")
    results.append(validate_utf8_and_newlines(repo_root))
    print()

    print("[5/6] Validating Directory & Filename Naming Standards...")
    results.append(validate_filename_conventions(repo_root))
    print()

    print("[6/6] Validating Master Metadata Completeness...")
    results.append(validate_metadata_completeness(repo_root))
    print()

    print("=" * 60)
    if all(results):
        print("🎉 ALL VALIDATION CHECKS PASSED SUCCESSFULLY!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("❌ ONE OR MORE VALIDATION CHECKS FAILED.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
