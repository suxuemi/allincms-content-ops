[中文](../../QUICKSTART.md) | English

# Quickstart

How to ship your first AllinCMS page or article without losing sources, SEO, images, or review status.

## 0. Mode-select first

- **light-mode**: typo, alt-text touch-up, residue-word swap, broken-link replace, image re-upload, OR a single-field patch on `meta_title` / `meta_description` / `summary` / `cover_alt`. Read only the target file + `wiki/glossary.md`, run `audit_content.py --light <file>`, commit, stop. No `lessons.md`, no index updates.
- **full-mode**: create / publish / restructure / change taxonomy / region / claims / cover / search intent, or touch any of `status`, `category`, `tags`, `route`, `slug`, `region`, `search_intent`, `persona`, `differentiation`, `cover_image`, `source_wiki`, `source_raw`. Walk steps 1–11 below.

Unsure → default light, ask once. Never silently escalate light → full.

## 1. Open the index

Read [PROJECT_INDEX.md](../../PROJECT_INDEX.md). **If any `Current Site` field is empty, STOP** and request values from the user. Do not proceed with placeholders.

## 2. Ingest sources

```bash
python3 allincms-content-ops/scripts/ingest_sources.py . path/to/file.pdf --rights "owned"
python3 allincms-content-ops/scripts/ingest_sources.py . https://example.com/source --rights "public web source"
```

Check [raw/index.md](../../raw/index.md). **`raw/` is append-only** — never modify a captured file after `collected_at`. If the source changes, create a new dated capture.

## 3. Distill into wiki

Turn raw material into stable pages:

- company: [wiki/company.md](../../wiki/company.md)
- products: `wiki/products/`
- personas: `wiki/personas/`
- methods: `wiki/methodology/`
- regions: `wiki/regions/`
- glossary: [wiki/glossary.md](../../wiki/glossary.md)

Each wiki page's frontmatter must include `consumed_by: []` listing every web draft that cites it. When a wiki fact changes, walk `consumed_by` to flag affected web pages for re-audit.

Claims that exist only in chat are not publishable — put them in `raw/` or `wiki/` first.

## 4. Choose search intent

Before writing, answer: target customer, query, pain, region/language, supporting evidence from `raw/`/`wiki/`, reader's next action. Use the template in [search-intent.md](../../allincms-content-ops/references/search-intent.md).

## 5. Draft web content

Place under `web/drafts/`, `web/pages/`, `web/posts/`, or `web/products/`.

**Required frontmatter**: `title`, `slug`, `route`, `category`, `tags`, `meta_title`, `meta_description`, `cover_image`, `cover_alt`, `source_wiki`, `source_raw`, **`differentiation`** (how this page beats the strongest competitor URL borrowed from — empty fails audit).

## 6. Prepare images

Use source images first. Crop / annotate / generate only when needed.

PicGo batch upload:

```bash
python3 allincms-content-ops/scripts/picgo_batch_upload.py media/processed --out media/uploaded/picgo-manifest.json
```

Update [media/index.md](../../media/index.md).

## 7. Monitor competitors (optional)

```bash
python3 allincms-content-ops/scripts/monitor_competitors.py .
```

New topics land in [raw/competitors/index.md](../../raw/competitors/index.md) and `wiki/content-opportunities.md`. **Never write or publish a monitored topic without user confirmation.**

## 8. Fill AllinCMS as DRAFT

In the logged-in workspace: title / slug / route / summary / body / category / tags / cover / SEO title / SEO description. **Save as DRAFT — do not publish in this step.** Clear old category / tag / cover residue.

**Generate a reviewer artifact** (see [allincms-backend.md](../../allincms-content-ops/references/allincms-backend.md) → "Generating a reviewer-accessible preview URL"): either a public preview URL or a saved `audits/<slug>-<date>-preview.html`. The reviewer refuses without it.

## 9. Adversarial audit (isolated reviewer)

```bash
python3 allincms-content-ops/scripts/audit_content.py .
python3 allincms-content-ops/scripts/spawn_reviewer.py <slug> \
  --preview-url https://... \
  --competitor https://comp1 --competitor https://comp2 --competitor https://comp3
```

Then spawn a **fresh subagent** (Claude: `Agent` tool `subagent_type=general-purpose`; Codex: new session) with the brief in [codex-adversarial-reviewer.md](../../allincms-content-ops/references/codex-adversarial-reviewer.md). Its only input is the YAML written by `spawn_reviewer.py`.

The reviewer surfaces ≥ 5 objections. Author records each as `accepted` / `rejected` / `deferred`.

Pass (all four required): total ≥ 8.5 **AND** every area ≥ 70% **AND** zero residue **AND** ≥ 5 objections with responses.

Write results to `audits/<slug>-<date>.md` (schema in [audits.md](../../allincms-content-ops/references/audits.md)). `pass:` must be a top-level YAML key with literal `true` / `false`; never write that exact substring elsewhere in the file.

## 10. Publish (gated by audit file)

```bash
python3 allincms-content-ops/scripts/audit_content.py --require-audit-file <slug> .
```

Exit 0 → flip AllinCMS `status` to published. Update [web/published/index.md](../../web/published/index.md), categories, tags, [web/index.md](../../web/index.md).

## 11. Reflect → `wiki/lessons.md` (full-mode only)

Append every user correction / new scenario / failed-audit pattern / competitor angle from this run as a `proposed` entry in [wiki/lessons.md](../../wiki/lessons.md), following the [Lessons File Contract](../../allincms-content-ops/references/llm-knowledge-base.md).

**Never edit SKILL.md or `references/*` directly to record a lesson** — go proposed → user adds `approved_by`/`approved_at` → the next agent's Workflow step 0 merges.

End each round with 3–7 next-topic suggestions and rationale.
