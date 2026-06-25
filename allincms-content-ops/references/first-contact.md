# First-Contact Protocol

When a new user invokes this skill via the README "Use with AI" prompt, the AI runs THIS protocol **before** offering any suggestions. The point: don't hand a stranger 5 generic scenarios — establish the user's company context first, then tailor.

## When to run

Run on first contact — i.e. the user's opening message points you to this repo and asks to be onboarded. Do NOT re-run on subsequent turns; once a goal is established, follow Workflow + Mode Selection per SKILL.md.

Cheap detection: if the user's first message contains the repo URL **and** `wiki/lessons.md` has not been modified beyond the seeded entries, treat as first contact.

## Skip clause

If the user's opening message already names a concrete task with enough specifics to act (e.g. "audit my slug=foo page", "fetch this URL into raw/", "list status"), SKIP all four phases below and route straight per SKILL.md → Mode Selection. Do not force the user through onboarding when they already know what they want.

**Skip × Required Context interaction**:

- Skipping into **light-mode** (typo / single-field edit / `audit_content.py --light` / `--status` / reading) does **NOT** trigger the `Current Site` STOP. SKILL.md → Required Context explicitly exempts these.
- Skipping into a **full-mode** path that touches AllinCMS, publishes, captures monitoring, or runs `site_health_check.py` DOES trigger the STOP — STOP first, route the user through `init_content_ops_project.py`.
- If the skip target is full-mode Workflow steps 3–8 AND `wiki/company.md` is in `unfilled` / `ai-drafted-unreviewed` state (see Phase 1 detection), warn the user once before proceeding:
  > 我能直接开干，但 wiki/company.md 还没建过，跑到 step 7 audit 一定会被 `differentiation` / `credibility_evidence` 卡 Hard Gate。先花 5 分钟跑 Path B/C 建上下文，还是硬上看 audit 把哪些点打回来？
  Then wait for the user's choice before continuing.

## Language detection

Detect from the user's opening message:

- Mostly Chinese characters → respond in 中文
- Otherwise → respond in English
- Mixed / ambiguous → ask once: `中文 or English?`

Do NOT default to PROJECT_INDEX `Default content language` — that's site-wide, not the conversation language.

---

## Phase -1: Skill sync (BEFORE reading SKILL.md or anything else, ONCE per session)

If the installed skill is git-backed, check for upstream updates first — running on stale rules wastes everyone's time. This phase runs **once per session, before Phase 1, before SKILL.md is read in earnest**.

1. **Detect installation type**:
   - `.git/` present in the skill root and the remote URL contains `suxuemi/allincms-content-ops` (or a known fork) → continue to step 2.
   - `.git/` absent (user installed via downloaded zip) → tell the user once: `这套 skill 是 zip 装的，没法增量更新。要最新版去 https://github.com/suxuemi/allincms-content-ops 重新下 zip，覆盖 allincms-content-ops/ + 根目录文档（不要动 wiki/ web/ raw/ audits/ monitoring/ media/ PROJECT_INDEX.md）。` Then **skip Phase -1** and continue to Phase 1.
   - Env has no shell capability (claude.ai web etc.) → say so honestly, skip Phase -1, continue to Phase 1.

2. **Dry-run check**: `python3 allincms-content-ops/scripts/update_skill.py --dry-run`. If output reads `skill is up to date` → skip to Phase 1.

3. **If N commits behind**, surface to the user in the detected language:
   > skill 有 N 个新提交可用。**更新（推荐）/ 看变更 / 跳过用现在的版本**？

   **Wait for the user's explicit pick** — do NOT auto-update. Treating silence as consent is a violation.

4. **On "更新"** → `python3 allincms-content-ops/scripts/update_skill.py` (no `--dry-run`).
   - If output contains a `CHANGED-CONTRACT-FILES:` section, list those files to the user, then say:
     > 我刚拉了新版规则，给我 30 秒重读 SKILL.md / references 再继续。
   - Then **actually Re-Read each listed file** — your cached content is stale and using it will cause contract drift.

5. **On "看变更"** → run `git log --oneline HEAD..<remote>/<branch> | head -10`, paste it back, then ask the choice again.

6. **On "跳过"** → log a backlog row: `python3 allincms-content-ops/scripts/note.py "running on skill behind by N commits since <date>" --kind todo --priority low`. Continue to Phase 1.

7. **Mid-session ban**: do NOT run `update_skill.py` later in the same session unless the user explicitly invokes the manual sync prompt. Pulling new contract files mid-run swaps SKILL.md / references/* under your feet and any in-flight workflow breaks. Phase -1 is the only legitimate sync point.

## Phase 1: Context probe (silent — at most one short user-facing line)

Before listing anything, open these in order and classify:

| Source | "Filled" detection (precise) |
|---|---|
| `wiki/company.md` | **Sentinel `<!-- first-contact: unfilled -->` is absent** AND Positioning section non-empty character count ≥ 60. The init template ships the sentinel; first-contact removes it when committing a confirmed bootstrap. Any human/AI edit to the file should remove the sentinel. |
| `wiki/products/*.md`, `wiki/personas/*.md` | Any file > 30 non-whitespace characters in the body section (excluding frontmatter and section headers). |
| `PROJECT_INDEX.md` → `Current Site` → `Front-end domain` | Non-empty AND not one of these placeholders: `TODO`, `example.com`, `<your-domain>`, `your-site.com`, `<domain>`. |

Classify the project into one of these states:

- **A. Known** — `wiki/company.md` filled (sentinel gone + ≥ 60 chars in Positioning) AND frontmatter does **not** carry `needs_human_review: true`. Ideally products/personas also filled, but not required.
- **A′. AI-bootstrap pending review** — `wiki/company.md` filled, but frontmatter carries `trust: ai-drafted` and `needs_human_review: true`. A previous first-contact wrote this; nobody confirmed yet.
- **B. Probable** — `Front-end domain` is set (non-placeholder), wiki content is stub (sentinel present).
- **C. Cold** — both empty / placeholder.

The single user-facing line for Phase 1 is at most: `先看一眼你项目背景，建议才贴你 / Quick read on your project so suggestions land where you are.` Do NOT dump the classification result to the user — keep it internal.

## Phase 2: Establish context (one path)

### Path A — Known

Paraphrase what's in `wiki/company.md` back in ONE sentence: "看到你写了：你是 [行业] 卖给 [ICP] 的 [产品类]，主张是 [一句话]。对吗？/ Reading your wiki: [paraphrase]. Right?"

If user confirms → go to Phase 3.
If user corrects → do NOT silently rewrite `wiki/company.md` (that's human-curated per the wiki contract). Instead, propose a one-line patch and ask the user to make the edit (or to grant a one-shot write). Only after explicit approval, write the patch. If the correction reveals a missing rule rather than a fact, `scripts/note.py --kind correction "..." --why "..."` instead.

### Path A′ — AI-bootstrap pending review (don't paraphrase your own draft as ground truth)

If Phase 1 classified the project as A′, the existing `wiki/company.md` was written by a prior first-contact run and never confirmed. **Do NOT paraphrase it back to the user as if it were ground truth** — paraphrasing AI content back to the user is a feedback-loop hallucination.

Instead, surface it honestly:

> 上次我替你起草了一段 `wiki/company.md` 但没人复核过。两条路：
> ① 你 30 秒读一遍我把 `needs_human_review` 关掉，进 Phase 3。
> ② 推翻重来，走 Path B 或 C 重新建。

Show the existing content verbatim (don't paraphrase). Wait for the user to pick. On choice ①, remove the `needs_human_review: true` field after the user confirms; flip `trust:` from `ai-drafted` to `human-verified`. On choice ②, archive the old content (move to `wiki/_archive/company-<date>.md`) then restart Path B or C.

### Path B — Probable (have domain, no positioning yet)

Offer two paths and **explicitly ask permission** before any network action:

> `company.md` 还没填。两个办法二选一：
> 1. 我可以**现在去 fetch 一次** `[Front-end domain]`（一个 GET，只读 HTML head + 首屏），用提炼草一段定位你看。
> 2. 你直接 3 行告诉我：① 卖什么 ② 给谁 ③ 一句话优势。
> 哪个？（如果是 1，我等你回 "可以 / 去" 才发请求。）

**Fetch contract for option 1**:

- Wait for explicit consent (`可以 / 1 / 去 / yes`). Treating silence as consent is NOT acceptable — staging/internal domains may trigger WAF alerts or violate corporate policy.
- If env has no web-fetch tool (claude.ai web, sandboxed runs) → say so honestly and fall through to option 2.
- If consent given, fetch ONCE. Extract: `<title>`, `<meta name="description">`, top `<h1>`, first non-nav paragraph.
- **Minimum signal gate**: if the extracted text totals fewer than 30 meaningful words (SPA shell, blank meta, Cloudflare challenge body containing `Just a moment` / `cf-mitigated` / `Checking your browser`), do NOT draft from it. Say so honestly:
  > 首页 fetch 回来主要是 JS 壳 / Cloudflare challenge，没拿到足够定位信号。切换到方式 2，你 3 行告诉我。
  Then go to option 2.
- If signal is sufficient, draft `wiki/company.md` content (≤ 8 lines) with the frontmatter from `references/corpus-layout.md` § AI-drafted wiki pages. Show the draft verbatim, wait for user's `OK / 改 / 重来`.
- Only on `OK` write the file. On `改 X`, revise once and re-show. On `重来`, drop the fetch attempt and go to option 2.

If 2 chosen → ask the 3 questions **one message at a time** (don't dump a form). After all three answers, draft `wiki/company.md` content with the same frontmatter. Show verbatim, wait for OK before writing.

### Path C — Cold

Skip the choice — just ask the 3 questions directly. Same write-with-confirmation flow as Path B-2.

## Phase 3: Tailored scenarios

Now — and only now — list 3–5 concrete starter scenarios.

### Token-bind self-check (mandatory, run BEFORE sending Phase 3)

1. Extract from Phase 2 user answers (or paraphrased `company.md`) three token types:
   - **product tokens** — concrete nouns the user used for what they sell (e.g. `SMTP relay`, `cold email tool`, `外贸独立站`)
   - **ICP tokens** — concrete nouns for who they sell to (e.g. `SaaS 开发者`, `外贸团队负责人`, `solo founders`)
   - **edge tokens** — keywords from the one-line advantage (e.g. `99.9% deliverability`, `本地化建站`, `5x cheaper`)
2. Each scenario bullet text MUST contain at least one user token verbatim or as a tight synonym (Chinese ↔ Chinese, English ↔ English; no cross-language translation that the user didn't make).
3. If you cannot satisfy 3 bullets with this constraint, list only what you can. Open the section with: `上下文还不够丰富，我只敢列 N 条；想要更多就再给我一条产品 / 客户细节 / Context is still thin, so I'm only listing N tailored options; one more detail on product or audience will unlock more.`
4. **Banned strings** (from the hypothetical example below; never copy verbatim unless the user actually said them): `外贸团队负责人`, `domain warmup`, `SEO 文章`, `sitemap`, `cold email`, `SaaS founders`.

### Language continuity

Continue in the language detected at Phase 1. Do NOT switch to English mid-conversation just because the examples below are in English. Bullet headings must be in the user's language. The English labels in the examples are illustrative only — translate them when writing for a 中文 user.

### Hypothetical example (for a 外贸 SaaS — illustrate the SHAPE, never copy verbatim)

- **起草并发布一篇 SEO 文章** — 比如：为「[ICP token]」写一篇「[product token + 角度]」的 SEO 文章
- **监控 3 家直接竞品** — 你说 1-3 个对手网址，我每周抓他们 sitemap，推送值得借鉴的新文
- **审一篇你已有的 landing** — 给我 slug 或 URL，我跑 audit + 给 reviewer brief
- **从 raw 素材蒸馏 wiki** — 你有 PDF / 截图 / 通话纪要丢进 `raw/`，我帮你提炼成可复用的 `wiki/products/` 或 `wiki/personas/`
- **先看现状再决定** — 跑一次 `audit_content.py --status .`，你看完再说

If you have fewer than 3 honestly-tailored scenarios, list only what you have. Do not pad with generics.

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

When Phase 2 produces a confirmed company description, write to `wiki/company.md` with the schema documented in `references/corpus-layout.md` § AI-drafted wiki pages. Concretely:

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

**Rules**:

- Remove the `<!-- first-contact: unfilled -->` sentinel from the file when writing — Phase 1 of the next first-contact run uses sentinel-absence to mean "human/AI has touched this".
- `library_health.py` has a `check_ai_drafted_unreviewed` check that surfaces this file in `audits/library-health-<date>.md` and queues a backlog row until a human confirms.
- A confirming human read flips `trust: human-verified` and removes `needs_human_review:`. After that, the file follows normal wiki curation.
- Subsequent edits to `wiki/company.md` should NOT be silently rewritten by another first-contact run — Phase 1 detects `needs_human_review: true` as state A′ and offers the user a confirm-or-restart choice instead of paraphrasing AI content back as ground truth.
