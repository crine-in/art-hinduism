import json
from pathlib import Path

repo_root = Path(__file__).parent.parent


def test_template_json_syntax():
    """Verify all template JSON files in templates/ parse cleanly."""
    templates_dir = repo_root / "templates"
    template_files = list(templates_dir.glob("*.json"))

    assert len(template_files) > 0, "No JSON templates found in templates/"

    for tf in template_files:
        with open(tf, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict), f"Template {tf.name} must be a JSON object"


def test_example_dataset_validity():
    """Verify the fictional example dataset in data/ parses cleanly."""
    example_orig = repo_root / "data" / "example-collection" / "example-book" / "original.json"
    assert example_orig.exists()

    with open(example_orig, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, dict)
    assert data["totalVerses"] == 3
    assert len(data["chapters"]) == 1
    assert data["chapters"][0]["verses"][0]["citation"] == "1.1"
