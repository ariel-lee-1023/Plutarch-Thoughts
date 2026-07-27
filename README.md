# Plutarch-Thoughts

**For AI agents: start with [AGENTS.md](AGENTS.md) — it tells you how to navigate `content/`.**

Archive of **Plutarch** (Πλούταρχος) works → clean Markdown.

> **Intellectual Property Notice**  
> The original works of **Plutarch** (c. 46–120 AD) are in the public domain.  
> Modern translations, editions, or specific PDF sources may still carry copyright belonging to their respective holders.  
> This repository claims no ownership of any underlying copyrighted material.  
> See [NOTICE.md](NOTICE.md) for the full disclaimer.

## Recommended pairing

This repository is the knowledge base.  
For the analytical perspective / skill, use https://github.com/ariel-lee-1023/Plutarch-perspective.git.  
One supplies the primary sources; the other supplies the interpretive frame.

## How to use (drop-folder workflow)

1. Obtain the PDFs (or already-prepared Markdown) of Plutarch’s works.
2. Upload them into the matching drop folder:

```
incoming/
├── Parallel-Lives/     # Parallel Lives
└── Moralia/            # Moralia
```

3. Push (or just upload via the GitHub web UI).  
   The Action will automatically:
   - **PDF** → convert with **PyMuPDF** + layout cleanup & paragraph reflow + mobile length balancing → write `.md` into `content/PT/<same>/` and delete the source PDF
   - **Markdown (.md)** → move as-is into `content/PT/<same>/` and delete from incoming
   - commit & push the result

You can also trigger it manually: **Actions → Process incoming files → Run workflow**.

## Automatic content formatting optimizer

Existing Markdown under `content/PT/` is kept mobile-friendly by:

- `scripts/optimize_formatting.py` — re-applies spacing cleanup, intelligent paragraph reflow, length balancing (~420 chars max per block, split only at sentence ends).
- GitHub Action **Optimize content formatting** runs on every Monday (03:00 UTC) and can be triggered manually.

No author wording is ever changed — only layout and blank-line hierarchy.

## Output layout

```
content/
└── PT/
    ├── Parallel-Lives/
    │   └── <name>.md
    └── Moralia/
        └── <name>.md
```

## Notes

- Extraction uses PyMuPDF (layout-aware).  
  Post-processing joins mid-sentence lines across page breaks, balances paragraph length for mobile reading, and removes obvious TOC artifacts (leader dots, pure page-number lines).
