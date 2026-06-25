# Media, Region Rules, and PicGo

## Media Extraction

For source files:

- PDF: extract text, tables, page images, and diagrams where useful.
- PPT/PPTX: extract slide text and speaker notes; export important slides as images.
- MP4: transcribe or summarize; extract frames only when they show a product, UI, process, or proof.
- DOC/DOCX: preserve headings, tables, and lists.
- Web pages: store URL, capture date, title, main text, and screenshot.
- Spreadsheets/CSV: extract product tables, pricing, specifications, and glossary terms.

Always save the original source in `raw/` and derived Markdown beside it.

Use `scripts/ingest_sources.py` for baseline extraction. It can copy local files/directories, fetch URLs, extract text from common text/HTML inputs, and use optional local tools such as `pdftotext` or `pandoc` when installed. If extraction is unavailable, it still stores the original and writes a manual-summary placeholder.

## Regional Visual Norms

Before generating or editing images, define:

- Target region and language.
- Industry visual norms.
- Buyer sophistication.
- Required units, currency, formats, and regulatory sensitivities.
- Whether people/faces are appropriate.
- Whether screenshots should show Chinese, English, or localized UI.
- Whether local law, platform norms, or buyer expectations require different claims, disclaimers, or imagery.

For B2B export SaaS, prefer:

- clean product screenshots
- workflow diagrams
- comparison tables
- launch checklists
- restrained colors
- real UI over generic stock photos

Avoid:

- random office stock photos
- generic AI illustrations
- illegible screenshots
- decorative gradients with no product signal
- red annotation arrows unless the article is explicitly a tutorial

## Image Repair

Before upload:

- Crop to the main subject.
- Remove browser chrome or sensitive data when needed.
- Resize to AllinCMS region requirements.
- Compress while preserving readability.
- Rename with descriptive slug.
- Write alt text and caption.

## PicGo Upload

Use `scripts/picgo_batch_upload.py` when a local PicGo server is running.

Expected local API pattern:

```bash
python3 allincms-content-ops/scripts/picgo_batch_upload.py media/processed --out media/uploaded/picgo-manifest.json
```

Environment variables:

- `PICGO_SERVER`, default `http://127.0.0.1:36677`
- `PICGO_ENDPOINT`, default `/upload`

After upload:

- Replace local image paths in `web/drafts`.
- Record uploaded URL, source path, alt text, and usage page in `media/index.md`.
- Verify remote URLs load before publishing.
- Use a unique cover per article unless the user explicitly approves reuse for a series.
