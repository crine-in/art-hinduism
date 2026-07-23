# CONTRIBUTING TO THIS DATASET REPOSITORY

Thank you for contributing to this **All Religious Texts (ART)** dataset repository maintained by **CRINE** ([www.crine.in](https://www.crine.in)).

---

## Development & Contribution Steps

1. **Fork & Clone Repository**:
   ```bash
   git clone https://github.com/crine-in/art-<tradition>.git
   cd art-<tradition>
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Add or Edit Dataset**:
   * Create folder structure: `data/<collection>/<book>/`
   * Copy templates from `templates/`
   * Format JSON: `python3 scripts/format_json.py`
   * Generate checksums: `python3 scripts/generate_checksums.py`

3. **Validate**:
   ```bash
   python3 validators/run_all.py
   pytest tests/
   ```

4. **Submit PR**: Follow Conventional Commits format (`feat`, `fix`, `docs`).
