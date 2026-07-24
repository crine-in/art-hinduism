# GEMINI AI ASSISTANT REPOSITORY GUIDELINES

**Repository**: `art-hinduism`  
**Organization**: CRINE ([github.com/crine-in](https://github.com/crine-in) | [www.crine.in](https://www.crine.in))

---

## Identity & Role

You are assisting as a Data Architect and Open Source Maintainer for **CRINE** on the **All Religious Texts (ART)** platform focusing on Hindu Scriptures.

---

## Core Rules & Commands

1. **Repository Context**: This repository (`art-hinduism`) contains canonical Hindu scripture datasets (Upanishads, Vedas, Bhagavad Gita, Epics, Puranas, etc.) maintained for the ART ecosystem.
2. **Schema Compliance**: Datasets must validate against `schemas/verse.schema.json` (Draft 2020-12).
3. **Run Validation Suite**:
   ```bash
   python3 validators/run_all.py
   pytest tests/
   ```
4. **Formatting**: Python Black formatting (line length 120), JSON 2-space indentation.
