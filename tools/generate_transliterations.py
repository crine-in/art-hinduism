#!/usr/bin/env python3
"""
ART Indic Scripture Transliteration Engine
Organization: CRINE (www.crine.in)

Transliterates IAST Sanskrit text from original.json scripture datasets into target Indic scripts
(Devanagari, Bengali, Grantha, Gujarati, Gurmukhi, Kannada, Malayalam, Odia, Telugu, Sharada, Tamil)
using the indic-transliteration Python library.
Generates schema-compliant JSON files under data/<collection>/<book>/translations/<script-name>/indic-transliteration.json.
"""

import argparse
import datetime
import json
import os
import re
import sys
import unicodedata
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from indic_transliteration import sanscript

SCRIPT_MAP: Dict[str, Dict[str, str]] = {
    "devanagari": {"scheme": "devanagari", "language": "Sanskrit (Devanagari)", "script": "Deva"},
    "bengali": {"scheme": "bengali", "language": "Sanskrit (Bengali)", "script": "Beng"},
    "grantha": {"scheme": "grantha", "language": "Sanskrit (Grantha)", "script": "Gran"},
    "gujarati": {"scheme": "gujarati", "language": "Sanskrit (Gujarati)", "script": "Gujr"},
    "gurmukhi": {"scheme": "gurmukhi", "language": "Sanskrit (Gurmukhi)", "script": "Guru"},
    "kannada": {"scheme": "kannada", "language": "Sanskrit (Kannada)", "script": "Knda"},
    "malayalam": {"scheme": "malayalam", "language": "Sanskrit (Malayalam)", "script": "Mlym"},
    "oriya": {"scheme": "oriya", "language": "Sanskrit (Odia)", "script": "Orya"},
    "telugu": {"scheme": "telugu", "language": "Sanskrit (Telugu)", "script": "Telu"},
    "sharada": {"scheme": "sharada", "language": "Sanskrit (Sharada)", "script": "Srbc"},
    "tamil": {"scheme": "tamil", "language": "Sanskrit (Tamil)", "script": "Taml"},
}


def slugify(text: str) -> str:
    """Convert text into lowercase ASCII kebab-case slug."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def load_json(filepath: Path) -> Any:
    """Load JSON file if it exists."""
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_json(data: Any, filepath: Path) -> None:
    """Save formatted JSON to file with 2-space indentation."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def transliterate_text(text: str, target_scheme: str) -> str:
    """Transliterate text string from IAST to target Indic script scheme."""
    if not text or not text.strip():
        return text
    try:
        return sanscript.transliterate(text, sanscript.IAST, target_scheme)
    except Exception:
        return text


def process_book_transliterations(
    book_dir_str: str,
    target_scripts: List[str],
    force: bool = False,
) -> Dict[str, Any]:
    """Process transliteration for a single book directory across selected target scripts."""
    book_dir = Path(book_dir_str)
    orig_path = book_dir / "original.json"

    if not orig_path.exists():
        return {"book_dir": book_dir_str, "status": "skipped", "reason": "No original.json"}

    orig_doc = load_json(orig_path)
    if not orig_doc or "chapters" not in orig_doc:
        return {"book_dir": book_dir_str, "status": "skipped", "reason": "Invalid original.json"}

    book_id = orig_doc.get("id", book_dir.name)
    religion = orig_doc.get("religion", "Hinduism")
    collection = orig_doc.get("collection", "")
    rel_slug = slugify(religion)
    col_slug = slugify(collection)

    generated_scripts = []

    for script_key in target_scripts:
        if script_key not in SCRIPT_MAP:
            continue

        script_info = SCRIPT_MAP[script_key]
        trans_file = book_dir / "translations" / script_key / "indic-transliteration.json"

        if trans_file.exists() and not force:
            continue

        trans_chapters = []
        for chap in orig_doc.get("chapters", []):
            verses_trans = []
            sections = chap.get("sections", [])
            if sections:
                for sec in sections:
                    for v_obj in sec.get("verses", []):
                        iast_text = v_obj.get("text", "")
                        trans_txt = transliterate_text(iast_text, script_info["scheme"])
                        verses_trans.append({
                            "verseId": v_obj.get("id", ""),
                            "verse": v_obj.get("verse"),
                            "citation": v_obj.get("citation"),
                            "text": trans_txt,
                            "notes": None,
                        })
            else:
                for v_obj in chap.get("verses", []):
                    iast_text = v_obj.get("text", "")
                    trans_txt = transliterate_text(iast_text, script_info["scheme"])
                    verses_trans.append({
                        "verseId": v_obj.get("id", ""),
                        "verse": v_obj.get("verse"),
                        "citation": v_obj.get("citation"),
                        "text": trans_txt,
                        "notes": None,
                    })

            trans_chapters.append({
                "number": chap.get("number", 1),
                "title": chap.get("title"),
                "totalVerses": len(verses_trans),
                "verses": verses_trans,
            })

        trans_doc = {
            "id": f"trans:{rel_slug}:{col_slug}:{book_id}:{script_info['script'].lower()}:indic-transliteration",
            "bookId": book_id,
            "title": orig_doc.get("title"),
            "religion": religion,
            "collection": collection,
            "book": orig_doc.get("book"),
            "targetLanguage": script_info["language"],
            "targetScript": script_info["script"],
            "translator": "indic-transliteration",
            "year": datetime.datetime.now().year,
            "license": orig_doc.get("license", "Public Domain"),
            "source": f"Auto-transliterated from IAST using indic-transliteration library ({orig_doc.get('source', '')})",
            "totalChapters": len(trans_chapters),
            "totalVerses": orig_doc.get("totalVerses", 0),
            "chapters": trans_chapters,
        }

        save_json(trans_doc, trans_file)
        generated_scripts.append(script_key)

    return {
        "book_id": book_id,
        "book_dir": book_dir_str,
        "status": "success",
        "generated_scripts": generated_scripts,
    }


def main():
    parser = argparse.ArgumentParser(description="ART Indic Scripture Transliteration Engine")
    parser.add_argument("--data-dir", default="data", help="Root data directory containing scriptures")
    parser.add_argument(
        "--scripts",
        default="devanagari,bengali,grantha,gujarati,gurmukhi,kannada,malayalam,oriya,telugu,sharada,tamil",
        help="Comma-separated list of target Indic scripts",
    )
    parser.add_argument("--limit", type=int, help="Maximum books to process")
    parser.add_argument("--workers", type=int, default=os.cpu_count(), help="Number of parallel worker processes")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing transliteration files")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing files")

    args = parser.parse_args()
    repo_root = Path(__file__).parent.parent.resolve()
    data_dir = repo_root / args.data_dir

    if not data_dir.exists():
        print(f"Error: Data directory '{data_dir}' not found.")
        sys.exit(1)

    target_scripts = [s.strip().lower() for s in args.scripts.split(",") if s.strip().lower() in SCRIPT_MAP]
    print(f"Target transliteration scripts ({len(target_scripts)}): {', '.join(target_scripts)}")

    # Locate all book directories with original.json
    book_dirs = [p.parent for p in data_dir.glob("**/original.json")]
    book_dirs.sort()

    if args.limit:
        book_dirs = book_dirs[: args.limit]

    print(f"Found {len(book_dirs)} scripture book dataset(s) to process.")

    if args.dry_run:
        print("Dry run mode enabled. Exiting without modifications.")
        return

    workers = max(1, args.workers or 1)
    print(f"Starting multi-process pool using {workers} worker(s)...")

    worker_args = [(str(b_dir), target_scripts, args.force) for b_dir in book_dirs]
    completed_count = 0

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_book_transliterations, *arg): arg for arg in worker_args}

        for future in as_completed(futures):
            try:
                res = future.result()
                completed_count += 1
                gen = res.get("generated_scripts", [])
                b_id = res.get("book_id", "book")
                if gen:
                    print(f"  [{completed_count}/{len(book_dirs)}] Transliterated: {b_id} -> {len(gen)} script(s)")
                else:
                    print(f"  [{completed_count}/{len(book_dirs)}] Up to date: {b_id}")
            except Exception as e:
                print(f"❌ Error processing book: {e}")

    print("\n============================================================")
    print(f"🎉 Transliteration finished! Processed {completed_count} scripture dataset(s).")
    print("============================================================")


if __name__ == "__main__":
    main()
