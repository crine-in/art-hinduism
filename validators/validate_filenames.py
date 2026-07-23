import sys
import re
from pathlib import Path


def validate_filename_conventions(repo_root: Path) -> bool:
    """Verifies directory and file naming conventions (kebab-case / lowercase)."""
    all_valid = True

    allowed_uppercase_files = {
        "README.md",
        "LICENSE",
        "ATTRIBUTION.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        "CHANGELOG.md",
        "CODEOWNERS",
        "PULL_REQUEST_TEMPLATE.md",
        "ISSUE_TEMPLATE",
        "GEMINI.md",
        "SKILLS.md",
        "AGENTS.md",
        "CLAUDE.md",
    }

    for path in repo_root.glob("**/*"):
        parts = path.parts
        if any(
            p.startswith(".") or p in {"venv", "node_modules", "__pycache__", "dist", "build"}
            for p in parts
            if p != repo_root.name
        ):
            continue

        rel_path = path.relative_to(repo_root)
        name = path.name

        if name in allowed_uppercase_files or name.startswith("."):
            continue

        if path.is_dir():
            if not re.match(r"^[a-z0-9\-_]+$", name):
                print(f"❌ Non-kebab-case directory name: {rel_path}")
                all_valid = False
        else:
            if path.suffix == ".py" and not re.match(r"^[a-z0-9_]+\.py$", name):
                print(f"❌ Python file should use snake_case: {rel_path}")
                all_valid = False

    if all_valid:
        print("✅ Filename & Directory naming validation passed.")
    return all_valid


if __name__ == "__main__":
    root = Path(__file__).parent.parent
    success = validate_filename_conventions(root)
    sys.exit(0 if success else 1)
