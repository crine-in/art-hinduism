import json
from pathlib import Path
import jsonschema
import pytest

from tools.parsers.tei_whole_parser import TeiWholeParser
from tools.build_whole_datasets import process_tei_file, update_whole_indexes
from tools.generate_whole_transliterations import process_whole_book_transliterations


@pytest.fixture
def repo_root():
    return Path(__file__).parent.parent.resolve()


def test_tei_whole_parser_isopanisad(repo_root):
    tei_file = repo_root / "temp" / "1_sanskr" / "tei" / "sa_IzopaniSad-or-IzAvAsyopaniSadkANva-recension-comm.xml"
    assert tei_file.exists(), f"Sample TEI file {tei_file} not found"

    parser = TeiWholeParser(tei_file)
    doc = parser.parse()

    assert doc is not None
    assert "Īśopaniṣad" in doc["title"]
    assert doc["religion"] == "Hinduism"
    assert doc["collection"] == "Vedic Canon"
    assert doc["language"] == "Sanskrit"
    assert doc["script"] == "IAST"
    assert doc["license"] is not None
    assert doc["text"] is not None
    assert "\n" in doc["text"]
    assert doc["totalLines"] > 0
    assert doc["totalWords"] > 0
    assert doc["keywords"] is None or isinstance(doc["keywords"], list)


def test_tei_whole_parser_lalitavistara(repo_root):
    tei_file = repo_root / "temp" / "1_sanskr" / "tei" / "sa_lalitavistara.xml"
    assert tei_file.exists(), f"Sample TEI file {tei_file} not found"

    parser = TeiWholeParser(tei_file)
    doc = parser.parse()

    assert doc is not None
    assert doc["title"] == "Lalitavistara"
    assert doc["religion"] == "Buddhism"
    assert doc["collection"] == "Buddhist Canon"
    assert doc["text"] is not None
    assert "\n" in doc["text"]
    assert doc["totalLines"] > 0
    assert doc["totalWords"] > 0


def test_whole_book_schema_compliance(repo_root):
    tei_file = repo_root / "temp" / "1_sanskr" / "tei" / "sa_IzopaniSad-or-IzAvAsyopaniSadkANva-recension-comm.xml"
    parser = TeiWholeParser(tei_file)
    doc = parser.parse()

    schema_file = repo_root / "schemas" / "whole_book.schema.json"
    with open(schema_file, "r", encoding="utf-8") as f:
        schema = json.load(f)

    validator = jsonschema.Draft202012Validator(schema)
    validator.validate(doc)


def test_build_whole_dataset_and_transliteration(repo_root, tmp_path):
    tei_file = repo_root / "temp" / "1_sanskr" / "tei" / "sa_IzopaniSad-or-IzAvAsyopaniSadkANva-recension-comm.xml"
    
    # Process single TEI file
    res = process_tei_file((str(tei_file), str(repo_root), True))
    assert res is not None
    assert res["status"] in ["success", "skipped"]

    book_dir = repo_root / "whole" / res["collection_slug"] / res["book_slug"]
    whole_json_path = book_dir / "whole.json"
    assert whole_json_path.exists()

    # Verify whole.json content
    with open(whole_json_path, "r", encoding="utf-8") as f:
        whole_data = json.load(f)
    assert whole_data["text"] is not None
    assert whole_data.get("referenceSystem") == "IsUp_n = mūla text"

    metrics_path = repo_root / "whole" / "metrics.json"
    assert metrics_path.exists()
    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics_data = json.load(f)
    assert metrics_data["totalScriptures"] > 0
    assert metrics_data["totalLines"] > 0
    assert metrics_data["totalWords"] > 0

    # Test transliteration generation for this whole book
    trans_res = process_whole_book_transliterations(str(book_dir), ["devanagari"], force=True)
    assert trans_res["status"] == "success"

    deva_file = book_dir / "translations" / "devanagari" / "indic-transliteration.json"
    assert deva_file.exists()

    with open(deva_file, "r", encoding="utf-8") as f:
        deva_data = json.load(f)
    assert deva_data["targetScript"] == "Deva"
    assert "ओṃ" in deva_data["text"] or "ईशा" in deva_data["text"] or "पूर्णम्" in deva_data["text"]
