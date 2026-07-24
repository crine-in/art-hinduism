#!/usr/bin/env python3
"""
TEI XML Whole Scripture Parser
Organization: CRINE (www.crine.in)

Parses GRETIL TEI XML files into unified "whole" dataset structures, extracting all
header metadata, licence, attributions, and the complete un-split text field (using \n for newlines).
"""

import hashlib
import re
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def slugify(text: str) -> str:
    """Convert text into lowercase ASCII kebab-case slug."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


class TeiWholeParser:
    """Parser for TEI XML scripture documents converting them to 'whole' dataset JSON objects."""

    def __init__(self, filepath: Path):
        self.filepath = Path(filepath).resolve()

    def parse(self) -> Optional[Dict[str, Any]]:
        """Parse TEI XML file and return a dictionary conforming to whole_book.schema.json."""
        if not self.filepath.exists():
            return None

        try:
            tree = ET.parse(self.filepath)
            root = tree.getroot()
        except Exception as e:
            print(f"XML Parse Error in {self.filepath.name}: {e}")
            return None

        ns = {"tei": "http://www.tei-c.org/ns/1.0"}

        # 1. Header Metadata Extraction
        title_el = root.find(".//tei:titleStmt/tei:title", ns)
        if title_el is None:
            title_el = root.find(".//tei:title", ns)
        title = "".join(title_el.itertext()).strip() if title_el is not None else self.filepath.stem

        author_el = root.find(".//tei:titleStmt/tei:author", ns)
        author = "".join(author_el.itertext()).strip() if author_el is not None and author_el.text else None

        editors = []
        for resp in root.findall(".//tei:titleStmt/tei:respStmt", ns):
            name_el = resp.find("tei:name", ns)
            if name_el is not None and name_el.text:
                editors.append(name_el.text.strip())
        editor_str = ", ".join(dict.fromkeys(editors)) if editors else "GRETIL / TEI Archive"

        pub_el = root.find(".//tei:publicationStmt/tei:publisher", ns)
        publisher = "".join(pub_el.itertext()).strip() if pub_el is not None else "Göttingen Register of Electronic Texts in Indian Languages"

        lic_el = root.find(".//tei:publicationStmt//tei:licence", ns)
        license_str = (
            "".join(lic_el.itertext()).strip()
            if lic_el is not None and lic_el.text
            else "Distributed under a Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License."
        )
        license_url = (
            lic_el.attrib.get("target", "https://creativecommons.org/licenses/by-nc-sa/4.0/")
            if lic_el is not None
            else "https://creativecommons.org/licenses/by-nc-sa/4.0/"
        )

        date_el = root.find(".//tei:publicationStmt/tei:date", ns)
        pub_date = date_el.attrib.get("when-iso", date_el.text or "2020-07-31") if date_el is not None else "2020-07-31"

        note_el = root.find(".//tei:notesStmt/tei:note[@type='legacyheader']", ns)
        if note_el is None:
            note_el = root.find(".//tei:notesStmt/tei:note", ns)
        notes_str = "".join(note_el.itertext()).strip() if note_el is not None else None
        ref_system = self._extract_reference_system(notes_str)

        bibl_el = root.find(".//tei:sourceDesc/tei:bibl", ns)
        bibl_source = "".join(bibl_el.itertext()).strip() if bibl_el is not None else None

        raw_terms = [kw.text.strip() for kw in root.findall(".//tei:keywords/tei:term", ns) if kw.text]
        split_keywords = []
        for term in raw_terms:
            parts = [p.strip() for p in term.split("--") if p.strip()]
            for p in parts:
                if p not in split_keywords:
                    split_keywords.append(p)
        keywords = split_keywords if split_keywords else None

        religion, collection, category = self._classify(keywords or [], title, self.filepath.name)

        # 2. Text Extraction
        text_el = root.find(".//tei:text", ns)
        body_text = self._extract_body_text(text_el, ns) if text_el is not None else ""

        lines = [line.strip() for line in body_text.splitlines() if line.strip()]
        cleaned_text = "\n".join(lines)

        word_count = len(re.findall(r"\w+", cleaned_text))
        line_count = len(lines)

        file_stem = self.filepath.stem
        if file_stem.startswith("sa_"):
            file_stem = file_stem[3:]
        book_slug = slugify(file_stem)
        col_slug = slugify(collection)
        rel_slug = slugify(religion)

        doc_id = f"whole:{rel_slug}:{col_slug}:{book_slug}:sanskrit-original"

        source_desc = f"GRETIL Archive ({self.filepath.name})"
        if bibl_source:
            source_desc += f"; {bibl_source}"

        return {
            "id": doc_id,
            "title": title,
            "originalTitle": title,
            "religion": religion,
            "collection": collection,
            "book": title,
            "language": "Sanskrit",
            "script": "IAST",
            "author": author,
            "editor": editor_str,
            "publisher": publisher,
            "publicationDate": pub_date,
            "license": license_str,
            "licenseUrl": license_url,
            "source": source_desc,
            "sourceUrl": "http://gretil.sub.uni-goettingen.de/",
            "notes": ref_system,
            "fullNotes": notes_str,
            "referenceSystem": ref_system,
            "keywords": keywords,
            "totalLines": line_count,
            "totalWords": word_count,
            "text": cleaned_text,
        }

    def _extract_reference_system(self, notes_str: Optional[str]) -> Optional[str]:
        """Extract the single line of Reference System containing '=' from notes."""
        if not notes_str:
            return None
        for line in notes_str.splitlines():
            line_clean = line.strip()
            if "=" in line_clean:
                return line_clean
        return None

    def _extract_body_text(self, text_el: ET.Element, ns: Dict[str, str]) -> str:
        """Extract clean plain text from TEI <text> element recursively preserving line breaks."""
        text_parts = []

        def recurse(node: ET.Element):
            tag = node.tag.split("}")[-1] if "}" in node.tag else node.tag

            # Ignore editorial notes / pagination inside body text
            if tag == "note":
                return

            # Handle choice elements (prefer reg over orig)
            if tag == "choice":
                reg_el = node.find("tei:reg", ns)
                if reg_el is not None:
                    txt = "".join(reg_el.itertext()).strip()
                    if txt:
                        text_parts.append(txt + " ")
                    return

            if node.text:
                t = node.text.strip()
                if t:
                    text_parts.append(t)

            for child in node:
                c_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if c_tag in ["p", "l", "div", "head", "lg"]:
                    text_parts.append("\n")
                recurse(child)
                if c_tag in ["p", "l", "div", "head", "lg"]:
                    text_parts.append("\n")
                if child.tail:
                    t = child.tail.strip()
                    if t:
                        text_parts.append(" " + t)

        recurse(text_el)
        raw = "".join(text_parts)
        # Normalize double newlines and spaces
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n\s*\n", "\n", raw)
        return raw.strip()

    def _classify(self, keywords: List[str], title: str, filename: str) -> Tuple[str, str, str]:
        """Classify religion, collection/canon, and category."""
        kw_str = " ".join(keywords).lower()
        title_lower = title.lower()
        fn_lower = filename.lower()

        religion = "Hinduism"
        collection = "General Scripture"
        category = "Text"

        if "buddhist" in kw_str or "bauddha" in kw_str or "buddhism" in kw_str:
            religion = "Buddhism"
            collection = "Buddhist Canon"
        elif "jaina" in kw_str or "jainism" in kw_str:
            religion = "Jainism"
            collection = "Jaina Canon"
        elif "veda" in kw_str:
            collection = "Vedic Canon"
        elif "purāṇa" in kw_str or "purana" in kw_str:
            collection = "Purāṇas"
        elif "śāstra" in kw_str or "philosophy" in kw_str:
            collection = "Śāstra & Philosophy"
        elif "poetry" in kw_str or "kāvya" in kw_str:
            collection = "Kāvya & Literature"
        elif "dharma" in kw_str or "smṛti" in kw_str:
            collection = "Smṛti & Dharmaśāstra"
        elif "śaiva" in kw_str:
            collection = "Śaiva Āgamas & Tantras"
        elif "vaiṣṇava" in kw_str:
            collection = "Vaiṣṇava Āgamas & Tantras"

        if "upaniṣad" in title_lower or "upanishad" in title_lower:
            category = "Upaniṣad"
        elif "sūtra" in title_lower or "sutra" in title_lower:
            category = "Sūtra"
        elif "gītā" in title_lower or "gita" in title_lower:
            category = "Gītā"
        elif "purāṇa" in title_lower or "purana" in title_lower:
            category = "Purāṇa"
        elif "stotra" in title_lower or "stuti" in title_lower:
            category = "Stotra"

        return religion, collection, category
