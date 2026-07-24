# CHANGELOG

All notable changes to the **`art-hinduism`** repository will be documented in this file.

The project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-07-25

### Added
* Categorized sub-index JSON files created under `metadata/`:
  * `religions/`: Sub-indexes for Hinduism, Buddhism, and Jainism.
  * `canons/`: Sub-indexes for Vedic Canon, Śāstra & Philosophy, Kāvya & Literature, Purāṇas, etc.
  * `categories/`: Sub-indexes for Sūtra, Veda, Bhāṣya (Commentary), Tantra, Gītā, Stotra, etc.
  * `languages/`: Sub-indexes by language.
  * `transliterations/`: Sub-indexes by transliteration schemes.
* `metadata/gretil_stats.json` containing master repository metrics: 802 texts, 40,661 chapters, 1,362,158 total verses, and comprehensive breakdown statistics across all dimensions.

---

## [1.1.0] - 2026-07-24

### Added
* Veda dataset builder (`tools/build_veda_datasets.py`) and dedicated Veda parser (`tools/parsers/veda_parser.py`).
* Canonical Vedic data structures and sub-index files in `metadata/vedas/` (Ṛgveda, Sāmaveda, Atharvaveda Paippalāda, Vedāṅga-Jyotiṣa, etc.).
* Automated transliteration generator (`tools/generate_transliterations.py`) and devanagari mapping registries in `metadata/devanagari/`.
* GRETIL TEI header parser (`tools/parse_gretil_headers.py`) and dataset builder (`tools/build_art_datasets.py`) with parallel processing (`tools/generate_all_max_parallel.py`).
* Test suites for transliteration generation (`tests/test_transliteration.py`) and Veda parsing (`tests/test_veda_parser.py`).

---

## [1.0.0] - 2026-07-23

### Added
* Initialized official `art-hinduism` repository for **CRINE** ([www.crine.in](https://www.crine.in)).
* Added reusable dataset templates in `templates/` (`metadata.json`, `book.json`, `verse.json`, `translation.json`, `commentary.json`, `LICENSE`, `ATTRIBUTION.md`, `sources.md`, `README.md`).
* Added JSON Schemas in `schemas/` and master registries in `metadata/`.
* Integrated CLI validation suite in `validators/` (`run_all.py`, `validate_json.py`, `validate_schema.py`, `validate_ids.py`, `validate_utf8.py`, `validate_filenames.py`, `validate_metadata.py`).
* Integrated ingestion tools in `tools/` and maintenance scripts in `scripts/`.
* Added GitHub Action workflows in `.github/workflows/` (`validate.yml`, `lint.yml`, `release.yml`).
* Added complete developer guides in `docs/` and AI IDE context rules (`GEMINI.md`, `SKILLS.md`, `AGENTS.md`, `.cursorrules`, `CLAUDE.md`).
