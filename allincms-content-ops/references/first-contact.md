# First-Contact Protocol

When a new user invokes this skill via the README "Use with AI" prompt, the AI runs THIS protocol **before** offering any suggestions. The point: don't hand a stranger 5 generic scenarios — establish the user's company context first, then tailor.

## When to run

Run on first contact — i.e. the user's opening message points you to this repo and asks to be onboarded. Do NOT re-run on subsequent turns; once a goal is established, follow Workflow + Mode Selection per SKILL.md.

Cheap detection: if the user's first message contains the repo URL **and** `wiki/lessons.md` has not been modified beyond the seeded entries, treat as first contact.

## Skip clause

If the user's opening message already names a concrete task with enough specifics to act (e.g. "audit my slug=foo page", "fetch this URL into raw/", "list status"), SKIP all four phases below and route straight per SKILL.md → Mode Selection. Do not force the user through onboarding when they already know what they want.

## Language detection

Detect from the user's opening message:

- Mostly Chinese characters → respond in 中文
- Otherwise → respond in English
- Mixed / ambiguous → ask once: `中文 or English?`

Do NOT default to PROJECT_INDEX `Default content language` — that's site-wide, not the conversation language.

---

## Phase 1: Context probe (silent — at most one short user-facing line)

Before listing anything, open these in order:

| Source | What you're checking | "Filled" heuristic |
|---|---|---|
| `wiki/company.md` | positioning, proof, open questions | > 80 words AND not a verbatim init template stub |
| `wiki/products/*.md` | any product .md beyond a stub | any file > 30 words |
| `wiki/personas/*.md` | any persona | any file > 30 words |
| `PROJECT_INDEX.md` → `Current Site` → `Front-end domain` | a fetchable URL we can probe | non-empty, non-placeholder |

Classify the project into one of three states:

- **A. Known** — `wiki/company.md` is filled (and ideally products/personas too)
- **B. Probable** — `Front-end domain` is set but wiki content is stub
- **C. Cold** — both empty

The single user-facing line for Phase 1 is at most: "先看一眼你项目背景，建议才贴你 / Quick read on your project so suggestions land where you are."

## Phase 2: Establish context (one path)

### Path A — Known

Paraphrase what's in `wiki/company.md` back in ONE sentence: "看到你写了：你是 [行业] 卖给 [ICP] 的 [产品类]，主张是 [一句话]。对吗？/ Reading your wiki: [paraphrase]. Right?"

If user confirms → go to Phase 3.
If user corrects → record the correction as a **proposed** entry in `wiki/lessons.md` (`trigger: user_correction`, `scope: project`) and update the paraphrase. Do NOT silently rewrite `wiki/company.md` — that needs human curation per the wiki contract.

### Path B — Probable (have domain, no positioning yet)

Offer two paths, user picks one:

> `company.md` 还没填。两个办法二选一：
> 1. 我去 fetch `[Front-end domain]` 主页，自动提炼一段定位，你看完确认。
> 2. 你直接 3 行告诉我：① 卖什么 ② 给谁 ③ 一句话优势。
> 哪个？

If 1 chosen and env supports web fetch:
- Fetch the homepage HTML
- Extract `<title>`, `<meta name="description">`, hero `<h1>`, first paragraph
- Propose draft `wiki/company.md` content (≤ 8 lines, marked `trust: ai-drafted, needs_human_review: true`)
- Show the draft to user, ask confirmation
- On confirmation, write `wiki/company.md`

If 1 chosen but env has no web fetch (claude.ai web, sandboxed Codex run): say so honestly, fall through to option 2.

If 2 chosen → ask the 3 questions one message at a time (don't dump a form). After all three, propose `wiki/company.md` content with the same `needs_human_review: true` flag.

### Path C — Cold

Skip the choice — just ask the 3 questions directly. Same write-with-confirmation flow as Path B-2.

## Phase 3: Tailored scenarios

Now — and only now — list 3–5 concrete starter scenarios. Each scenario MUST reference what the user just told you (or what `company.md` says). Don't echo generic templates.

Examples for a hypothetical 外贸 SaaS:

- **起草并发布一篇 SEO 文章** — 比如：为「外贸团队负责人」写一篇「冷启动 domain warmup」的 SEO 文章
- **监控 3 家直接竞品** — 你说 1-3 个对手网址，我每周抓他们 sitemap，推送值得借鉴的新文
- **审一篇你已有的 landing** — 给我 slug 或 URL，我跑 audit + 给 reviewer brief
- **从 raw 素材蒸馏 wiki** — 你有 PDF / 截图 / 通话纪要丢进 `raw/`，我帮你提炼成可复用的 `wiki/products/` 或 `wiki/personas/`
- **先看现状再决定** — 跑一次 `audit_content.py --status .`，你看完再说

If you have fewer than 3 honestly-tailored scenarios, list only what you have. Don't pad with generics.

## Phase 4: Meta question

> 上面哪个最接近你想做的？或者用一句话告诉我你想交付什么。

After user picks:

| User's pick | Next move |
|---|---|
| `init a fresh project` | Walk through 5 `Current Site` fields one at a time. Then run `init_content_ops_project.py`. |
| `draft & ship` | Check `Current Site` is complete; if not, route through init first. Then ask: persona slug + primary query (or "infer from competitor URL?"). Scaffold via `scripts/new_draft.py`. Enter Workflow at step 3. |
| `monitor competitors` | Ask for 1–3 competitor domains. Run `sitemap_discover.py` on each, show candidates, user confirms entries into `monitoring/competitors.yml`. Then `monitor_run.py --dry-run`. |
| `audit existing page` | Ask for slug or live URL. Local → `audit_content.py --light`. Live → `site_health_check.py`. Report, ask which fix first. |
| `distill from raw` | Ask what's in `raw/` already, or what they'd drop. Walk through `ingest_sources.py`. Then suggest a `wiki/` page structure. |
| `explore first` | Show `audit_content.py --status .` output, **warn** that seeded `lessons.md` + `backlog.md` + example audit are scaffold samples, not real issues. Then offer to walk through one of the other paths. |

## Don'ts

- Don't list generic scenarios before establishing context — that's the bug this protocol exists to prevent.
- Don't ask all 5 `Current Site` fields before knowing the user wants to init or draft.
- Don't dump `SKILL.md` verbatim or list all 9 Workflow steps in the intro.
- Don't silently write `wiki/company.md` — always propose, get confirmation.
- Don't reply in English to a Chinese-speaking user (or vice versa).
- Don't claim the seeded `lessons.md` / `backlog.md` / sample audit are problems with the user's project.
- Don't skip the **Skip clause** at the top — if user pasted a concrete task, just do the task.

## Exemption from `Current Site` STOP

SKILL.md → Required Context says "STOP if any `Current Site` field is empty before any other action." That applies to **work actions** (drafting, publishing, monitoring captures, audits that write). First-contact phases 1–4 are read-only (or write only to `wiki/company.md` with user confirmation, which is part of establishing the project) — exempt. Fill `Current Site` once the user's chosen path requires production writes.

## `wiki/company.md` write contract for first-contact

When Phase 2 produces a confirmed company description, write to `wiki/company.md` with:

```yaml
---
trust: ai-drafted
needs_human_review: true
drafted_at: <YYYY-MM-DD>
drafted_by: first-contact-protocol
---

## Positioning

<one-line positioning, in user's words where possible>

## What we sell

<from user>

## Who buys

<from user>

## One-line edge

<from user>

## Open questions

- (left for human follow-up)
```

The `trust: ai-drafted, needs_human_review: true` frontmatter is a flag for `library_health.py` and the next agent: this content was bootstrapped, deserves a human pass when there's time. Subsequent edits to `wiki/company.md` should follow normal wiki curation (human-driven, AI assists), not be silently rewritten by another first-contact run.
