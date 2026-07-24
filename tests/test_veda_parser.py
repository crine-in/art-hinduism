"""
Unit Tests for Veda Parser & Structured Indexing
Organization: CRINE (www.crine.in)
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import jsonschema
import pytest

from tools.build_veda_datasets import generate_sub_index
from tools.parsers.veda_parser import VedaParser


@pytest.fixture
def sample_tei_xml(tmp_path: Path) -> Path:
    """Create a temporary TEI XML file for Rigveda testing."""
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0" xml:id="sa_Rgveda-edAufrecht">
  <text xml:lang="sa-Latn" xml:id="RV">
    <body>
      <div>
        <head>Ṛgveda-Saṁhitā</head>
        <div type="maṇḍala" n="1">
          <head>Maṇḍala 1</head>
          <div type="sūkta" n="001">
            <lg xml:id="RV_1.001.01">
              <l n="1.001.01a">a<orig>̱</orig>gnim ī<orig>̍</orig>ḻe pu<orig>̱</orig>rohi<orig>̍</orig>taṁ ya<orig>̱</orig>jñasya<orig>̍</orig> de<orig>̱</orig>vam ṛ<orig>̱</orig>tvija<orig>̍</orig>m |</l>
              <l n="1.001.01c">hotā<orig>̍</orig>raṁ ratna<orig>̱</orig>dhāta<orig>̍</orig>mam ||</l>
            </lg>
            <lg xml:id="RV_1.001.02">
              <l n="1.001.02a">a<orig>̱</orig>gniḥ pūrve<orig>̍</orig>bhi<orig>̱</orig>r ṛṣi<orig>̍</orig>bhi<orig>̱</orig>r īḍyo<orig>̱</orig> nūta<orig>̍</orig>nair u<orig>̱</orig>ta |</l>
              <l n="1.001.02c">sa de<orig>̱</orig>vām̐ eha va<orig>̍</orig>kṣati ||</l>
            </lg>
          </div>
        </div>
      </div>
    </body>
  </text>
</TEI>
"""
    file_path = tmp_path / "test_rgveda.xml"
    file_path.write_text(xml_content, encoding="utf-8")
    return file_path


def test_clean_line_text_danda_preservation():
    """Test that VedaParser retains '|' and '||' and strips accent markup tags."""
    xml_str = '<l xmlns="http://www.tei-c.org/ns/1.0">a<orig>̱</orig>gnim ī<orig>̍</orig>ḻe |</l>'
    l_el = ET.fromstring(xml_str)
    cleaned = VedaParser.clean_line_text(l_el, preserve_accents=False)
    assert cleaned == "agnim īḻe |"
    assert "|" in cleaned


def test_parse_tei_xml_nested_hierarchy(sample_tei_xml: Path):
    """Test that VedaParser correctly extracts Mandala -> Sukta -> Mantra nested hierarchy without redundancy."""
    doc = VedaParser.parse_tei_xml(
        filepath=sample_tei_xml,
        religion="Hinduism",
        collection="Vedic Canon",
        book_title="Ṛgveda-Saṁhitā",
        book_slug="rigveda",
    )

    assert doc["id"] == "rigveda"
    assert doc["totalChapters"] == 1
    assert doc["totalVerses"] == 2

    mandala = doc["chapters"][0]
    assert mandala["number"] == 1
    assert mandala["type"] in ["mandala", "maṇḍala"]
    assert mandala["totalSections"] == 1
    assert mandala["totalVerses"] == 2

    sukta = mandala["sections"][0]
    assert sukta["number"] == 1
    assert sukta["type"] in ["sukta", "sūkta"]
    assert sukta["totalVerses"] == 2
    assert len(sukta["verses"]) == 2

    v1 = sukta["verses"][0]
    assert v1["verse"] == 1
    assert v1["citation"] == "1.1.1"
    assert "agnim īḻe purohitaṁ yajñasya devam ṛtvijam |" in v1["text"]
    assert "hotāraṁ ratnadhātamam ||" in v1["text"]
    assert v1["text"].endswith("||")

    # Verify non-redundancy: inherited fields should not be duplicated inside verse object
    assert "religion" not in v1
    assert "collection" not in v1
    assert "book" not in v1
    assert "language" not in v1

    v2 = sukta["verses"][1]
    assert v2["citation"] == "1.1.2"
    assert "||" in v2["text"]


def test_book_and_verse_schema_compliance(sample_tei_xml: Path):
    """Test that parsed Veda book and verse structures validate against schemas/book.schema.json."""
    repo_root = Path(__file__).parent.parent.resolve()
    book_schema_path = repo_root / "schemas" / "book.schema.json"
    verse_schema_path = repo_root / "schemas" / "verse.schema.json"

    with open(book_schema_path, "r", encoding="utf-8") as f:
        book_schema = json.load(f)

    with open(verse_schema_path, "r", encoding="utf-8") as f:
        verse_schema = json.load(f)

    resolver = jsonschema.RefResolver(
        base_uri=book_schema_path.as_uri(),
        referrer=book_schema,
        store={
            "verse.schema.json": verse_schema,
            verse_schema.get("$id", ""): verse_schema,
        },
    )

    doc = VedaParser.parse_tei_xml(
        filepath=sample_tei_xml,
        religion="Hinduism",
        collection="Vedic Canon",
        book_title="Ṛgveda-Saṁhitā",
        book_slug="rigveda",
    )

    # Validate full book document
    validator = jsonschema.Draft202012Validator(book_schema, resolver=resolver)
    validator.validate(doc)


def test_sub_index_structure(sample_tei_xml: Path):
    """Test that generate_sub_index creates a valid structured Veda sub-index."""
    doc = VedaParser.parse_tei_xml(
        filepath=sample_tei_xml,
        religion="Hinduism",
        collection="Vedic Canon",
        book_title="Ṛgveda-Saṁhitā",
        book_slug="rigveda",
    )

    sub_index = generate_sub_index(doc, "rigveda")
    assert sub_index["vedaId"] == "rigveda"
    assert sub_index["totalMandalas"] == 1
    assert sub_index["totalSuktas"] == 1
    assert sub_index["totalMantras"] == 2

    mandala = sub_index["mandalas"][0]
    assert mandala["mandala"] == 1
    assert mandala["totalSuktas"] == 1
    assert mandala["totalMantras"] == 2

    sukta = mandala["suktas"][0]
    assert sukta["sukta"] == 1
    assert sukta["totalMantras"] == 2
    assert sukta["citationPrefix"] == "1.1"
    assert sukta["verseRange"] == "1.1.1 - 1.1.2"
    assert "agnim īḻe" in sukta["previewText"]
