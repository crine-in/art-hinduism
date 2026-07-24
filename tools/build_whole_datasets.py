#!/usr/bin/env python3
"""
ART Whole Scripture Dataset Builder & Indexer
Organization: CRINE (www.crine.in)

Converts GRETIL TEI XML texts into whole (un-split) scripture datasets in whole/<collection-slug>/<book-slug>/.
Outputs:
- whole/<collection-slug>/<book-slug>/whole.json
- whole/<collection-slug>/<book-slug>/metadata.json
- whole/<collection-slug>/<book-slug>/LICENSE
- whole/<collection-slug>/<book-slug>/ATTRIBUTION.md
- whole/<collection-slug>/<book-slug>/sources.md

Maintains whole directory search index in:
- whole/index.json
- whole/index.db
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sqlite3
import sys
import unicodedata
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import TeiWholeParser
sys.path.insert(0, str(Path(__file__).parent))
from parsers.tei_whole_parser import TeiWholeParser, slugify


def load_json(filepath: Path) -> Any:
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_json(data: Any, filepath: Path) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def process_tei_file(args_tuple: Tuple[str, str, bool]) -> Optional[Dict[str, Any]]:
    file_path_str, repo_root_str, force = args_tuple
    filepath = Path(file_path_str)
    repo_root = Path(repo_root_str)

    parser = TeiWholeParser(filepath)
    doc = parser.parse()
    if not doc:
        return None

    collection = doc["collection"]
    religion = doc["religion"]
    title = doc["title"]

    collection_slug = slugify(collection) or "vedic-canon"
    file_stem = filepath.stem
    if file_stem.startswith("sa_"):
        file_stem = file_stem[3:]
    book_slug = slugify(file_stem) or "scripture"

    whole_dir = repo_root / "whole" / collection_slug / book_slug
    whole_json_path = whole_dir / "whole.json"

    if whole_json_path.exists() and not force:
        return {
            "status": "skipped",
            "book_slug": book_slug,
            "collection_slug": collection_slug,
            "title": title,
            "religion": religion,
            "collection": collection,
            "file": str(filepath.relative_to(repo_root / "temp")),
            "whole_json": doc,
        }

    whole_dir.mkdir(parents=True, exist_ok=True)

    # Extract fullNotes for ATTRIBUTION.md, then pop it from doc
    full_notes = doc.pop("fullNotes", None)
    ref_system = doc.get("referenceSystem")
    keywords = doc.get("keywords")

    # Create lean whole.json document removing fields that belong purely to metadata.json
    whole_doc = {
        "id": doc.get("id"),
        "title": title,
        "originalTitle": doc.get("originalTitle"),
        "religion": religion,
        "collection": collection,
        "book": title,
        "language": doc.get("language", "Sanskrit"),
        "script": doc.get("script", "IAST"),
        "author": doc.get("author"),
        "license": doc.get("license"),
        "referenceSystem": ref_system,
        "totalLines": doc.get("totalLines"),
        "totalWords": doc.get("totalWords"),
        "text": doc.get("text"),
    }

    # Save whole.json
    save_json(whole_doc, whole_json_path)

    # Save metadata.json with comprehensive metadata
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    iso_now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    metadata_doc = {
        "id": book_slug,
        "title": title,
        "originalTitle": doc.get("originalTitle"),
        "religion": religion,
        "collection": collection,
        "book": title,
        "author": doc.get("author"),
        "language": doc.get("language", "Sanskrit"),
        "script": doc.get("script", "IAST"),
        "translator": None,
        "editor": doc.get("editor"),
        "publisher": doc.get("publisher"),
        "publicationDate": doc.get("publicationDate"),
        "edition": "GRETIL TEI Critical Edition (Whole Dataset)",
        "license": doc.get("license"),
        "licenseUrl": doc.get("licenseUrl"),
        "source": doc.get("source"),
        "sourceUrl": doc.get("sourceUrl"),
        "provenance": f"Ingested from TEI XML file {filepath.name} into whole dataset structure.",
        "retrievalDate": today,
        "referenceSystem": ref_system,
        "keywords": keywords,
        "totalLines": doc.get("totalLines"),
        "totalWords": doc.get("totalWords"),
        "lastUpdated": iso_now,
    }
    save_json(metadata_doc, whole_dir / "metadata.json")

    # Save LICENSE
    license_content = f"""License: {doc.get('license')}
License URL: {doc.get('licenseUrl')}
Publisher: {doc.get('publisher')}
Publication Date: {doc.get('publicationDate')}

This digital text is provided by GRETIL under the license terms above.
Distributed within the CRINE All Religious Texts (ART) ecosystem.
"""
    with open(whole_dir / "LICENSE", "w", encoding="utf-8") as f:
        f.write(license_content)

    # Save ATTRIBUTION.md
    notes_to_use = full_notes or doc.get("notes") or ""
    notes_block = f"\n## Source Notes & Edition Details\n\n```text\n{notes_to_use}\n```\n" if notes_to_use else ""
    attrib_content = f"""# Attribution & Provenance: {title}

- **Scripture Title**: {title}
- **Author**: {doc.get('author') or 'Traditional / Unknown'}
- **Collection / Canon**: {collection}
- **Religion**: {religion}
- **Editor / Digitizers**: {doc.get('editor')}
- **Publisher**: {doc.get('publisher')}
- **License**: [{doc.get('license')}]({doc.get('licenseUrl')})
- **GRETIL Publication Date**: {doc.get('publicationDate')}
- **Source File**: `{filepath.name}`
{notes_block}"""
    with open(whole_dir / "ATTRIBUTION.md", "w", encoding="utf-8") as f:
        f.write(attrib_content)

    # Save sources.md
    sources_content = f"""# Sources & Bibliography

- **Primary Archive**: Göttingen Register of Electronic Texts in Indian Languages (GRETIL)
- **Source File**: `{filepath.name}`
- **Source URL**: http://gretil.sub.uni-goettingen.de/
- **Publisher**: {doc.get('publisher')}
"""
    with open(whole_dir / "sources.md", "w", encoding="utf-8") as f:
        f.write(sources_content)

    return {
        "status": "success",
        "book_slug": book_slug,
        "collection_slug": collection_slug,
        "title": title,
        "religion": religion,
        "collection": collection,
        "file": str(filepath.relative_to(repo_root)),
        "whole_json": doc,
    }


def update_whole_indexes(repo_root: Path, records: List[Dict[str, Any]]) -> None:
    """Maintain index.json, index.db, and metrics.json inside whole/ directory."""
    whole_dir = repo_root / "whole"
    whole_dir.mkdir(parents=True, exist_ok=True)

    json_index_path = whole_dir / "index.json"
    db_index_path = whole_dir / "index.db"
    metrics_path = whole_dir / "metrics.json"

    index_records = []
    religions_count = {}
    collections_count = {}
    keywords_count = {}
    total_lines = 0
    total_words = 0

    for r in records:
        doc = r.get("whole_json") or {}
        rel = r.get("religion", "Hinduism")
        col = r.get("collection", "Vedic Canon")
        l_cnt = doc.get("totalLines", 0) or 0
        w_cnt = doc.get("totalWords", 0) or 0

        kws = doc.get("keywords")
        if not kws:
            meta_file = repo_root / "whole" / r["collection_slug"] / r["book_slug"] / "metadata.json"
            if meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        mdata = json.load(f)
                        kws = mdata.get("keywords")
                except Exception:
                    pass

        if isinstance(kws, list):
            for kw in kws:
                if kw:
                    keywords_count[kw] = keywords_count.get(kw, 0) + 1

        religions_count[rel] = religions_count.get(rel, 0) + 1
        collections_count[col] = collections_count.get(col, 0) + 1
        total_lines += l_cnt
        total_words += w_cnt

        index_records.append({
            "id": r["book_slug"],
            "title": r["title"],
            "religion": rel,
            "collection": col,
            "collection_slug": r["collection_slug"],
            "book_slug": r["book_slug"],
            "language": doc.get("language", "Sanskrit"),
            "script": doc.get("script", "IAST"),
            "author": doc.get("author"),
            "editor": doc.get("editor"),
            "publisher": doc.get("publisher"),
            "license": doc.get("license"),
            "referenceSystem": doc.get("referenceSystem"),
            "totalLines": l_cnt,
            "totalWords": w_cnt,
            "file": f"whole/{r['collection_slug']}/{r['book_slug']}/whole.json",
        })

    index_records.sort(key=lambda x: (x["collection_slug"], x["book_slug"]))

    # Save whole/index.json
    save_json(index_records, json_index_path)
    print(f"✅ Updated whole/index.json ({len(index_records)} records)")

    # Save whole/index.db
    conn = sqlite3.connect(db_index_path)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS whole_corpus")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS whole_corpus (
            id TEXT PRIMARY KEY,
            title TEXT,
            religion TEXT,
            collection TEXT,
            collection_slug TEXT,
            book_slug TEXT,
            language TEXT,
            script TEXT,
            author TEXT,
            editor TEXT,
            publisher TEXT,
            license TEXT,
            referenceSystem TEXT,
            totalLines INTEGER,
            totalWords INTEGER,
            file TEXT
        )
    """)
    cursor.execute("DELETE FROM whole_corpus")

    for rec in index_records:
        cursor.execute("""
            INSERT OR REPLACE INTO whole_corpus (
                id, title, religion, collection, collection_slug, book_slug,
                language, script, author, editor, publisher, license, referenceSystem,
                totalLines, totalWords, file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rec["id"], rec["title"], rec["religion"], rec["collection"],
            rec["collection_slug"], rec["book_slug"], rec["language"], rec["script"],
            rec["author"], rec["editor"], rec["publisher"], rec["license"], rec["referenceSystem"],
            rec["totalLines"], rec["totalWords"], rec["file"]
        ))

    conn.commit()
    conn.close()
    print(f"✅ Updated whole/index.db ({len(index_records)} records)")

    # Save whole/metrics.json
    sorted_keywords = dict(sorted(keywords_count.items(), key=lambda item: (-item[1], item[0])))
    iso_now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    metrics_doc = {
        "totalScriptures": len(index_records),
        "totalCollections": len(collections_count),
        "totalLines": total_lines,
        "totalWords": total_words,
        "religions": religions_count,
        "collections": collections_count,
        "keywords": sorted_keywords,
        "lastUpdated": iso_now,
    }
    save_json(metrics_doc, metrics_path)
    print(f"✅ Updated whole/metrics.json")

    # Save whole/README.md
    rel_rows = "\n".join([f"| **{r}** | {c:,} |" for r, c in sorted(religions_count.items(), key=lambda x: -x[1])])
    col_rows = "\n".join([f"| **{c}** | {cnt:,} |" for c, cnt in sorted(collections_count.items(), key=lambda x: -x[1])])
    kw_rows = "\n".join([f"| `{k}` | {v:,} |" for k, v in list(sorted_keywords.items())[:20]])

    readme_content = f"""# ART Hinduism - Whole Scripture Corpus

**Organization**: CRINE ([www.crine.in](https://www.crine.in))  
**Platform**: All Religious Texts (ART)  

---

## Overview

The `whole/` directory contains the complete, un-split hinduism scripture datasets in JSON format built for the ART platform. Each dataset encapsulates full scripture texts with line breaks (`\\n`), comprehensive cataloging metadata (`metadata.json`), source attributions (`ATTRIBUTION.md`), license information (`LICENSE`), Indic script transliterations (`translations/`), and index databases (`index.json`, `index.db`).

---

## Corpus Statistics

Statistics generated from `whole/metrics.json`:

- **Total Scriptures**: {len(index_records):,}
- **Total Collections**: {len(collections_count)}
- **Total Lines**: {total_lines:,}
- **Total Words**: {total_words:,}

### Religion Breakdown

| Religion | Scripture Count |
| :--- | :--- |
{rel_rows}

### Collection Breakdown

| Collection | Scripture Count |
| :--- | :--- |
{col_rows}

### Top Keywords Frequency

| Keyword | Frequency |
| :--- | :--- |
{kw_rows}

---

## Directory Structure

```text
whole/
├── index.json               # Master JSON database index ({len(index_records)} records)
├── index.db                 # Master SQLite database index
├── metrics.json             # Aggregated corpus metrics & keyword stats
├── README.md                # Corpus overview documentation
├── LICENSE                  # General dataset licensing framework
├── ATTRIBUTION.md           # Master attributions & source repositories
└── <collection-slug>/
    └── <book-slug>/
        ├── whole.json       # Lean whole scripture text & essential metadata
        ├── metadata.json    # Complete cataloging & provenance metadata
        ├── LICENSE          # Scripture-specific license
        ├── ATTRIBUTION.md   # Full editor attributions & header notes
        └── translations/
            └── <script>/
                └── indic-transliteration.json  # Indic script transliterations
```

---

## Tooling & Validation

- **Parser**: `tools/parsers/tei_whole_parser.py`
- **Dataset Builder**: `tools/build_whole_datasets.py`
- **Transliteration Engine**: `tools/generate_whole_transliterations.py`
- **Schema**: `schemas/whole_book.schema.json`
"""
    with open(whole_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    # Save whole/LICENSE
    license_content = """CRINE All Religious Texts (ART) - Hinduism Scripture Corpus General License

Organization: CRINE (www.crine.in)
Repository: https://github.com/crine-in/art-hinduism 

GENERAL LICENSE NOTICE:
-----------------------
Individual scriptures, commentary editions, and translations contained in this `whole/` dataset directory are sourced from open academic digital repositories (including GRETIL / SUB Göttingen, Nagarjuna Institute Nepal, Digital Sanskrit Buddhist Canon, and Sansknet Project).

Each scripture directory contains its own specific LICENSE file:
`whole/<collection-slug>/<book-slug>/LICENSE`

Most texts in this collection are distributed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0) or Public Domain / Open Data licenses, as declared in each scripture's respective directory.

TERMS & CONDITIONS:
-------------------
1. Attribution: When reusing, distributing, or processing datasets from this corpus, you must retain attributions to the original editors, digitizers, and publishing academic institutions as recorded in `ATTRIBUTION.md` and scripture-specific `metadata.json` files.
2. Non-Commercial & ShareAlike: Where declared by individual text licenses (such as CC BY-NC-SA 4.0), commercial redistribution is restricted without prior authorization from the originating rights holders, and derivative works must be shared under compatible terms.
3. Disclaimer: This dataset collection is provided "as-is" for educational, research, and non-commercial analytical purposes.
"""
    with open(whole_dir / "LICENSE", "w", encoding="utf-8") as f:
        f.write(license_content)

    # Save whole/ATTRIBUTION.md
    attrib_content = f"""# Attribution & Provenance: Whole Scripture Corpus

**Organization**: CRINE ([www.crine.in](https://www.crine.in))  
**Platform**: All Religious Texts (ART)  
**Corpus**: Hinduism Whole Scripture Collection (`whole/`)  

---

## Summary Statistics

- **Total Scriptures**: {len(index_records):,}
- **Total Collections**: {len(collections_count)}
- **Total Lines**: {total_lines:,}
- **Total Words**: {total_words:,}

---

## Primary Digital Repositories & Digitizers

The texts in this whole scripture dataset collection were ingested from TEI XML digital archives and critical scholarly editions, made available through the dedicated work of academic institutions and open-access digitizer teams:

1. **GRETIL (Göttingen Register of Electronic Texts in Indian Languages)**
   - *Publisher*: Niedersächsische Staats- und Universitätsbibliothek Göttingen (SUB Göttingen)
   - *URL*: [http://gretil.sub.uni-goettingen.de/](http://gretil.sub.uni-goettingen.de/)
   - *Contributions*: Comprehensive Sanskrit TEI XML editions covering Vedic Canon, Epics, Purāṇas, Śāstra & Philosophy, Kāvya, and Tantras.

2. **Digital Sanskrit Buddhist Canon (DSBC)**
   - *Institutions*: Nagarjuna Institute (Nepal) & University of the West (Rosemead, California, USA)
   - *URL*: [http://www.uwest.edu/sanskritcanon](http://www.uwest.edu/sanskritcanon)
   - *Contributions*: Digitization of Mahāyāna Buddhist canonical texts, sūtras, and śāstras.

3. **Sansknet Project & Individual Scholars**
   - *Contributions*: Digitization and critical TEI mark-up contributions by Reinhold Grünendahl, Maximilian Mehner, Patrick Olivelle, and university scholarly teams across Europe and India.

---

## Detailed Scripture Attributions

Every individual scripture directory under `whole/<collection-slug>/<book-slug>/` contains a dedicated `ATTRIBUTION.md` file documenting the specific text edition, original editors, digitizers, publication dates, and original source notes.
"""
    with open(whole_dir / "ATTRIBUTION.md", "w", encoding="utf-8") as f:
        f.write(attrib_content)
    print("✅ Updated whole/README.md, whole/LICENSE, and whole/ATTRIBUTION.md")


def main():
    parser = argparse.ArgumentParser(description="ART Whole Scripture Dataset Builder")
    parser.add_argument("--dir", default="temp/1_sanskr/tei", help="Directory containing TEI XML files")
    parser.add_argument("--limit", type=int, help="Maximum files to process")
    parser.add_argument("--workers", type=int, default=os.cpu_count(), help="Number of parallel worker processes")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing whole files")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing files")

    args = parser.parse_args()
    repo_root = Path(__file__).parent.parent.resolve()
    tei_dir = repo_root / args.dir

    if not tei_dir.exists():
        print(f"Error: Directory '{tei_dir}' not found.")
        sys.exit(1)

    xml_files = sorted(list(tei_dir.glob("*.xml")))
    print(f"Found {len(xml_files)} TEI XML file(s) in {tei_dir}...")

    if args.limit:
        xml_files = xml_files[: args.limit]
        print(f"Limited processing to {len(xml_files)} file(s).")

    if args.dry_run:
        print("Dry run mode enabled. Exiting without modifications.")
        return

    workers = max(1, args.workers or 1)
    print(f"Starting process pool with {workers} worker(s)...")

    worker_args = [(str(f), str(repo_root), args.force) for f in xml_files]
    all_processed = []
    completed_count = 0

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_tei_file, arg): arg for arg in worker_args}
        for future in as_completed(futures):
            try:
                res = future.result()
                completed_count += 1
                if res:
                    all_processed.append(res)
                    b_id = res["book_slug"]
                    st = res["status"]
                    print(f"  [{completed_count}/{len(xml_files)}] {st.capitalize()}: {res['title']} -> whole/{res['collection_slug']}/{b_id}/whole.json")
            except Exception as e:
                print(f"❌ Error processing file: {e}")

    # Update index files inside whole/
    if all_processed:
        update_whole_indexes(repo_root, all_processed)

    print("\n============================================================")
    print(f"🎉 Whole dataset building completed! Processed {len(all_processed)} scripture(s).")
    print("============================================================")


if __name__ == "__main__":
    main()
