# Plutarch-Thoughts

**For AI agents: start with [AGENTS.md](AGENTS.md) — it tells you how to navigate `content/`.**

Archive of **Plutarch** (Πλούταρχος) works → clean Markdown.

> **Intellectual Property Notice**  
> The original works of **Plutarch** (c. 46–120 AD) are in the public domain.  
> Modern translations, editions, or specific PDF sources may still carry copyright belonging to their respective holders.  
> This repository claims no ownership of any underlying copyrighted material.  
> See [NOTICE.md](NOTICE.md) for the full disclaimer.

## How to use (drop-folder workflow)

1. Obtain the PDFs of Plutarch’s works (Lives, Moralia, etc.).
2. Upload them into the drop folder:

```
incoming/
└── Works/
```

3. Push (or just upload via the GitHub web UI).  
   The Action will automatically:
   - convert every `*.pdf` with **PyMuPDF** + layout cleanup & paragraph reflow + mobile length balancing
   - write the `.md` files into `content/PT/Works/`
   - delete the source PDF (keeps the repo light)
   - commit & push the result

You can also trigger it manually: **Actions → Convert incoming PDFs → Run workflow**.

## Automatic content formatting optimizer

Existing Markdown under `content/PT/` is kept mobile-friendly by:

- `scripts/optimize_formatting.py` — re-applies spacing cleanup, intelligent paragraph reflow, length balancing (~420 chars max per block, split only at sentence ends).
- GitHub Action **Optimize content formatting** runs on every Monday (03:00 UTC) and can be triggered manually.

No author wording is ever changed — only layout and blank-line hierarchy.

## Output layout

```
content/
└── PT/
    └── Works/
        └── <original-name>.md
```

## Notes

- Extraction uses PyMuPDF (layout-aware).  
  Post-processing joins mid-sentence lines across page breaks, balances paragraph length for mobile reading, and removes obvious TOC artifacts (leader dots, pure page-number lines).
