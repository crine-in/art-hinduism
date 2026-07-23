import json
import argparse
import hashlib
from pathlib import Path


def convert_txt_to_json(
    input_path: Path,
    output_path: Path,
    book_title: str,
    religion: str = "Generic",
    collection: str = "Example Collection",
    language: str = "English",
    script: str = "Latn",
):
    """Parses plain text lines into ART verse schema JSON."""
    with open(input_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.read().splitlines() if l.strip()]

    verses = []
    for idx, line in enumerate(lines, start=1):
        checksum = hashlib.sha256(line.encode("utf-8")).hexdigest()
        verses.append(
            {
                "id": f"{religion.lower()}:{collection.lower().replace(' ', '-')}:{book_title.lower().replace(' ', '-')}:1.{idx}",
                "externalId": idx,
                "religion": religion,
                "collection": collection,
                "book": book_title,
                "chapter": 1,
                "verse": idx,
                "citation": f"1.{idx}",
                "language": language,
                "script": script,
                "text": line,
                "license": "Public Domain",
                "source": input_path.name,
                "checksum": checksum,
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(verses, f, ensure_ascii=False, indent=2)

    print(f"Converted {len(verses)} verses from {input_path} -> {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--book", required=True, type=str)
    args = parser.parse_args()

    convert_txt_to_json(args.input, args.output, args.book)
