# LLM Knowledge Base

Use this reference when turning scattered files, browser work, and monitoring into a durable knowledge system that future agents can reuse.

## Operating Model

The project is a living knowledge base:

- `raw/` is evidence. It stores original material, captures, extracts, screenshots, transcripts, competitor pages, and dated observations.
- `wiki/` is distilled memory. It stores stable company, product, persona, market, method, competitor, region, and glossary knowledge.
- `web/` is publishable output. It stores drafts, pages, posts, published indexes, AllinCMS IDs, routes, and SEO/GEO metadata.

Never skip from raw source directly to publishing unless the task is explicitly a tiny edit and the source truth is already in `wiki/`.

## Karpathy-Style Wiki Rules

Treat the knowledge base as context engineering, not prompt stuffing:

1. Keep raw append-only.
2. Distill repeatedly into small wiki pages.
3. Use indexes so agents can retrieve the right page without reading everything.
4. Keep facts, interpretations, and open questions separate.
5. Attach source paths to claims.
6. Prefer durable abstractions over conversation summaries.
7. Convert repeated user corrections into SOP rules after approval.
8. Evaluate outputs against real tasks, not against whether they sound polished.

## Retrieval Shape

Every important page should be chunk-friendly:

- short title
- one scope sentence
- stable headings
- bullets or compact tables for facts
- explicit source links to `raw/`
- open questions
- last reviewed date when the fact can drift

Avoid giant "everything" pages. Split by product, persona, region, competitor, method, or site section.

## Content Memory Loop

For each run:

1. Capture sources to `raw/`.
2. Update indexes immediately.
3. Distill reusable facts to `wiki/`.
4. Write web content from wiki plus task-specific raw evidence.
5. Record what was published and why.
6. Add new lessons, rejected claims, and user corrections back to wiki after approval.

## Agent Handoff Contract

A future agent should be able to answer these without reading chat history:

- What is the site and AllinCMS workspace?
- What products and audiences does it target?
- What sources are trusted?
- What topics are approved, rejected, drafting, and published?
- What images are uploaded and where are they used?
- What competitor targets are monitored?
- What audit score did each published page receive?

If any answer exists only in the chat, move it into `raw/`, `wiki/`, `web/`, `monitoring/`, `media/`, or `audits/` before ending the run.

## Human Approval Gates

Ask before:

- publishing or unpublishing content
- changing product positioning
- using competitor-derived topics
- making claims that need legal, medical, financial, compliance, or safety review
- changing the taxonomy for categories, tags, routes, or glossary terms
- adding long-term SOP or knowledge rules

## Lessons File Contract

`wiki/lessons.md` is the single channel for run-time corrections and new rules. Never silently edit SKILL.md, `references/*`, or `CLAUDE.md` to record a lesson — route it through here so the user can see and approve.

Append entries with this shape:

```yaml
- date: YYYY-MM-DD
  trigger: user_correction | new_scenario | failed_audit | competitor_pattern
  rule: <one sentence, imperative>
  why: <the incident or reasoning>
  scope: skill | project
  proposed_destination: <file:section that should absorb this once approved>
  status: proposed | approved | merged | rejected
```

Rules graduate: `proposed` → user reviews → `approved` → next agent merges into the destination file → `merged`. Reject with a one-line reason instead of deleting; rejected rules document tried-and-failed paths.

Light-mode runs MUST NOT write to `lessons.md`. Only full-mode runs reflect.

## Quality Principle

The knowledge base is successful when it reduces future context cost while increasing factual accuracy. It is failing if agents must reread old chat, repeat the same questions, or publish content that cannot be traced back to sources.
