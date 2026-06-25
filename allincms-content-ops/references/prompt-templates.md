# Prompt Templates

Reusable prompts for SOP steps. Copy verbatim into the LLM of your choice; replace `{{...}}` with project values from `wiki/` and `monitoring/`.

These are starting points, not contracts. The contracts live in SKILL.md and `references/audits.md`.

## Step 3 — Customer persona extraction (from raw materials)

```
You are an industry content analyst. Read the materials I paste below and extract:

1. Top 3 product categories my product fits into (e.g. [foreign-trade independent site, lead capture, AI marketing]).
2. The most likely buyer personas (3–5), each as: title + size of company + region + decision trigger.
3. For each persona: top pain points (concrete, not "efficiency"), real-world buying triggers, and 1–2 typical search queries they would actually type (in the persona's language).

Output as YAML I can drop into `wiki/personas/*.md`. No commentary outside the YAML.

Materials:
{{paste raw extracts here}}
```

## Step 3 — Search-intent brief

```
You write SEO briefs for a foreign-trade SaaS site. Given the persona and primary query below, produce a brief with these fields:

- persona (one-line)
- region
- primary_query
- secondary_queries (3–5, including long-tail)
- funnel_stage (awareness | consideration | decision)
- buyer_objections (3, concrete)
- proof_we_have (link wiki/raw paths if known)
- desired_conversion (one action)
- competitor_urls (3 URLs that currently rank or get cited by AI)
- differentiation (one sentence: why our page beats those 3)
- preview_url: (leave blank; SOP step 6 fills this after AllinCMS DRAFT is saved)
- preview_html_path: (alternative to preview_url; relative path to a rendered HTML snapshot)

Save the result to `wiki/briefs/{{slug}}.md` so `scripts/spawn_reviewer.py` can read it via the slug.

Persona: {{persona slug}}
Primary query: "{{query}}"
Region: {{region}}
```

## Step 4 — Article outline (AI generates, human deep-rewrites)

```
You are a B2B foreign-trade content writer. Given the brief below, produce an article outline:

- title (under 60 chars, contains the primary query naturally)
- meta_title (under 60 chars)
- meta_description (under 155 chars, includes one specific number or example)
- H2 list (5–8 sections, each tied to a buyer objection or sub-query)
- for each H2: 3–5 bullet points of what to cover, naming any wiki source path you'd cite
- 3 credibility add-ons to include (data table, customer screenshot, product video, real comparison) — each must be saved under `raw/` or `media/` with a `source:` line (customer id / order no / ticket no / public URL), and the paths listed in the draft's `credibility_evidence:` frontmatter (required; binary Hard Gate)
- frontmatter fields to set when scaffolding: `published_at` (blank until publish), `updated_at: <today>`, `author: <name>`, `related: []`, `last_seo_check: <today>`

Hard rules:
- No phrases from the residue list (Free shipping, seamless, cutting-edge, …).
- Every claim must be either sourced from {{wiki paths}} or marked `[needs evidence]`.
- One primary audience, one primary search intent.

Brief:
{{paste search-intent brief}}
```

## Step 4 — Competitor article distillation (input to your draft)

```
You are extracting reusable patterns from a competitor article. Read the article at:
{{competitor_url}}

Output:
- core argument in one sentence
- structural skeleton (H2 list)
- 3 hooks they used in the opening
- the strongest claim and what evidence they cite for it
- 3 weak claims (no evidence, vague, AI-filler)
- what they DON'T address (gap our article can own)
- 1 image or chart type that earns the page (describe so we can make our own better version)

Do not summarize the article narratively. Output only the 7 items above.
```

## Step 5 — Image alt text + caption

```
Generate alt text and a caption for this image used in an article about "{{primary_query}}".

Image content: {{describe or paste OCR}}
Article persona: {{persona}}
Region: {{region}}

Output:
- alt: under 125 chars, describes the image AND the article's claim it supports
- caption: under 30 words, gives the reader takeaway + invites scrolling
- filename: kebab-case, includes primary query keyword, under 60 chars

Avoid generic words: "image", "photo", "diagram of".
```

## Step 7 — Reviewer spawn (DO NOT use this for the reviewer itself)

For spawning the adversarial reviewer subagent, the prompt is `references/codex-adversarial-reviewer.md` — paste that file verbatim. Do not write your own reviewer prompt; the isolation contract depends on the wording.

## Step 11 — Lesson proposal (from a run debrief)

```
You just finished a content ops run. List every moment where:
- the user corrected your approach
- you encountered a scenario the SOP didn't cover cleanly
- an audit failed for a reason the script didn't catch
- a competitor used an angle we don't have a pattern for

For each: write a YAML entry per the schema in `wiki/lessons.md`:
- date: today
- trigger: user_correction | new_scenario | failed_audit | competitor_pattern
- rule: one-sentence imperative
- why: the incident
- scope: skill | project
- proposed_destination: file:section that should absorb this
- status: proposed

Append to `wiki/lessons.md`. Do NOT edit any other file.
```
