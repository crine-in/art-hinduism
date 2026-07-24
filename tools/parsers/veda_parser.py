"""
Specialized Veda Parser
Organization: CRINE (www.crine.in)

Parses Vedic scripture texts (Rigveda, Atharvaveda, Samaveda, Yajurveda) from TEI XML
into canonical, nested schema-compliant ART book & verse structures.

Key Features:
- Eliminates metadata redundancy using nested structured JSON:
  Book -> chapters (Mandalas) -> sections (Suktas) -> verses (Mantras).
- Preserves Sanskrit dandas ('|' and '||') as essential clause and verse punctuation.
- Strips TEI accent markup tags (<orig>) cleanly while preserving IAST text content.
- Verses contain zero redundant inherited fields when serialized inside Book JSON.
"""

import html
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class VedaParser:
    """Specialized parser for Vedic literature (Mandala -> Sukta -> Mantra)."""

    TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}

    @staticmethod
    def slugify(text: str) -> str:
        """Convert text into lowercase ASCII kebab-case slug."""
        import unicodedata

        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
        text = text.lower()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[\s_-]+", "-", text)
        return text.strip("-")

    @classmethod
    def clean_line_text(cls, l_element: ET.Element, preserve_accents: bool = False) -> str:
        """Extract line text from a TEI <l> element, preserving '|' and '||' dandas.

        Strips TEI accent tags (<orig>) if preserve_accents is False, but retains
        all text, punctuation, and dandas.
        """
        if l_element is None:
            return ""

        if not preserve_accents:
            fragments = []
            if l_element.text:
                fragments.append(l_element.text)
            for child in l_element.iter():
                if child == l_element:
                    continue
                tag_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if tag_name != "orig" and child.text:
                    fragments.append(child.text)
                if child.tail:
                    fragments.append(child.tail)
            text = "".join(fragments)
        else:
            text = "".join(l_element.itertext())

        text = html.unescape(text)
        # Normalize whitespace while preserving dandas
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @classmethod
    def parse_tei_xml(
        cls,
        filepath: Union[str, Path],
        religion: str = "Hinduism",
        collection: str = "Vedic Canon",
        book_title: str = "Ṛgveda-Saṁhitā",
        book_slug: Optional[str] = None,
        collection_slug: Optional[str] = None,
        language: str = "Sanskrit",
        script: str = "IAST",
        license_str: str = "Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License",
        preserve_accents: bool = False,
    ) -> Dict[str, Any]:
        """Parse a Veda TEI XML file into a non-redundant nested Book dataset conforming to ART schemas."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Veda TEI file not found: {path}")

        book_slug = book_slug or cls.slugify(book_title)
        collection_slug = collection_slug or cls.slugify(collection)
        rel_slug = cls.slugify(religion)

        tree = ET.parse(path)
        root = tree.getroot()
        ns = cls.TEI_NS

        # Look for text body
        body = root.find(".//tei:text/tei:body", ns)
        if body is None:
            body = root.find(".//tei:body", ns)
        if body is None:
            body = root

        chapters = []
        total_verses_count = 0
        external_id = 1

        # Check for Mandalas/Kandas divs
        mandala_divs = body.findall(".//tei:div[@type='maṇḍala']", ns)
        if not mandala_divs:
            mandala_divs = body.findall(".//tei:div[@type='kāṇḍa']", ns)
        if not mandala_divs:
            mandala_divs = body.findall(".//tei:div[@type='book']", ns)
        if not mandala_divs:
            # Fallback: treat body as containing suktas directly under a single default mandala
            mandala_divs = [body]

        for m_idx, m_div in enumerate(mandala_divs, start=1):
            m_n_attr = m_div.attrib.get("n", str(m_idx))
            try:
                mandala_num = int(re.sub(r"\D", "", m_n_attr)) if re.sub(r"\D", "", m_n_attr) else m_idx
            except ValueError:
                mandala_num = m_idx

            head_el = m_div.find("tei:head", ns)
            mandala_title = "".join(head_el.itertext()).strip() if head_el is not None else f"Mandala {mandala_num}"
            div_type = m_div.attrib.get("type", "mandala")

            # Find Suktas inside this Mandala
            sukta_divs = m_div.findall("tei:div[@type='sūkta']", ns)
            if not sukta_divs:
                sukta_divs = m_div.findall("tei:div[@type='hymn']", ns)
            if not sukta_divs:
                sukta_divs = m_div.findall("tei:div[@type='anuvāka']", ns)
            if not sukta_divs and m_div == body:
                sukta_divs = m_div.findall(".//tei:div", ns)

            sections = []
            mandala_verse_count = 0

            for s_idx, s_div in enumerate(sukta_divs, start=1):
                s_n_attr = s_div.attrib.get("n", str(s_idx))
                try:
                    sukta_num = int(re.sub(r"\D", "", s_n_attr)) if re.sub(r"\D", "", s_n_attr) else s_idx
                except ValueError:
                    sukta_num = s_idx

                s_head_el = s_div.find("tei:head", ns)
                sukta_head_title = "".join(s_head_el.itertext()).strip() if s_head_el is not None else None

                # Find line groups (lg) representing Mantras
                lg_elements = s_div.findall(".//tei:lg", ns)

                verses = []
                mantra_num = 1

                if lg_elements:
                    for lg in lg_elements:
                        lg_id = lg.attrib.get("{http://www.w3.org/XML/1998/namespace}id", "") or lg.attrib.get("xml:id", "")
                        if lg_id:
                            parts = lg_id.split(".")
                            if len(parts) >= 3:
                                try:
                                    mantra_num = int(parts[-1])
                                except ValueError:
                                    pass

                        lines = lg.findall("tei:l", ns)
                        line_texts = []
                        for l_el in lines:
                            cleaned_l = cls.clean_line_text(l_el, preserve_accents=preserve_accents)
                            if cleaned_l:
                                line_texts.append(cleaned_l)

                        if line_texts:
                            combined_text = " ".join(line_texts)

                            # Guarantee double danda || at end of verse if not present
                            if not (combined_text.endswith("||") or combined_text.endswith("|")):
                                combined_text += " ||"

                            verse_id = f"{rel_slug}:{collection_slug}:{book_slug}:{mandala_num}.{sukta_num}.{mantra_num}"
                            citation_str = f"{mandala_num}.{sukta_num}.{mantra_num}"

                            # Non-redundant verse object for nested Book structure
                            verse_obj = {
                                "id": verse_id,
                                "externalId": external_id,
                                "verse": mantra_num,
                                "citation": citation_str,
                                "text": combined_text,
                            }
                            verses.append(verse_obj)
                            external_id += 1
                            mantra_num += 1
                else:
                    # Fallback for divs containing <l> directly without <lg> wrapper
                    lines = s_div.findall("tei:l", ns)
                    if lines:
                        current_lines = []
                        for l_el in lines:
                            txt = cls.clean_line_text(l_el, preserve_accents=preserve_accents)
                            if not txt:
                                continue
                            current_lines.append(txt)
                            if "||" in txt or txt.endswith("."):
                                combined_text = " ".join(current_lines)
                                verse_id = f"{rel_slug}:{collection_slug}:{book_slug}:{mandala_num}.{sukta_num}.{mantra_num}"
                                citation_str = f"{mandala_num}.{sukta_num}.{mantra_num}"
                                verse_obj = {
                                    "id": verse_id,
                                    "externalId": external_id,
                                    "verse": mantra_num,
                                    "citation": citation_str,
                                    "text": combined_text,
                                }
                                verses.append(verse_obj)
                                external_id += 1
                                mantra_num += 1
                                current_lines = []

                if verses:
                    sec_title = sukta_head_title if sukta_head_title else f"Sukta {sukta_num}"
                    sections.append({
                        "number": sukta_num,
                        "title": sec_title,
                        "type": "sukta",
                        "totalVerses": len(verses),
                        "verses": verses,
                    })
                    mandala_verse_count += len(verses)

            if sections:
                chapters.append({
                    "number": mandala_num,
                    "title": mandala_title,
                    "type": div_type,
                    "totalSections": len(sections),
                    "totalVerses": mandala_verse_count,
                    "sections": sections,
                })
                total_verses_count += mandala_verse_count

        # Fallback 1: Root-level <lg> elements (e.g. Vedanga-Jyotisa)
        if not chapters:
            lg_elements = body.findall(".//tei:lg", ns)
            if lg_elements:
                verses = []
                mantra_num = 1
                for lg in lg_elements:
                    lines = lg.findall("tei:l", ns)
                    line_texts = []
                    for l_el in lines:
                        cleaned_l = cls.clean_line_text(l_el, preserve_accents=preserve_accents)
                        if cleaned_l:
                            line_texts.append(cleaned_l)
                    if line_texts:
                        combined_text = " ".join(line_texts)
                        if not (combined_text.endswith("||") or combined_text.endswith("|")):
                            combined_text += " ||"
                        verse_id = f"{rel_slug}:{collection_slug}:{book_slug}:1.{mantra_num}"
                        citation_str = f"1.{mantra_num}"
                        verse_obj = {
                            "id": verse_id,
                            "externalId": external_id,
                            "verse": mantra_num,
                            "citation": citation_str,
                            "text": combined_text,
                        }
                        verses.append(verse_obj)
                        external_id += 1
                        mantra_num += 1

                if verses:
                    chapters.append({
                        "number": 1,
                        "title": book_title,
                        "type": "section",
                        "totalVerses": len(verses),
                        "verses": verses,
                    })
                    total_verses_count = len(verses)

        # Fallback 2: Check for <p> paragraph blocks with custom line patterns (Samaveda, Padapatha, Parisistas)
        if not chapters:
            p_elements = body.findall(".//tei:p", ns)

            # Patterns for different Vedic TEI XML variants
            sv_pattern = re.compile(r"^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d{4})([a-z])\s+(.+)$")
            pp_pattern = re.compile(r"^(.*?)\s*//\s*RV_(\d+),(\d+)\.(\d+)\s*//$")
            avp_pattern = re.compile(r"^\s*\([A-Za-z]+_(\d+),(\d+)\.(\d+)\)\s*(.+)$")

            m_s_map: Dict[int, Dict[int, List[Dict[str, Any]]]] = {}
            sv_prap_map: Dict[int, List[Dict[str, Any]]] = {}

            for p_el in p_elements:
                p_text = "".join(p_el.itertext())
                lines = p_text.splitlines()

                # Try matching Padapatha or Parisista style per <p> element
                pp_match = pp_pattern.search(p_text.strip())
                avp_match = avp_pattern.match(p_text.strip())

                if pp_match:
                    txt, m_num, s_num, v_num = pp_match.groups()
                    m_idx, s_idx, v_idx = int(m_num), int(s_num), int(v_num)
                    txt = txt.strip()
                    if not (txt.endswith("||") or txt.endswith("|")):
                        txt += " ||"

                    verse_obj = {
                        "id": f"{rel_slug}:{collection_slug}:{book_slug}:{m_idx}.{s_idx}.{v_idx}",
                        "externalId": external_id,
                        "verse": v_idx,
                        "citation": f"{m_idx}.{s_idx}.{v_idx}",
                        "text": txt,
                    }
                    external_id += 1
                    m_s_map.setdefault(m_idx, {}).setdefault(s_idx, []).append(verse_obj)

                elif avp_match:
                    m_num, s_num, v_num, txt = avp_match.groups()
                    m_idx, s_idx, v_idx = int(m_num), int(s_num), int(v_num)
                    txt = txt.strip()
                    if not (txt.endswith("||") or txt.endswith("|")):
                        txt += " ||"

                    verse_obj = {
                        "id": f"{rel_slug}:{collection_slug}:{book_slug}:{m_idx}.{s_idx}.{v_idx}",
                        "externalId": external_id,
                        "verse": v_idx,
                        "citation": f"{m_idx}.{s_idx}.{v_idx}",
                        "text": txt,
                    }
                    external_id += 1
                    m_s_map.setdefault(m_idx, {}).setdefault(s_idx, []).append(verse_obj)

                else:
                    # Line-by-line check (e.g. Samaveda)
                    current_v_key = None
                    current_v_lines = []

                    for l_str in lines:
                        match = sv_pattern.match(l_str)
                        if match:
                            arcika, prapathaka, ardha, code, line_char, txt = match.groups()
                            prap_num = int(prapathaka)
                            v_key = (arcika, prapathaka, code)

                            txt = txt.strip()
                            txt = re.sub(r"\.\.\s*\d*", "||", txt)
                            txt = re.sub(r"\.", "|", txt)
                            txt = re.sub(r"\s+", " ", txt).strip()

                            if current_v_key and current_v_key != v_key:
                                c_num, p_num, c_code = current_v_key
                                v_idx = int(c_code[2:])
                                comb_txt = " ".join(current_v_lines)
                                if not comb_txt.endswith("||") and not comb_txt.endswith("|"):
                                    comb_txt += " ||"

                                if int(p_num) not in sv_prap_map:
                                    sv_prap_map[int(p_num)] = []

                                verse_obj = {
                                    "id": f"{rel_slug}:{collection_slug}:{book_slug}:{p_num}.{v_idx}",
                                    "externalId": external_id,
                                    "verse": v_idx,
                                    "citation": f"{p_num}.{v_idx}",
                                    "text": comb_txt,
                                }
                                sv_prap_map[int(p_num)].append(verse_obj)
                                external_id += 1
                                current_v_lines = []

                            current_v_key = v_key
                            if not current_v_lines or current_v_key == v_key:
                                current_v_lines.append(txt)

                    if current_v_key and current_v_lines:
                        c_num, p_num, c_code = current_v_key
                        v_idx = int(c_code[2:])
                        comb_txt = " ".join(current_v_lines)
                        if not comb_txt.endswith("||") and not comb_txt.endswith("|"):
                            comb_txt += " ||"

                        if int(p_num) not in sv_prap_map:
                            sv_prap_map[int(p_num)] = []

                        verse_obj = {
                            "id": f"{rel_slug}:{collection_slug}:{book_slug}:{p_num}.{v_idx}",
                            "externalId": external_id,
                            "verse": v_idx,
                            "citation": f"{p_num}.{v_idx}",
                            "text": comb_txt,
                        }
                        sv_prap_map[int(p_num)].append(verse_obj)
                        external_id += 1

            if m_s_map:
                for m_num in sorted(m_s_map.keys()):
                    sec_dict = m_s_map[m_num]
                    sections = []
                    mandala_verses = 0
                    for s_num in sorted(sec_dict.keys()):
                        v_list = sec_dict[s_num]
                        sections.append({
                            "number": s_num,
                            "title": f"Sukta {s_num}",
                            "type": "sukta",
                            "totalVerses": len(v_list),
                            "verses": v_list,
                        })
                        mandala_verses += len(v_list)

                    chapters.append({
                        "number": m_num,
                        "title": f"Mandala {m_num}",
                        "type": "mandala",
                        "totalSections": len(sections),
                        "totalVerses": mandala_verses,
                        "sections": sections,
                    })
                    total_verses_count += mandala_verses

            elif sv_prap_map:
                for p_num in sorted(sv_prap_map.keys()):
                    verses = sv_prap_map[p_num]
                    if verses:
                        chapters.append({
                            "number": p_num,
                            "title": f"Prapāṭhaka {p_num}",
                            "type": "prapāṭhaka",
                            "totalVerses": len(verses),
                            "verses": verses,
                        })
                        total_verses_count += len(verses)

        return {
            "id": book_slug,
            "title": book_title,
            "religion": religion,
            "collection": collection,
            "book": book_title,
            "language": language,
            "script": script,
            "license": license_str,
            "source": f"GRETIL Archive ({path.name})",
            "totalChapters": len(chapters),
            "totalVerses": total_verses_count,
            "chapters": chapters,
        }
