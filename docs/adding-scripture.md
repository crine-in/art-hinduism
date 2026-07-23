# ADDING A NEW SCRIPTURE DATASET

**Organization**: CRINE ([www.crine.in](https://www.crine.in))

---

## Step-by-Step Instructions

1. **Copy Templates**:
   ```bash
   mkdir -p data/<collection-slug>/<book-slug>
   cp -r templates/* data/<collection-slug>/<book-slug>/
   ```

2. **Incorporate & Enrich Verses**:
   Run `tools/enrich_dataset.py` or use appropriate converter in `tools/`.

3. **Format & Generate Checksums**:
   ```bash
   python3 scripts/format_json.py
   python3 scripts/generate_checksums.py
   ```

4. **Validate & Test**:
   ```bash
   python3 validators/run_all.py
   pytest tests/
   ```
