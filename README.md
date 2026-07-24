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
* **Standard Data Layout**: `data/<collection>/<book>/` hierarchy
* **Reusable Templates**: Pre-made `metadata.json`, `sources.md`, `LICENSE`, and `ATTRIBUTION.md` templates in `templates/`
* **JSON Schemas**: Draft 2020-12 schemas in `schemas/` inherited from `all-religious-texts`
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

### 2. Add a New Hindu Scripture Dataset

```bash
# 1. Copy book template to target collection and book directory
mkdir -p data/principal-upanishads/isha-upanishad
cp -r templates/* data/principal-upanishads/isha-upanishad/

# 2. Enrich draft dataset to verse.schema.json
python3 tools/enrich_dataset.py \
  --input isha_draft.json \
  --output data/principal-upanishads/isha-upanishad/original.json \
  --book "Isha Upanishad" \
  --collection "Principal Upanishads" \
  --religion "Hinduism"

# 3. Run validation suite
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
│   ├── book.json             # Book structural metadata template
│   ├── verse.json            # Verse schema template
│   ├── translation.json      # Translation template
│   ├── commentary.json       # Commentary template
│   ├── LICENSE               # Text edition license template
│   ├── ATTRIBUTION.md        # Attribution template
│   ├── sources.md            # Bibliography template
│   └── README.md             # Dataset directory guide template
├── data/                     # Scripture dataset directory (e.g. principal-upanishads)
│   └── example-collection/
│       └── example-book/
│           ├── metadata.json
│           ├── LICENSE
│           ├── ATTRIBUTION.md
│           ├── sources.md
│           ├── original.json
│           └── translations/
│               └── english/
│                   └── example.json
├── schemas/                  # Draft 2020-12 JSON Schemas
├── metadata/                 # Master registries (religions, collections, languages, etc.)
├── validators/               # Python CLI validation suite
├── tools/                    # Conversion & enrichment utilities
├── scripts/                  # Formatting, checksums, renumbering scripts
├── docs/                     # Detailed developer guides
├── tests/                    # Automated unit tests
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
