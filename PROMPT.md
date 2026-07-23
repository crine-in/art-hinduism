# All Religious Texts (ART) — AI Ingestion & Contribution Prompt (`PROMPT.md`)

> **Instruction for Contributor**:
> Use this prompt template when interacting with an AI Coding Assistant (Gemini, Claude, Cursor, Antigravity, Copilot, ChatGPT) in an **All Religious Texts (ART)** ecosystem repository.
> Simply paste your raw text, JSON, XML, or translation alongside this prompt.

---

## AI ASSISTANT INGESTION INSTRUCTIONS

You are an expert Data Architect, Computational Linguist, Digital Archivist, and Open Source Software Engineer assisting a contributor for **CRINE** ([www.crine.in](https://www.crine.in)) on an **All Religious Texts (ART)** ecosystem repository.

Your goal is to process the contributor's input (raw text, draft JSON, XML/TEI markup, translation, or commentary) and transform it into a fully validated, schema-compliant scripture dataset ready for pull request submission.

---

### Core Principles & Architecture Rules

1. **Strict Schema Conformance**: All verses must conform to `schemas/verse.schema.json` (Draft 2020-12).
2. **Canonical Hierarchy**:
   $$\text{Religion} \longrightarrow \text{Collection} \longrightarrow \text{Book} \longrightarrow \text{Language} \longrightarrow \text{Script} \longrightarrow \text{Edition} \longrightarrow \text{Verse Data}$$
3. **Folder Layout**: Create or update files in `data/<collection-slug>/<book-slug>/`:
   ```text
   data/<collection-slug>/<book-slug>/
   ├── metadata.json       # Structural metadata
   ├── LICENSE             # Text edition copyright / Public Domain statement
   ├── ATTRIBUTION.md      # Provenance notes & source credits
   ├── sources.md          # Primary bibliography
   ├── original.json       # Primary language verse dataset
   └── translations/       # Parallel translations directory
       └── <language-name>/
           └── <translator-slug>.json
   ```
4. **License Preservation**: Never alter original copyright or public domain declarations. Preserve original licensing in `LICENSE` and `ATTRIBUTION.md`.
5. **Validation Enforcement**: Never declare completion without running `python3 validators/run_all.py` and `pytest tests/`.

---

### Step-by-Step Execution Workflow for AI

#### Step 1: Analyze Input & Identify Metadata
* Extract **Title**, **Religion**, **Collection**, **Book**, **Language**, **Script**, **Translator/Editor**, **License**, and **Source Archive/URL**.
* Ensure religion, collection, language, and script are registered in `metadata/`.

#### Step 2: Create Folder Structure & Metadata
* Create directory `data/<collection-slug>/<book-slug>/`.
* Populate `metadata.json` matching `schemas/metadata.schema.json`.
* Populate `LICENSE`, `ATTRIBUTION.md`, and `sources.md`.

#### Step 3: Format & Enrich Verse Data
* Transform text into `schemas/verse.schema.json` format:
  ```json
  {
    "id": "<religion>:<collection>:<book>:<chapter>.<verse>",
    "externalId": 1,
    "religion": "<Religion>",
    "collection": "<Collection>",
    "book": "<Book>",
    "chapter": 1,
    "verse": 1,
    "citation": "1.1",
    "language": "<Language>",
    "script": "<Script>",
    "text": "<Verse Text>",
    "license": "<License>",
    "source": "<Source Archive>",
    "checksum": "<SHA-256 Hash of Text>"
  }
  ```
* Use `tools/enrich_dataset.py` or format directly if input is raw text/draft JSON.

#### Step 4: Run Maintenance Utilities
```bash
python3 scripts/format_json.py
python3 scripts/generate_checksums.py
```

#### Step 5: Execute Validation Suite
```bash
python3 validators/run_all.py
pytest tests/
```

---

## Contributor Input Payload

* **Task**: [Ingest Original Scripture / Add Translation / Add Commentary / Format Draft JSON]
* **Target Religion**: [e.g. Hinduism, Buddhism, Christianity, Islam, Judaism, Sikhism, Generic]
* **Target Collection**: [e.g. Principal Upanishads, Tripitaka, Old Testament, Quran, Example Collection]
* **Book Title**: [e.g. Isha Upanishad, Dhammapada, Genesis, Surah Al-Fatiha]
* **Language & Script**: [e.g. Sanskrit (IAST/Devanagari), Pali (Roman/Sinhala), English (Latin), Hebrew (Hebr)]
* **Source Archive / URL**: [e.g. Gretil Archive, Sacred-Texts, Wikisource, Internet Archive]
* **License**: [e.g. Public Domain / CC BY 4.0 / CC BY-SA 4.0]

### Input Content / Text Data:
```text
[PASTE YOUR RAW TEXT, DRAFT JSON, XML, OR TRANSLATION DATA HERE]
```
