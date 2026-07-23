import pytest
from pathlib import Path
import sys

repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

from validators.validate_json import validate_json_syntax
from validators.validate_schema import validate_schemas
from validators.validate_ids import validate_ids
from validators.validate_utf8 import validate_utf8_and_newlines
from validators.validate_filenames import validate_filename_conventions
from validators.validate_metadata import validate_metadata_completeness


def test_json_syntax():
    assert validate_json_syntax(repo_root) is True


def test_schemas():
    assert validate_schemas(repo_root) is True


def test_ids():
    assert validate_ids(repo_root) is True


def test_utf8():
    assert validate_utf8_and_newlines(repo_root) is True


def test_filenames():
    assert validate_filename_conventions(repo_root) is True


def test_metadata():
    assert validate_metadata_completeness(repo_root) is True
