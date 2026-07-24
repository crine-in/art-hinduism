import json
from pathlib import Path
import jsonschema
import pytest
from tools.generate_transliterations import (
    SCRIPT_MAP,
    process_book_transliterations,
    transliterate_text,
)

repo_root = Path(__file__).parent.parent


def test_transliterate_text_basic():
    """Verify basic transliteration outputs across core scripts."""
    iast = "oṃ bhūr bhuvaḥ svaḥ"

    devanagari = transliterate_text(iast, "devanagari")
    assert "ॐ" in devanagari or "ओम्" in devanagari

    bengali = transliterate_text(iast, "bengali")
    assert "ওঁ" in bengali or "ওম" in bengali

    telugu = transliterate_text(iast, "telugu")
    assert "ఓం" in telugu or "ఒం" in telugu


def test_process_book_transliterations_example(tmp_path):
    """Test generating transliterated translation files for a book dataset."""
    # Create test book directory structure
    book_dir = tmp_path / "data" / "test-collection" / "test-book"
    book_dir.mkdir(parents=True)

    original_data = {
        "id": "test-book",
        "title": "Test Book Title",
        "religion": "Hinduism",
        "collection": "Vedic Canon",
        "book": "Test Book Title",
        "language": "Sanskrit",
        "script": "IAST",
        "license": "Public Domain",
        "source": "Test Source",
        "totalChapters": 1,
        "totalVerses": 2,
        "chapters": [
            {
                "number": 1,
                "title": "Chapter 1",
                "totalVerses": 2,
                "verses": [
                    {
                        "id": "hinduism:vedic-canon:test-book:1.1",
                        "chapter": 1,
                        "verse": 1,
                        "citation": "1.1",
                        "text": "kaṭhopaniṣat",
                    },
                    {
                        "id": "hinduism:vedic-canon:test-book:1.2",
                        "chapter": 1,
                        "verse": 2,
                        "citation": "1.2",
                        "text": "uśan ha vai vājaśravasaḥ",
                    },
                ],
            }
        ],
    }

    with open(book_dir / "original.json", "w", encoding="utf-8") as f:
        json.dump(original_data, f, ensure_ascii=False, indent=2)

    # Load translation schema
    schema_path = repo_root / "schemas" / "translation.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        trans_schema = json.load(f)
    validator = jsonschema.Draft202012Validator(trans_schema)

    # Process transliteration for devanagari and bengali
    res = process_book_transliterations(str(book_dir), ["devanagari", "bengali"], force=True)
    assert res["status"] == "success"
    assert "devanagari" in res["generated_scripts"]
    assert "bengali" in res["generated_scripts"]

    dev_file = book_dir / "translations" / "devanagari" / "indic-transliteration.json"
    assert dev_file.exists()

    with open(dev_file, "r", encoding="utf-8") as f:
        dev_data = json.load(f)

    # Validate against translation.schema.json
    validator.validate(dev_data)
    assert dev_data["targetLanguage"] == "Sanskrit (Devanagari)"
    assert dev_data["targetScript"] == "Deva"
    assert dev_data["chapters"][0]["verses"][0]["text"] == "कठोपनिषत्"
