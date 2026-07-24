#!/usr/bin/env python3
"""
GRETIL Corpus Metadata Parser & Search Indexer (TEI XML Edition)
Organization: CRINE (www.crine.in)

Scans GRETIL TEI XML files in temp/1_sanskr/tei, extracts header metadata
(Title, Author, Editor, Religion, Canon, Category, Language, Transliteration, Verse/Chapter counts),
and builds a custom JSON and SQLite index database for searching and linking across the ART ecosystem.
"""

import argparse
import html
import json
import os
import re
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


import unicodedata

def slugify(text: str) -> str:
    """Generate a clean ASCII URL/filename-safe identifier string."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


class GretilTeiParser:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()

    def parse_all(self) -> List[Dict[str, Any]]:
        """Find and parse all TEI XML metadata headers across supported files."""
        records = []
        if not self.root_dir.exists():
            print(f"Error: Target directory '{self.root_dir}' does not exist.")
            return records

        # Prefer tei directory if present
        tei_dir = self.root_dir / "1_sanskr" / "tei"
        search_dir = tei_dir if tei_dir.exists() else self.root_dir

        xml_files = sorted(search_dir.rglob("*.xml"))
        print(f"Found {len(xml_files)} TEI XML file(s) in {search_dir}...")

        for filepath in xml_files:
            try:
                record = self.parse_tei_file(filepath)
                if record:
                    records.append(record)
            except Exception as e:
                print(f"Warning: Failed to parse TEI file {filepath.name}: {e}")

        return records

    def parse_tei_file(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Extract metadata from a single TEI XML file."""
        rel_path = filepath.relative_to(self.root_dir).as_posix()

        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
        except Exception as e:
            print(f"XML Parse Error in {filepath.name}: {e}")
            return None

        ns = {"tei": "http://www.tei-c.org/ns/1.0"}

        # Title
        title_el = root.find(".//tei:titleStmt/tei:title", ns)
        if title_el is None:
            title_el = root.find(".//tei:title", ns)
        title = "".join(title_el.itertext()).strip() if title_el is not None else filepath.stem

        # Author
        author_el = root.find(".//tei:titleStmt/tei:author", ns)
        author = "".join(author_el.itertext()).strip() if author_el is not None and author_el.text else "Unknown"

        # Editors / Contributors
        editors = []
        for resp in root.findall(".//tei:titleStmt/tei:respStmt", ns):
            name_el = resp.find("tei:name", ns)
            if name_el is not None and name_el.text:
                editors.append(name_el.text.strip())
        editor_str = ", ".join(dict.fromkeys(editors)) if editors else "GRETIL / TEI Archive"

        # Publisher / Source
        pub_el = root.find(".//tei:publicationStmt/tei:publisher", ns)
        source = "".join(pub_el.itertext()).strip() if pub_el is not None else "GRETIL"

        # License & Target URL
        lic_el = root.find(".//tei:publicationStmt//tei:licence", ns)
        license_str = "".join(lic_el.itertext()).strip() if lic_el is not None and lic_el.text else "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License"
        license_url = lic_el.attrib.get("target", "https://creativecommons.org/licenses/by-nc-sa/4.0/") if lic_el is not None else "https://creativecommons.org/licenses/by-nc-sa/4.0/"

        # Publication Date
        date_el = root.find(".//tei:publicationStmt/tei:date", ns)
        pub_date = date_el.attrib.get("when-iso", date_el.text or "2020-07-31") if date_el is not None else "2020-07-31"

        # Legacy Header / Edition notes
        note_el = root.find(".//tei:notesStmt/tei:note[@type='legacyheader']", ns)
        if note_el is None:
            note_el = root.find(".//tei:notesStmt/tei:note", ns)
        notes_str = "".join(note_el.itertext()).strip() if note_el is not None else ""

        # Keywords / Taxonomy
        keywords = []
        for kw in root.findall(".//tei:keywords/tei:term", ns):
            if kw.text:
                keywords.append(kw.text.strip())

        # Classification heuristics
        religion, canon, category, is_commentary = self._classify_tei(keywords, title, filepath.name)
        commentator = self._extract_commentator(title, author, notes_str) if is_commentary else None

        # Language & Transliteration
        lang_el = root.find(".//tei:text", ns)
        lang_code = lang_el.attrib.get("{http://www.w3.org/XML/1998/namespace}lang", "sa-Latn") if lang_el is not None else "sa-Latn"
        
        language = "Sanskrit"
        transliteration = "IAST (International Alphabet of Sanskrit Transliteration)"
        if "Deva" in lang_code:
            language = "Sanskrit (Devanagari)"
            transliteration = "Devanagari"

        # Verse & Chapter counts
        chapter_count, verse_count = self._estimate_tei_counts(root, ns)

        stem = filepath.stem
        if stem.startswith("sa_"):
            stem = stem[3:]
        file_id = slugify(stem)
        if file_id.startswith("sa-"):
            file_id = file_id[3:]

        return {
            "id": file_id,
            "title": title,
            "religion": religion,
            "canon": canon,
            "category": category,
            "is_commentary": is_commentary,
            "commentator": commentator,
            "language": language,
            "author": author,
            "editor": editor_str,
            "source": source,
            "license": license_str,
            "license_url": license_url,
            "publication_date": pub_date,
            "notes": notes_str,
            "transliteration": transliteration,
            "translation_available": False,
            "chapter_count": chapter_count,
            "verse_count": verse_count,
            "file": rel_path,
        }

    def _extract_commentator(self, title: str, author: str, notes: str) -> str:
        """Extract name of commentator from title or notes."""
        if "samkara" in title.lower() or "śamkara" in title.lower() or "śāṃkara" in title.lower() or "sankara" in title.lower():
            return "Śaṃkara"
        if "abhinavagupta" in title.lower():
            return "Abhinavagupta"
        if "bhāskara" in title.lower() or "bhaskara" in title.lower():
            return "Bhāskara I"
        if "dignāga" in title.lower() or "dinnaga" in title.lower():
            return "Dignāga"
        if "gauḍapāda" in title.lower() or "gaudapada" in title.lower():
            return "Gauḍapāda"
        if "haradatta" in title.lower():
            return "Haradatta"
        return author if author and author != "Unknown" else "Traditional Commentator"

    def _classify_tei(self, keywords: List[str], title: str, filename: str) -> Tuple[str, str, str, bool]:
        """Classify religion, canon, category, and commentary status based on TEI keywords and title."""
        kw_str = " ".join(keywords).lower()
        title_lower = title.lower()
        fn_lower = filename.lower()

        religion = "Hinduism"
        canon = "General Scripture"
        category = "Text"
        is_commentary = False

        if "-comm" in fn_lower or "_comm" in fn_lower or "comm" in title_lower or "bhāṣya" in title_lower or "bhasya" in title_lower or "vṛtti" in title_lower or "vrtti" in title_lower or "ṭīkā" in title_lower or "locana" in title_lower or "vivaraṇa" in title_lower:
            is_commentary = True

        # Religion detection
        if "buddhist" in kw_str or "bauddha" in kw_str or "buddhism" in kw_str:
            religion = "Buddhism"
            canon = "Buddhist Canon"
        elif "jaina" in kw_str or "jainism" in kw_str:
            religion = "Jainism"
            canon = "Jaina Canon"
        elif "veda" in kw_str:
            canon = "Vedic Canon"
        elif "purāṇa" in kw_str or "purana" in kw_str:
            canon = "Purāṇas"
        elif "śāstra" in kw_str or "philosophy" in kw_str:
            canon = "Śāstra & Philosophy"
        elif "poetry" in kw_str or "kāvya" in kw_str:
            canon = "Kāvya & Literature"
        elif "dharma" in kw_str or "smṛti" in kw_str:
            canon = "Smṛti & Dharmaśāstra"
        elif "śaiva" in kw_str:
            canon = "Śaiva Āgamas & Tantras"
        elif "vaiṣṇava" in kw_str:
            canon = "Vaiṣṇava Āgamas & Tantras"

        # Category detection
        if is_commentary:
            category = "Bhāṣya (Commentary)"
        elif "upaniṣad" in title_lower or "upanishad" in title_lower or "up_0" in fn_lower:
            category = "Upaniṣad"
        elif "sūtra" in title_lower or "sutra" in title_lower:
            category = "Sūtra"
        elif "gītā" in title_lower or "gita" in title_lower:
            category = "Gītā"
        elif "purāṇa" in title_lower or "purana" in title_lower:
            category = "Purāṇa"
        elif "saṃhitā" in title_lower or "samhita" in title_lower:
            category = "Saṃhitā"
        elif "stotra" in title_lower or "stuti" in title_lower or "stava" in title_lower:
            category = "Stotra"
        elif "tantra" in title_lower or "āgama" in title_lower:
            category = "Tantra"
        elif "kāvya" in title_lower or "carita" in title_lower or "zataka" in title_lower:
            category = "Kāvya"
        elif "veda" in title_lower:
            category = "Veda"

        return religion, canon, category, is_commentary

    def _estimate_tei_counts(self, root: ET.Element, ns: Dict[str, str]) -> Tuple[int, int]:
        """Estimate chapter and verse count from TEI XML text body."""
        text_el = root.find(".//tei:text", ns)
        if text_el is None:
            return 1, 10

        verses = text_el.findall(".//tei:l", ns)
        if not verses:
            verses = text_el.findall(".//tei:p", ns)
        
        divs = text_el.findall(".//tei:div", ns)
        
        verse_count = max(1, len(verses))
        chapter_count = max(1, len(divs))

        return chapter_count, verse_count


def save_to_json(records: List[Dict[str, Any]], output_path: str) -> None:
    """Save parsed corpus index to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON Index written to: {output_path} ({len(records)} records)")


def save_to_sqlite(records: List[Dict[str, Any]], db_path: str) -> None:
    """Save parsed corpus index to SQLite database."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gretil_corpus (
            id TEXT PRIMARY KEY,
            title TEXT,
            religion TEXT,
            canon TEXT,
            category TEXT,
            language TEXT,
            author TEXT,
            editor TEXT,
            source TEXT,
            transliteration TEXT,
            translation_available BOOLEAN,
            chapter_count INTEGER,
            verse_count INTEGER,
            file TEXT
        )
    """)

    cursor.execute("DELETE FROM gretil_corpus")

    for r in records:
        cursor.execute("""
            INSERT OR REPLACE INTO gretil_corpus (
                id, title, religion, canon, category, language, author, editor, source,
                transliteration, translation_available, chapter_count, verse_count, file
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r["id"], r["title"], r["religion"], r["canon"], r["category"], r["language"],
            r["author"], r["editor"], r["source"], r["transliteration"], r["translation_available"],
            r["chapter_count"], r["verse_count"], r["file"]
        ))

    conn.commit()
    conn.close()
    print(f"✅ SQLite Database written to: {db_path} ({len(records)} records)")


def search_index(db_path: str, query: str) -> None:
    """Search the generated SQLite database."""
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. Run index build first.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    sql = """
        SELECT id, title, religion, canon, category, author, file
        FROM gretil_corpus
        WHERE title LIKE ? OR category LIKE ? OR canon LIKE ? OR id LIKE ?
    """
    pattern = f"%{query}%"
    cursor.execute(sql, (pattern, pattern, pattern, pattern))
    results = cursor.fetchall()
    conn.close()

    print(f"\n--- Search Results for '{query}' ({len(results)} matches) ---")
    for row in results:
        print(f"• [{row[0]}] {row[1]} | Canon: {row[3]} | Category: {row[4]} | File: {row[6]}")


def main():
    parser = argparse.ArgumentParser(description="GRETIL Corpus Metadata Parser & Database Generator (TEI XML)")
    parser.add_argument("--dir", default="temp", help="Root directory containing GRETIL corpus files (default: temp)")
    parser.add_argument("--json", default="temp/gretil_index.json", help="Output JSON database path")
    parser.add_argument("--db", default="temp/gretil_index.db", help="Output SQLite database path")
    parser.add_argument("--search", help="Search the generated corpus database query")

    args = parser.parse_args()

    if args.search:
        search_index(args.db, args.search)
        return

    print(f"Scanning GRETIL TEI XML corpus in directory: {args.dir}...")
    g_parser = GretilTeiParser(args.dir)
    records = g_parser.parse_all()

    save_to_json(records, args.json)
    save_to_sqlite(records, args.db)


if __name__ == "__main__":
    main()
