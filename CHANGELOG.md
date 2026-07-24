# CHANGELOG

All notable changes to the **`art-hinduism`** repository will be documented in this file.

The project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-07-25

### Added
* **Whole Scripture Dataset Architecture (`whole/`)**:
  * Ingested and structured 802 complete, un-split scripture datasets (`whole.json`) with line-break preserved text (`\n`) and essential reading parameters.
  * Added `schemas/whole_book.schema.json` (Draft 2020-12) and `templates/whole_book.json`.
  * TEI Whole Scripture Parser (`tools/parsers/tei_whole_parser.py`) with automatic single-line reference system extraction (`referenceSystem`) and `--`-split keyword term array extraction (`keywords`).
  * Whole Dataset Builder & Indexer (`tools/build_whole_datasets.py`) with multi-process pool, generating `whole.json`, `metadata.json`, `LICENSE`, `ATTRIBUTION.md`, `sources.md`, `whole/index.json`, `whole/index.db`, `whole/metrics.json`, `whole/README.md`, `whole/LICENSE`, and `whole/ATTRIBUTION.md`.
  * Whole Indic Transliteration Engine (`tools/generate_whole_transliterations.py`) supporting line-by-line transliteration into 11 Indic scripts (Devanagari, Bengali, Grantha, Gujarati, Gurmukhi, Kannada, Malayalam, Odia, Telugu, Sharada, Tamil).
  * Corpus metrics aggregation in `whole/metrics.json` tracking total scriptures (802), lines (2,180,022), words (17,738,936), religion breakdowns, collection counts, and keyword frequencies.
  * Comprehensive test suite in `tests/test_tei_whole_parser.py` testing TEI whole parsing, schema compliance, dataset building, and Indic transliteration.

### Changed
* Reduced data redundancy in `whole.json` by maintaining comprehensive cataloging metadata in `metadata.json`.
* Removed checksum calculation and `checksum` properties across whole dataset schemas, parsers, and build tools.

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
