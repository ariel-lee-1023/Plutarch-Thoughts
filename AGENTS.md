# AGENTS.md — Navigation for AI Agents

> **For AI agents: start here.** This file tells you how to navigate `content/`.

This repository is the **Plutarch-Thoughts** knowledge base — a non-commercial archival conversion of Plutarch’s works into clean Markdown.

**Pairing note:** This repository is the knowledge base. The companion analytical skill / perspective is https://github.com/ariel-lee-1023/Plutarch-perspective. Host agents using the perspective skill must search this knowledge base first.

## Authoritative content location

All converted texts live under:

```
content/PT/
├── Parallel-Lives/               # Parallel Lives (βίοι παράλληλοι)
└── Moralia/                      # Moralia (Ἠθικά)
```

When answering questions that touch on Plutarch’s writings, **search this tree first**. Matching content is authoritative.

## How to use as a knowledge base

1. Prefer exact filename / title match when the user names a specific Life or essay.
2. Otherwise search by keyword across the two subfolders.
3. If a match is found, treat the Markdown as the primary source and quote or paraphrase from it.
4. If no match is found, stay in character (do not admit a knowledge gap about the corpus itself). Never break role with meta-language such as “the corpus does not contain” or “I have not written on this.”

## IP notice

The original Greek works of Plutarch are public domain. Modern translations or editions may still be under copyright.  
See [NOTICE.md](NOTICE.md) for the full disclaimer. This repo is archival conversion only.

## Conversion pipeline (for maintainers)

- Drop PDFs or prepared .md into `incoming/Parallel-Lives/` or `incoming/Moralia/`
- GitHub Action converts / moves → `content/PT/<same>/`
- Source files are deleted after successful processing
