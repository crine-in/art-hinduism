# art-hinduism

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Build & Validation](https://github.com/crine-in/art-hinduism/actions/workflows/validate.yml/badge.svg)](.github/workflows/validate.yml)
[![Ecosystem Standard](https://img.shields.io/badge/CRINE-Ecosystem%20Dataset-emerald.svg)](https://www.crine.in)

> **Official Hindu Scripture Dataset Repository for the All Religious Texts (ART) Ecosystem.**
>
> Maintained by [**CRINE**](https://www.crine.in) ([github.com/crine-in](https://github.com/crine-in)).

---

## Overview

**`art-hinduism`** is the canonical Hindu scripture dataset repository within the **All Religious Texts (ART)** ecosystem maintained by CRINE. It hosts structured, open, and machine-readable digital archives of Hindu scriptures including the Upanishads, Bhagavad Gita, Vedas, Epics (Ramayana, Mahabharata), and Puranas in original languages (Sanskrit IAST/Devanagari) alongside verified translations and commentaries.

It provides a standardized, pre-configured foundation including:
* **Standard Data Layout**: Verse-level split data in `data/<collection>/<book>/` and whole un-split datasets in `whole/<collection>/<book>/`
* **Whole Scripture Corpus**: 802 un-split scripture datasets in `whole/` with structured metadata, reference systems, and multi-script Indic transliterations
* **Reusable Templates**: Pre-made `metadata.json`, `whole_book.json`, `book.json`, `verse.json`, `sources.md`, `LICENSE`, and `ATTRIBUTION.md` templates in `templates/`
* **JSON Schemas**: Draft 2020-12 schemas in `schemas/` (`whole_book.schema.json`, `verse.schema.json`, `book.schema.json`, `metadata.schema.json`)
* **Zero-Config Validation Suite**: CLI validators in `validators/` requiring no code modifications
* **GitHub Actions Workflows**: Automated validation, linting, and release packaging in `.github/workflows/`
* **AI IDE Instructions**: Full assistant guidelines in `GEMINI.md`, `SKILLS.md`, `.cursorrules`, and `CLAUDE.md`

---

## Repository Setup & Usage

### 1. Clone & Environment Setup
```bash
git clone https://github.com/crine-in/art-hinduism.git
cd art-hinduism
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Build Whole Scripture Datasets & Transliterations

```bash
# Build whole un-split scripture datasets from TEI XML files into whole/
python3 tools/build_whole_datasets.py --force

# Generate Indic script transliterations for whole datasets
python3 tools/generate_whole_transliterations.py --force

# Run validation suite and test suite
python3 validators/run_all.py
pytest tests/
```

---

## Directory Structure

```text
art-hinduism/
├── README.md                 # Primary repository documentation & setup guide
├── LICENSE                   # MIT License for codebase & tools
├── ATTRIBUTION.md            # Provenance and source credits
├── CONTRIBUTING.md           # Contribution guidelines for this repository
├── CODE_OF_CONDUCT.md        # Community Code of Conduct
├── SECURITY.md               # Vulnerability reporting procedures
├── CHANGELOG.md              # Dataset release history
├── .gitignore                # Git ignore patterns
├── pyproject.toml            # Python packaging and tool configuration
├── requirements.txt          # Dependencies for validation suite & tools
├── .github/                  # CI/CD workflows, issue templates, PR template
│   ├── workflows/            # GitHub Actions (validate.yml, lint.yml, release.yml)
│   └── ISSUE_TEMPLATE/       # GitHub issue templates
├── templates/                # Reusable metadata & scripture templates
│   ├── metadata.json         # Folder metadata template
│   ├── whole_book.json       # Whole scripture template
│   ├── book.json             # Book structural metadata template
│   ├── verse.json            # Verse schema template
│   ├── translation.json      # Translation template
│   └── ...
├── whole/                    # Complete, un-split scripture corpus (802 scriptures)
│   ├── index.json            # Master JSON index database (802 records)
│   ├── index.db              # Master SQLite index database
│   ├── metrics.json          # Aggregated corpus stats & keyword metrics
│   ├── README.md             # Whole corpus documentation
│   ├── LICENSE               # General whole corpus license
│   ├── ATTRIBUTION.md        # Master whole corpus attributions
│   └── <collection-slug>/<book-slug>/
│       ├── whole.json        # Clean whole text (Sanskrit IAST)
│       ├── metadata.json     # Complete cataloging metadata & keywords
│       ├── LICENSE           # Text edition license
│       ├── ATTRIBUTION.md    # Source notes & editor attributions
│       └── translations/<script>/indic-transliteration.json
├── data/                     # Verse-level split scripture dataset directory
├── schemas/                  # Draft 2020-12 JSON Schemas (whole_book.schema.json, etc.)
├── metadata/                 # Master registries & GRETIL index metadata
├── validators/               # Python CLI validation suite
├── tools/                    # Conversion, whole dataset builder & transliteration tools
│   ├── parsers/
│   │   ├── tei_whole_parser.py  # TEI XML Whole Scripture Parser
│   │   └── veda_parser.py
│   ├── build_whole_datasets.py  # Whole Dataset Builder & Indexer
│   └── generate_whole_transliterations.py  # Whole Indic Transliteration Engine
├── scripts/                  # Formatting and maintenance scripts
├── docs/                     # Detailed developer guides
├── tests/                    # Automated unit tests (test_tei_whole_parser.py, etc.)
└── GEMINI.md                 # AI IDE context & instructions
```

---

## Validation Suite

Verify clean compliance across all datasets, templates, schemas, and metadata:

```bash
python3 validators/run_all.py
pytest tests/
```

---

## Licensing

* **Infrastructure & Tooling**: [MIT License](LICENSE).
* **Metadata & Specifications**: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
* **Imported Scriptures**: Retain their original public-domain or open CC licenses.

---

## Organization & Contact

* **Organization**: CRINE
* **GitHub**: [github.com/crine-in](https://github.com/crine-in)
* **Website**: [www.crine.in](https://www.crine.in)
