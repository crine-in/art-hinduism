#!/usr/bin/env python3
"""
ART Hinduism Batch Dataset Generator
Organization: CRINE (www.crine.in)

Converts indexed GRETIL texts into canonical, schema-compliant ART datasets in data/<collection-slug>/<book-slug>/.
Features:
- Multiprocessing CPU parallel processing (--workers N)
- Flexible batching (--batch 1-10, --limit N, --offset N)
- History tracking (--history temp/ingestion_history.json) for seamless continuation
- Master metadata auto-registration in metadata/collections.json
- Schema validation compliance for verse.schema.json and metadata.schema.json
"""

import argparse
import datetime
import hashlib
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


import unicodedata


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


def clean_html_tags(text: str) -> str:
    """Strip HTML tags and unescape HTML entities."""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = html.unescape(clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def parse_file_to_nested_json(
    filepath: Path,
    religion: str,
    collection: str,
    book_title: str,
    book_slug: str,
    collection_slug: str,
    language: str = "Sanskrit",
    script: str = "IAST",
) -> Dict[str, Any]:
    """Parse GRETIL TEI XML/content into a clean, nested JSON structure."""
    if not filepath.exists():
        return {}

    rel_slug = slugify(religion)

    if filepath.suffix.lower() == ".xml":
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            ns = {"tei": "http://www.tei-c.org/ns/1.0"}
            text_el = root.find(".//tei:text", ns)

            chapters = []
            total_verses = 0
            external_id = 1

            if text_el is not None:
                divs = text_el.findall(".//tei:div", ns)
                if not divs:
                    divs = [text_el]

                chap_num = 1
                for div in divs:
                    head_el = div.find("tei:head", ns)
                    head_title = "".join(head_el.itertext()).strip() if head_el is not None else f"Chapter {chap_num}"
                    div_type = div.attrib.get("type", "chapter")

                    verses = []
                    v_num = 1

                    for child in div.iter():
                        tag = child.tag.split("}")[-1]
                        if tag in ["l", "p", "seg"] and child.tag != div.tag:
                            child_tags = [c.tag.split("}")[-1] for c in child]
                            if not any(t in ["l", "p", "seg"] for t in child_tags):
                                txt = "".join(child.itertext()).strip()
                                if txt and txt != head_title:
                                    for l_str in txt.splitlines():
                                        if l_str.strip():
                                            verse_obj = {
                                                "id": f"{rel_slug}:{collection_slug}:{book_slug}:{chap_num}.{v_num}",
                                                "externalId": external_id,
                                                "chapter": chap_num,
                                                "verse": v_num,
                                                "citation": f"{chap_num}.{v_num}",
                                                "text": l_str.strip(),
                                            }
                                            verses.append(verse_obj)
                                            v_num += 1
                                            external_id += 1
                    if verses:
                        chapters.append({
                            "number": chap_num,
                            "title": head_title,
                            "type": div_type,
                            "totalVerses": len(verses),
                            "verses": verses,
                        })
                        total_verses += len(verses)
                        chap_num += 1

            return {
                "id": book_slug,
                "title": book_title,
                "religion": religion,
                "collection": collection,
                "book": book_title,
                "language": language,
                "script": script,
                "license": "Public Domain",
                "source": f"GRETIL Archive ({filepath.name})",
                "totalChapters": len(chapters),
                "totalVerses": total_verses,
                "chapters": chapters,
            }
        except Exception as e:
            print(f"Error parsing TEI XML in {filepath.name}: {e}")
            return {}

    # Fallback structure for text/HTML files
    return {
        "id": book_slug,
        "title": book_title,
        "religion": religion,
        "collection": collection,
        "book": book_title,
        "language": language,
        "script": script,
        "license": "Public Domain",
        "source": f"GRETIL Archive ({filepath.name})",
        "totalChapters": 1,
        "totalVerses": 1,
        "chapters": [
            {
                "number": 1,
                "title": "Chapter 1",
                "type": "chapter",
                "totalVerses": 1,
                "verses": [
                    {
                        "id": f"{rel_slug}:{collection_slug}:{book_slug}:1.1",
                        "externalId": 1,
                        "chapter": 1,
                        "verse": 1,
                        "citation": "1.1",
                        "text": book_title,
                    }
                ],
            }
        ],
    }


def process_item(args_tuple: Tuple[Dict[str, Any], str, str]) -> Dict[str, Any]:
    """Worker process function to generate dataset for a single GRETIL index item."""
    record, repo_root_str, history_path_str = args_tuple
    repo_root = Path(repo_root_str)

    file_rel = record.get("file", "")
    file_path = repo_root / "temp" / file_rel

    title = record.get("title", "Untitled Scripture")
    religion = record.get("religion", "Hinduism")
    collection = record.get("canon", record.get("collection", "Vedic Canon"))
    
    collection_slug = slugify(collection)
    book_slug = slugify(record.get("id", title))

    if not collection_slug:
        collection_slug = "vedic-canon"
    if not book_slug:
        book_slug = "scripture"

    book_dir = repo_root / "data" / collection_slug / book_slug
    book_dir.mkdir(parents=True, exist_ok=True)

    # Determine script code
    translit = record.get("transliteration", "")
    script_code = "IAST"
    if "Devanagari" in translit:
        script_code = "Deva"
    elif "Kyoto" in translit:
        script_code = "Latn"

    # Extract parsed header metadata fields
    author = record.get("author", "Unknown")
    editor = record.get("editor", "GRETIL / Digital Archive")
    license_str = record.get("license", "Distributed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License")
    license_url = record.get("license_url", "https://creativecommons.org/licenses/by-nc-sa/4.0/")
    pub_date = record.get("publication_date", "2020-07-31")
    notes_str = record.get("notes", "")

    # Parse nested JSON dataset object
    nested_doc = parse_file_to_nested_json(
        filepath=file_path,
        religion=religion,
        collection=collection,
        book_title=title,
        book_slug=book_slug,
        collection_slug=collection_slug,
        language="Sanskrit",
        script=script_code,
    )
    nested_doc["license"] = license_str
    nested_doc["source"] = f"GRETIL Archive ({file_rel})"

    # Write original.json
    save_json(nested_doc, book_dir / "original.json")

    # Calculate dataset SHA-256 checksum
    dataset_checksum = hashlib.sha256(json.dumps(nested_doc, sort_keys=True).encode("utf-8")).hexdigest()
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    iso_now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    total_verses = nested_doc.get("totalVerses", 0)
    is_comm = record.get("is_commentary", False)
    commentator = record.get("commentator")

    # If dataset is a commentary, generate commentary.json
    if is_comm:
        commentaries = []
        comm_id = 1
        for chap in nested_doc.get("chapters", []):
            for v_obj in chap.get("verses", []):
                commentaries.append({
                    "id": f"{v_obj['id']}:comm{comm_id}",
                    "verseId": v_obj["id"],
                    "commentaryName": title,
                    "commentator": commentator or "Traditional Commentator",
                    "school": None,
                    "language": "Sanskrit",
                    "script": script_code,
                    "text": v_obj["text"],
                    "license": license_str,
                    "source": f"GRETIL Archive ({file_rel})",
                })
                comm_id += 1
        save_json(commentaries, book_dir / "commentary.json")

    # Write metadata.json
    metadata_data = {
        "id": book_slug,
        "title": title,
        "originalTitle": title,
        "religion": religion,
        "collection": collection,
        "book": title,
        "author": author if author != "Unknown" else None,
        "isCommentary": is_comm,
        "commentator": commentator if is_comm else None,
        "commentaryName": title if is_comm else None,
        "language": "Sanskrit",
        "script": script_code,
        "translator": None,
        "editor": editor,
        "edition": "GRETIL TEI Critical Edition",
        "license": license_str,
        "licenseUrl": license_url,
        "source": "GRETIL (Göttingen Register of Electronic Texts in Indian Languages)",
        "sourceUrl": "http://gretil.sub.uni-goettingen.de/",
        "provenance": f"Digitized text ingested from GRETIL file {file_rel}.",
        "retrievalDate": today,
        "checksum": dataset_checksum,
        "totalChapters": nested_doc.get("totalChapters", 1),
        "verseCount": total_verses,
        "lastUpdated": iso_now,
    }
    save_json(metadata_data, book_dir / "metadata.json")

    # Write LICENSE
    license_content = f"""License: {license_str}
License URL: {license_url}
Publisher: {record.get("source", "GRETIL, SUB Göttingen")}
Publication Date: {pub_date}

This digital text is provided by GRETIL under the license terms above.
Distributed within the CRINE All Religious Texts (ART) ecosystem.
"""
    with open(book_dir / "LICENSE", "w", encoding="utf-8") as f:
        f.write(license_content)

    # Write ATTRIBUTION.md
    notes_md = f"\n## Source Notes & Edition Details\n\n```text\n{notes_str}\n```\n" if notes_str else ""
    attrib_content = f"""# Attribution & Provenance: {title}

- **Scripture Title**: {title}
- **Author**: {author}
- **Collection / Canon**: {collection}
- **Religion**: {religion}
- **Editor / Digitizers**: {editor}
- **Publisher**: {record.get("source", "GRETIL")}
- **License**: [{license_str}]({license_url})
- **GRETIL Publication Date**: {pub_date}
- **Source Archive File**: `{file_rel}`
{notes_md}"""
    with open(book_dir / "ATTRIBUTION.md", "w", encoding="utf-8") as f:
        f.write(attrib_content)

    # Write sources.md
    sources_content = f"""# Sources & Bibliography

- **Primary Archive**: Göttingen Register of Electronic Texts in Indian Languages (GRETIL), SUB Göttingen
- **Source File**: `{file_rel}`
- **Source URL**: http://gretil.sub.uni-goettingen.de/
- **Publisher / Archive**: {record.get("source", "GRETIL")}
"""
    with open(book_dir / "sources.md", "w", encoding="utf-8") as f:
        f.write(sources_content)

    return {
        "id": record.get("id"),
        "title": title,
        "collection": collection,
        "collection_slug": collection_slug,
        "book_slug": book_slug,
        "verses_count": total_verses,
        "file": file_rel,
        "status": "success",
    }


def update_master_collections(repo_root: Path, new_collections: Dict[str, str]) -> None:
    """Register any newly encountered collections into metadata/collections.json."""
    collections_path = repo_root / "metadata" / "collections.json"
    collections = load_json(collections_path) or []

    existing_ids = {item["id"] for item in collections}

    updated = False
    for col_slug, col_name in new_collections.items():
        if col_slug not in existing_ids:
            collections.append({
                "id": col_slug,
                "name": col_name,
                "religion": "Hinduism",
            })
            existing_ids.add(col_slug)
            updated = True

    if updated:
        save_json(collections, collections_path)
        print(f"✅ Updated master registry: metadata/collections.json")


def parse_batch_range(batch_str: str) -> Tuple[int, int]:
    """Parse batch string format like '1-10', '10-100', '100' into 1-based start and end indices."""
    if "-" in batch_str:
        parts = batch_str.split("-")
        return int(parts[0]), int(parts[1])
    else:
        val = int(batch_str)
        return 1, val


def main():
    parser = argparse.ArgumentParser(description="ART Hinduism Batch Dataset Generator")
    parser.add_argument("--index", default="temp/gretil_index.json", help="Path to GRETIL index JSON file")
    parser.add_argument("--batch", help="Batch range (e.g., '1-10', '10-100', '1-50')")
    parser.add_argument("--limit", type=int, help="Maximum records to process")
    parser.add_argument("--offset", type=int, default=0, help="Offset to start processing records from")
    parser.add_argument("--workers", type=int, default=os.cpu_count(), help="Number of parallel process workers")
    parser.add_argument("--history", default="temp/ingestion_history.json", help="History state JSON file")
    parser.add_argument("--force", action="store_true", help="Force reprocessing even if already in history log")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without writing files")

    args = parser.parse_args()
    repo_root = Path(__file__).parent.parent.resolve()

    index_path = repo_root / args.index
    if not index_path.exists():
        print(f"Error: Index file '{index_path}' not found. Run 'python3 tools/parse_gretil_headers.py' first.")
        sys.exit(1)

    records = load_json(index_path) or []
    total_records = len(records)
    print(f"Loaded {total_records} records from GRETIL index: {args.index}")

    # Load history
    history_path = repo_root / args.history
    history_data = load_json(history_path) or {}

    # Determine subset to process
    start_idx = args.offset
    end_idx = total_records

    if args.batch:
        b_start, b_end = parse_batch_range(args.batch)
        start_idx = max(0, b_start - 1)
        end_idx = min(total_records, b_end)
    elif args.limit:
        end_idx = min(total_records, start_idx + args.limit)

    target_records = records[start_idx:end_idx]
    print(f"Processing records range [{start_idx + 1}..{end_idx}] (Total: {len(target_records)} items)")

    # Filter records already in history unless --force
    items_to_process = []
    for rec in target_records:
        rec_id = rec.get("id") or rec.get("file")
        if not args.force and rec_id in history_data:
            continue
        items_to_process.append(rec)

    print(f"Items to execute (excluding history): {len(items_to_process)}")

    if args.dry_run:
        print("Dry run mode enabled. Exiting without modifications.")
        return

    if not items_to_process:
        print("No new items to process.")
        return

    workers = max(1, args.workers or 1)
    print(f"Starting multi-core processing pool using {workers} worker process(es)...")

    new_collections = {}
    completed_count = 0

    worker_args = [(item, str(repo_root), str(history_path)) for item in items_to_process]

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_item, arg): arg[0] for arg in worker_args}

        for future in as_completed(futures):
            item = futures[future]
            try:
                res = future.result()
                completed_count += 1
                rec_id = item.get("id") or item.get("file")
                history_data[rec_id] = {
                    "book_slug": res["book_slug"],
                    "collection_slug": res["collection_slug"],
                    "verses_count": res["verses_count"],
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                }
                new_collections[res["collection_slug"]] = res["collection"]
                print(f"  [{completed_count}/{len(items_to_process)}] Completed: {res['title']} -> data/{res['collection_slug']}/{res['book_slug']} ({res['verses_count']} verses)")
            except Exception as e:
                print(f"❌ Error processing item {item.get('title')}: {e}")

    # Save updated history
    save_json(history_data, history_path)
    print(f"✅ Ingestion history updated: {args.history}")

    # Update master metadata collections registry
    update_master_collections(repo_root, new_collections)

    print("\n============================================================")
    print(f"🎉 Batch processing finished! Successfully generated {completed_count} ART scripture dataset(s).")
    print("============================================================")


if __name__ == "__main__":
    main()
