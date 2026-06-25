# First-Contact Protocol

When a new user invokes this skill via the README "Use with AI" prompt, the AI runs THIS protocol **before** accepting any task. The point: don't dump 9 workflow steps on someone who just wants to know what this is for.

## When to run

Run on first contact — i.e. the user's opening message points you to this repo and asks to be onboarded. Do NOT re-run on subsequent turns; once a goal is established, follow Workflow + Mode Selection per SKILL.md as usual.

Cheap detection: if the user's first message contains the repo URL **and** `wiki/lessons.md` has not been modified by this user (only the seeded entries exist), treat as first contact.

## Language

Detect the user's language from their opening message:

- Mostly Chinese characters → respond in 中文
- Otherwise → respond in English
- If ambiguous (3 words total, mixed) → ask once: `中文 or English?`

Do NOT default to PROJECT_INDEX `Default content language` here — that's a site-wide setting, not the conversation language. A Chinese-speaking operator may run an English-language site, and vice versa.

## Introduction script (≤ 15 lines of output)

In the detected language, output three blocks. Keep each tight.

### 1. One-sentence problem framing

NOT feature-language ("This skill provides 15 scripts and 9 workflow steps…").
**Problem-language** ("This turns your scattered notes / competitor pages / half-drafts into audited articles you can ship to AllinCMS, without losing what worked between sessions.")

### 2. Three to five concrete starter scenarios

Anchor each to a real verb the user might want. Examples (pick what fits):

- **draft & ship one article** — "I have a topic and rough material; help me draft, audit, and publish it"
- **monitor competitors** — "Watch N competitor sites; weekly summary of what's new and what to borrow"
- **audit an existing page** — "Here's a slug / URL; tell me what to fix before I republish"
- **init a fresh project** — "I'm setting up a new AllinCMS site from zero"
- **explore first** — "I want to understand what this can do before committing to anything"

Each is one line. Don't explain how — just name the outcome.

### 3. One meta-question

Pick the closest scenario above, or describe what you want to ship in one sentence. Do NOT ask the 5 `Current Site` fields here — that's only needed once the user picks "init" or "draft & ship". Asking up-front feels like a form.

## After user picks a path

| User's pick | Next move |
|---|---|
| `init a fresh project` | Walk through the 5 `Current Site` fields one at a time (site id → front-end domain → workspace URL → browser profile → default content language). Then run `init_content_ops_project.py` with their answers. Resume per SKILL.md from Workflow step 0. |
| `draft & ship one article` | First check `PROJECT_INDEX.md` → `Current Site` — if any field is empty, route through the init flow above. Then ask: persona + primary query + region (or "shall I infer from a competitor URL?"). Scaffold via `scripts/new_draft.py`. Enter SKILL.md Workflow at step 3. |
| `monitor competitors` | Ask for 1-3 competitor domains. Run `sitemap_discover.py` on each, show candidates, ask user to confirm. Add confirmed entries to `monitoring/competitors.yml`. Then run `monitor_run.py --dry-run` to preview. |
| `audit an existing page` | Ask for slug or live URL. Run `audit_content.py --light <file>` if local, otherwise `site_health_check.py` for the live URL. Report findings, ask which to fix first. |
| `explore first` | Show `audit_content.py --status .` output (warn that the seeded `lessons.md` proposed entries + 1 example audit are scaffold samples, not real issues). Then offer to walk through one of the other 4 scenarios. |

## Hand-off into SKILL.md

Once the user's first concrete task is identified, drop the introduction tone and follow SKILL.md → Mode Selection. Subsequent turns use Workflow + Hard Gates normally. The capture protocol at Workflow step 9 still applies.

## Don'ts

- Don't dump SKILL.md verbatim or list all 9 Workflow steps in the intro.
- Don't ask for all 5 Current Site fields before knowing the user wants to init.
- Don't reply in English to a Chinese-speaking user (or vice versa). Re-detect each turn if unsure.
- Don't skip this protocol because "the user obviously knows what they want" — they pasted the README prompt; assume they don't.
- Don't claim the seeded `lessons.md` / `backlog.md` / sample audit file are problems with their project. They are scaffold.

## Exemption from `Current Site` STOP

SKILL.md → Required Context says "STOP if any `Current Site` field is empty before any other action." This applies to **work** actions (drafting, publishing, monitoring captures). The first-contact introduction itself is read-only and exempt: you may read SKILL.md / references / run `--status` without filling Current Site. Fill it only when the user's chosen path requires writes.
