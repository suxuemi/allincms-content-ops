# OCR Strategy

How this skill turns documents and images into text. Designed for the common case (text-based PDF / Office files) to need **zero** OCR; OCR is the fallback when the input is image-based or extraction returns thin output.

## Why not Baidu AI Studio (and other hosted OCR)

The skill ingests **competitor screenshots, customer interview screenshots, internal sales decks**. Sending these to a hosted API:

- **Privacy / compliance**: customer data leaving your network may breach GDPR / corporate policy / customer agreements
- **Network egress**: corporate users behind proxies can't reach hosted endpoints
- **Rate limits + auth**: hosted APIs gate at quota, require accounts and rotating keys
- **Single point of failure**: API outage stops your pipeline

For these reasons, **all OCR in this skill runs locally**. No hosted endpoints.

## Tool ladder

Pick by file shape, not by hype:

| Tool | License | Runs on | Strength | Use when |
|---|---|---|---|---|
| **MarkItDown** (Microsoft) | MIT | Python (pipx) | one-shot text PDF / Word / PPT / Excel | **default** — 80% of inputs |
| **PaddleOCR** (Baidu) | Apache 2.0 | Python + ~1 GB models | best Chinese image OCR + scanned PDF | image input OR MarkItDown output sparse |
| pdftotext + pandoc | various | CLI (brew/apt) | fast for plain text PDF / docx | fast-path fallback when MarkItDown not installed |
| **MinerU** (OpenDataLab) | **AGPL-3.0** ⚠️ | Python (heavy) | best for academic / financial PDFs with math + tables | opt-in only; **NEVER** auto-invoked |
| Surya (VikParuchuri) | Apache 2.0 (since 2024) | Python | modern, multi-language alternative to PaddleOCR | when you can't run paddlepaddle |
| EasyOCR (JaidedAI) | Apache 2.0 | Python | simpler API than PaddleOCR | quick prototype |
| Tesseract | Apache 2.0 | CLI | mature, weak on Chinese | last resort |

### MinerU AGPL caveat

MinerU is **AGPL-3.0**. Embedding it in a closed-source service or SaaS will trigger AGPL's network-use clause and force you to release your source. For this reason:

- `ingest_sources.py` **NEVER** auto-invokes MinerU
- This skill only mentions MinerU as an opt-in tool you run manually (`mineru <file.pdf>`)
- If you ship a commercial SaaS that uses MinerU output, talk to legal first

## doctor.py policy (this is what shows up in the dashboard)

| Check | Default treatment | Triggers degraded? |
|---|---|---|
| `extraction × ingest` (ANY-of: markitdown OR (pdftotext + pandoc)) | required | yes — only when **all** missing |
| `chinese_ocr × ingest` (paddleocr) | **optional** | **no** — never red in doctor summary |
| `media_uploader × media` (r2.toml OR PicGo running) | required when publishing images | yes — when both missing |
| `media_mix × media` (media/index.md has ≥ 2 host domains) | informational | warn — but doesn't block |

**`chinese_ocr` is intentionally not degraded by default.** A user who only handles English text PDFs should not be guilted into a 1 GB install. PaddleOCR is recommended only when a specific ingest actually needs it — `ingest_sources.py` surfaces "install paddleocr" in its own per-file report, not in the global doctor dashboard.

## ingest_sources.py fallback chain

```text
input is PDF / DOCX / PPTX / XLSX
  → markitdown <file>
  → output ≥ 100 chars OR input file ≤ 50 KB?
     YES → success, write to raw/
     NO (output thin AND input was substantial)
        → markitdown output preserved to .raw/<source>.markitdown.md (not discarded)
        → paddleocr installed?
           YES → run paddleocr; output preserved to .raw/<source>.paddleocr.md
                 use longer of the two as raw/
           NO  → report "want OCR? install: pip install paddleocr paddlepaddle"
                 use markitdown output anyway
  → markitdown not installed
     → fast-path: pdftotext / pandoc (legacy CLI)
     → still failed → EXTRACTION FAILED + install prompt

input is image (.png/.jpg/.webp)
  → paddleocr installed?
     YES → paddleocr direct → write to raw/
     NO  → "want image OCR? install: pip install paddleocr paddlepaddle"
            + skip the file (don't write empty raw/)
```

### Constants (locked by tests/test_doctor_extraction_matrix.py)

- `EXTRACTION_MIN_CHARS = 100` — output below this on a substantial input triggers OCR fallback
- `INPUT_SUBSTANTIAL_BYTES = 50_000` — inputs above this are considered "substantial" (a one-page short PDF won't trigger fallback unintentionally)

Why these numbers: fixture corpus `tests/fixtures/short_pdfs/` has median 187 chars, so 100 catches roughly 30% percentile = real bad extractions. The dual gate prevents misfires on legitimately short inputs.

## Install recipes

### Default (Chinese-friendly content ops)

```bash
pipx install markitdown
pip install paddleocr paddlepaddle pdf2image       # when first image/scanned PDF arrives
```

### Minimum (English-only, lightweight)

```bash
pipx install markitdown
# paddleocr can wait — install only if ingest_sources.py asks for it
```

### Fast-path (existing pdftotext + pandoc users)

```bash
# nothing to do — fast-path keeps working
# upgrade path: when convenient, `pipx install markitdown` to cover Excel etc.
```

### Heavy (academic PDFs)

```bash
pipx install markitdown
pip install paddleocr paddlepaddle pdf2image
pipx install mineru   # AGPL — only for self-use; not for SaaS embedding
# Then run `mineru <file>` manually when needed; ingest_sources.py never calls it.
```

## Why no audio / video this release

Audio / video transcription needs Whisper (1+ GB) or a hosted API. Both have heavy implications (model size or privacy). Punted to v0.9+ or later — when there's a real use case.

## Privacy commitment

The skill ships zero hosted-API integrations for OCR. If a future maintainer wants to add one:

1. It must be opt-in via an explicit flag (never default).
2. Documentation must list every byte that gets sent.
3. `doctor.py` must report "data leaves your machine" as a degraded signal so users see it.
