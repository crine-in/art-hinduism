# CHANGELOG

All notable changes to the **`art-template`** starter repository will be documented in this file.

The project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-07-23

### Added
* Initialized official `art-template` repository for **CRINE** ([www.crine.in](https://www.crine.in)).
* Added reusable dataset templates in `templates/` (`metadata.json`, `book.json`, `verse.json`, `translation.json`, `commentary.json`, `LICENSE`, `ATTRIBUTION.md`, `sources.md`, `README.md`).
* Added fictional example dataset in `data/example-collection/example-book/`.
* Added JSON Schemas in `schemas/` and master registries in `metadata/`.
* Integrated CLI validation suite in `validators/` (`run_all.py`, `validate_json.py`, `validate_schema.py`, `validate_ids.py`, `validate_utf8.py`, `validate_filenames.py`, `validate_metadata.py`).
* Integrated ingestion tools in `tools/` and maintenance scripts in `scripts/`.
* Added GitHub Action workflows in `.github/workflows/` (`validate.yml`, `lint.yml`, `release.yml`) and issue templates.
* Added complete developer guides in `docs/`.
* Integrated AI IDE instructions (`GEMINI.md`, `SKILLS.md`, `AGENTS.md`, `.cursorrules`, `CLAUDE.md`).
