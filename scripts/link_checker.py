import re
from pathlib import Path


def check_markdown_links(repo_root: Path) -> bool:
    """Verifies that internal markdown relative links point to existing files."""
    all_good = True
    md_files = list(repo_root.glob("**/*.md"))
    ignore_dirs = {".git", "venv", ".venv", "node_modules"}
    md_files = [p for p in md_files if not any(part in ignore_dirs for part in p.parts)]

    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    print(f"Checking internal links across {len(md_files)} markdown files...")
    for md_file in md_files:
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        for match in link_pattern.finditer(content):
            target = match.group(2)
            if (
                target.startswith("http://")
                or target.startswith("https://")
                or target.startswith("mailto:")
                or target.startswith("#")
            ):
                continue
            target_path = target.split("#")[0]
            if not target_path:
                continue
            resolved = (md_file.parent / target_path).resolve()
            if not resolved.exists():
                print(f"❌ Broken link in {md_file.relative_to(repo_root)}: '{target}'")
                all_good = False

    if all_good:
        print("✅ All markdown internal links verified successfully.")
    return all_good


if __name__ == "__main__":
    root = Path(__file__).parent.parent
    check_markdown_links(root)
