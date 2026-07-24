#!/usr/bin/env python3
"""
ART Veda Dataset & Index Builder
Organization: CRINE (www.crine.in)

Parses Vedic TEI XML scriptures using VedaParser, generates canonical ART datasets in
data/vedic-canon/<veda-slug>/, and maintains structured master & sub-indexes:
- metadata/veda_index.json (Master Index)
- metadata/vedas/<veda-slug>_index.json (Sub-Index per Veda)
"""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from parsers.veda_parser import VedaParser


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


def generate_sub_index(doc: Dict[str, Any], veda_slug: str) -> Dict[str, Any]:
    """Generate structured sub-index detailing Mandalas, Suktas, Mantra counts, and previews."""
    mandalas_list = []
    total_suktas_count = 0
    total_mantras = doc.get("totalVerses", 0)

    for chap in doc.get("chapters", []):
        mandala_num = chap.get("number", 1)
        sections = chap.get("sections", [])

        suktas_list = []
        mandala_mantras = 0

        if sections:
            for sec in sections:
                sukta_num = sec.get("number", 1)
                verses = sec.get("verses", [])
                if not verses:
                    continue

                first_v = verses[0]
                last_v = verses[-1]
                v_count = len(verses)
                mandala_mantras += v_count

                preview_text = first_v.get("text", "")
                if len(preview_text) > 120:
                    preview_text = preview_text[:117] + "..."

                sukta_entry = {
                    "sukta": sukta_num,
                    "title": sec.get("title", f"Sukta {sukta_num}"),
                    "totalMantras": v_count,
                    "citationPrefix": f"{mandala_num}.{sukta_num}",
                    "verseRange": f"{first_v.get('citation')} - {last_v.get('citation')}",
                    "previewText": preview_text,
                }
                suktas_list.append(sukta_entry)
        else:
            verses = chap.get("verses", [])
            if verses:
                first_v = verses[0]
                last_v = verses[-1]
                v_count = len(verses)
                mandala_mantras += v_count
                preview_text = first_v.get("text", "")
                if len(preview_text) > 120:
                    preview_text = preview_text[:117] + "..."
                suktas_list.append({
                    "sukta": 1,
                    "title": chap.get("title", "Sukta 1"),
                    "totalMantras": v_count,
                    "citationPrefix": f"{mandala_num}.1",
                    "verseRange": f"{first_v.get('citation')} - {last_v.get('citation')}",
                    "previewText": preview_text,
                })

        total_suktas_count += len(suktas_list)
        mandalas_list.append({
            "mandala": mandala_num,
            "title": chap.get("title", f"Mandala {mandala_num}"),
            "totalSuktas": len(suktas_list),
            "totalMantras": mandala_mantras,
            "suktas": suktas_list,
        })

    return {
        "vedaId": veda_slug,
        "title": doc.get("title", "Veda"),
        "religion": doc.get("religion", "Hinduism"),
        "collection": doc.get("collection", "Vedic Canon"),
        "totalMandalas": len(mandalas_list),
        "totalSuktas": total_suktas_count,
        "totalMantras": total_mantras,
        "mandalas": mandalas_list,
    }


def process_veda_tei(
    tei_path: Path,
    repo_root: Path,
    religion: str,
    collection: str,
    book_title: str,
    book_slug: str,
) -> Dict[str, Any]:
    """Parse a single Veda TEI XML file, write dataset files, sub-index, and return master index record."""
    print(f"\nParsing Veda TEI file: {tei_path.name}...")

    doc = VedaParser.parse_tei_xml(
        filepath=tei_path,
        religion=religion,
        collection=collection,
        book_title=book_title,
        book_slug=book_slug,
        collection_slug="vedic-canon",
        language="Sanskrit",
        script="IAST",
    )

    out_dir = repo_root / "data" / "vedic-canon" / book_slug
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save original.json
    save_json(doc, out_dir / "original.json")

    # Calculate dataset checksum
    dataset_bytes = json.dumps(doc, sort_keys=True).encode("utf-8")
    checksum = hashlib.sha256(dataset_bytes).hexdigest()
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    iso_now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    total_chapters = doc.get("totalChapters", 0)
    total_verses = doc.get("totalVerses", 0)

    # Save metadata.json (strictly conforming to metadata.schema.json)
    meta_doc = {
        "title": book_title,
        "originalTitle": book_title,
        "religion": religion,
        "collection": collection,
        "book": book_title,
        "language": "Sanskrit",
        "script": "IAST",
        "translator": None,
        "editor": "GRETIL Critical TEI Archive",
        "edition": "GRETIL Critical Edition",
        "license": doc.get("license", "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License"),
        "licenseUrl": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
        "source": f"GRETIL Archive ({tei_path.name})",
        "sourceUrl": "http://gretil.sub.uni-goettingen.de/",
        "provenance": f"Parsed from GRETIL TEI XML file {tei_path.name} with VedaParser preserving single and double dandas (| and ||).",
        "retrievalDate": today,
        "checksum": checksum,
        "verseCount": total_verses,
        "lastUpdated": iso_now,
    }
    save_json(meta_doc, out_dir / "metadata.json")

    # Generate LICENSE
    license_str = doc.get("license", "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License")
    license_url = "https://creativecommons.org/licenses/by-nc-sa/4.0/"
    license_content = f"""License: {license_str}
License URL: {license_url}
Publisher: GRETIL (Göttingen Register of Electronic Texts in Indian Languages), SUB Göttingen

This digital text is provided by GRETIL under the license terms above.
Distributed within the CRINE All Religious Texts (ART) ecosystem.
"""
    with open(out_dir / "LICENSE", "w", encoding="utf-8") as f:
        f.write(license_content)

    # Generate ATTRIBUTION.md
    attrib_content = f"""# Attribution & Provenance: {book_title}

- **Scripture Title**: {book_title}
- **Collection / Canon**: {collection}
- **Religion**: {religion}
- **Language**: Sanskrit
- **Script**: IAST
- **Editor / Digitizers**: GRETIL Critical TEI Archive
- **Publisher**: Göttingen Register of Electronic Texts in Indian Languages (GRETIL), SUB Göttingen
- **License**: [{license_str}]({license_url})
"""
    with open(out_dir / "ATTRIBUTION.md", "w", encoding="utf-8") as f:
        f.write(attrib_content)

    # Generate sources.md
    sources_content = f"""# Primary Sources & Bibliography

- **Primary Archive**: Göttingen Register of Electronic Texts in Indian Languages (GRETIL), SUB Göttingen
- **Source URL**: http://gretil.sub.uni-goettingen.de/
- **Publisher / Archive**: GRETIL, SUB Göttingen
"""
    with open(out_dir / "sources.md", "w", encoding="utf-8") as f:
        f.write(sources_content)


    # Generate sub-index
    sub_index_doc = generate_sub_index(doc, book_slug)
    sub_index_path = repo_root / "metadata" / "vedas" / f"{book_slug}_index.json"
    save_json(sub_index_doc, sub_index_path)

    print(f"✅ Generated dataset: data/vedic-canon/{book_slug}/original.json ({total_chapters} chapters, {total_verses} mantras)")
    print(f"✅ Generated sub-index: metadata/vedas/{book_slug}_index.json")

    return {
        "id": book_slug,
        "title": book_title,
        "slug": book_slug,
        "subIndex": f"metadata/vedas/{book_slug}_index.json",
        "dataPath": f"data/vedic-canon/{book_slug}/original.json",
        "metadataPath": f"data/vedic-canon/{book_slug}/metadata.json",
        "totalMandalas": sub_index_doc["totalMandalas"],
        "totalSuktas": sub_index_doc["totalSuktas"],
        "totalMantras": total_verses,
        "license": doc.get("license"),
        "source": f"GRETIL Archive ({tei_path.name})",
    }


def main():
    parser = argparse.ArgumentParser(description="ART Veda Dataset & Index Builder")
    parser.add_argument("--tei-dir", default="temp/1_sanskr/tei", help="Path to TEI XML directory")
    parser.add_argument("--vedas", nargs="*", help="Specific veda slugs to process (e.g. rigveda, samaveda, atharvaveda-paippalada)")

    args = parser.parse_args()
    repo_root = Path(__file__).parent.parent.resolve()
    tei_dir = repo_root / args.tei_dir

    if not tei_dir.exists():
        print(f"Error: TEI directory '{tei_dir}' not found.")
        return

    # Registry of supported Veda TEI files
    veda_files = [
        {
            "slug": "rigveda",
            "title": "Ṛgveda-Saṁhitā",
            "file": "sa_Rgveda-edAufrecht.xml",
            "collection": "Vedic Canon",
        },
        {
            "slug": "samaveda",
            "title": "Sāmaveda-Saṁhitā",
            "file": "sa_sAmavedasaMhitA.xml",
            "collection": "Vedic Canon",
        },
        {
            "slug": "atharvaveda-paippalada",
            "title": "Paippalāda-Saṁhitā",
            "file": "sa_paippalAdasaMhitA.xml",
            "collection": "Vedic Canon",
        },
        {
            "slug": "vedanga-jyotisa",
            "title": "Vedāṅga-Jyotiṣa",
            "file": "sa_lagadha-RgvedavedAGgajyotiSa.xml",
            "collection": "Vedic Canon",
        },
    ]

    if args.vedas:
        selected_slugs = set(args.vedas)
        veda_files = [v for v in veda_files if v["slug"] in selected_slugs]

    master_records = []
    total_all_mantras = 0

    for item in veda_files:
        xml_path = tei_dir / item["file"]
        if not xml_path.exists():
            print(f"Skipping {item['title']}: File {xml_path} not found.")
            continue

        master_rec = process_veda_tei(
            tei_path=xml_path,
            repo_root=repo_root,
            religion="Hinduism",
            collection=item["collection"],
            book_title=item["title"],
            book_slug=item["slug"],
        )
        master_records.append(master_rec)
        total_all_mantras += master_rec["totalMantras"]

    # Generate master index metadata/veda_index.json
    master_index_path = repo_root / "metadata" / "veda_index.json"
    master_index_doc = {
        "title": "ART Vedic Literature Master Index",
        "religion": "Hinduism",
        "collection": "Vedic Canon",
        "structurePattern": "Mandala/Kanda -> Sukta/Hymn -> Mantra/Verse",
        "totalVedas": len(master_records),
        "totalVerses": total_all_mantras,
        "lastUpdated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "vedas": master_records,
    }
    save_json(master_index_doc, master_index_path)
    print(f"\n🎉 Master Veda Index created: metadata/veda_index.json (Total Vedas: {len(master_records)}, Total Verses: {total_all_mantras})")


if __name__ == "__main__":
    main()
