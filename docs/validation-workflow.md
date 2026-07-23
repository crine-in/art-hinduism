# VALIDATION WORKFLOW

Execute CLI validators:
```bash
python3 validators/run_all.py
pytest tests/
```
Checks performed: JSON syntax, JSON Schema Draft 2020-12, master ID uniqueness, UTF-8 encoding, filename conventions, and metadata completeness.
