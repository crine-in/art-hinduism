# REPOSITORY DIRECTORY STRUCTURE

**Organization**: CRINE ([www.crine.in](https://www.crine.in))

---

## Data Hierarchy Standard

Downstream dataset repositories created from this template adhere strictly to:

```text
data/
└── <collection-slug>/
    └── <book-slug>/
        ├── metadata.json       # Required book structural metadata
        ├── LICENSE             # Edition copyright / Public Domain terms
        ├── ATTRIBUTION.md      # Provenance and source notes
        ├── sources.md          # Primary bibliography
        ├── original.json       # Primary language text
        └── translations/       # Translations sub-directory
            └── <language>/
                └── <translator-slug>.json
```
