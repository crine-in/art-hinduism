import xml.etree.ElementTree as ET
import json
import argparse
import hashlib
from pathlib import Path


def convert_xml_to_json(input_path: Path, output_path: Path):
    """Parses XML verse nodes into ART verse schema JSON."""
    tree = ET.parse(input_path)
    root = tree.getroot()

    verses = []
    for idx, verse_node in enumerate(root.findall(".//verse"), start=1):
        text = verse_node.text.strip() if verse_node.text else ""
        v_num = int(verse_node.attrib.get("number", idx))
        ch_num = int(verse_node.attrib.get("chapter", 1))

        checksum = hashlib.sha256(text.encode("utf-8")).hexdigest()
        verses.append(
            {
                "id": f"generic:xml:1.{ch_num}.{v_num}",
                "externalId": idx,
                "religion": "Generic",
                "collection": "Example Collection",
                "book": "XML Ingestion",
                "chapter": ch_num,
                "verse": v_num,
                "citation": f"{ch_num}.{v_num}",
                "language": "English",
                "script": "Latn",
                "text": text,
                "license": "Public Domain",
                "source": input_path.name,
                "checksum": checksum,
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(verses, f, ensure_ascii=False, indent=2)

    print(f"Parsed {len(verses)} verses from XML file {input_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    convert_xml_to_json(args.input, args.output)
