# Competitor Monitoring

## Purpose

Use competitor monitoring to discover topics, objections, feature framing, buyer language, pricing movement, content gaps, and SERP/GEO opportunities. Do not copy competitor wording or structure.

## Monitor Index

Store monitored targets in `monitoring/competitors.yml`:

```yaml
competitors:
  - name:
    domain:
    pages:
      - url:
        type: pricing|blog|docs|product|case-study|changelog
        cadence: weekly
        notes:
```

Run:

```bash
python3 allincms-content-ops/scripts/monitor_competitors.py <project-root>
```

Every run creates:

```text
monitoring/runs/YYYY-MM-DD/
  fetch-log.md
  diff-summary.md
  topics.md
```

Raw captures go to:

```text
raw/competitors/YYYY-MM-DD-competitor-name/
```

Update `raw/competitors/index.md` every time.

## Topic Extraction

For each new or changed competitor item, extract:

- Topic
- Page URL
- Buyer pain
- Search intent
- Competitor angle
- Missing proof or weakness
- Our product angle
- Needed raw/wiki sources
- Proposed content type
- Priority
- Approval status

Add approved opportunities to `wiki/content-opportunities.md`.

Also add rejected topics with the reason. Rejections are useful training data for future topic selection.

## User Confirmation Gate

Monitoring may propose topics automatically, but it must not publish automatically. Ask the user to confirm:

- topic
- target persona
- route/category/tags
- whether to write, generate images, and publish

If the user approves a batch, still keep one row per topic with approval status, source URL, proposed route, category, tags, and target query.

## Anti-Copy Rule

Use competitor content for:

- gaps
- terminology
- objections
- structure awareness
- market movement

Do not use it for:

- copied paragraphs
- copied screenshots unless rights allow it
- fake comparisons
- unsupported claims
