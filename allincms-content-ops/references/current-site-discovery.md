# Opportunistic Current Site Discovery

When the user asks for an action that needs `Current Site` (open backend / publish / capture monitoring / `site_health_check.py`) AND any of `[site_id, front_end_domain, workspace_url, browser_profile]` is empty in `PROJECT_INDEX.md`, **don't ask the user for values first**. Most of those values can be discovered by opening the workspace.

Origin: codex round `audits/codex-rounds/v0.7.0-r1.md` — user reported that being asked for `workspace_url` (a constant) and `browser_profile` (auto-detectable) before the AI would even open the dashboard felt like the AI pushing its own work onto the newbie.

## Preconditions (read before triggering)

Discovery isn't an always-on entry — it's a sub-protocol called from specific contexts. Behavior:

| Caller context | Discovery entry point |
|---|---|
| `first-contact.md` Phase 2 in progress | Steps 4–5 only (login / site listing inlined into Phase 2). Don't open workspace again — Phase 2 may already have. |
| Phase 2 finished, `PROJECT_INDEX` has at least `site_id` filled | Resume from the **first unfilled field**, not Step 1. Skip the workspace re-open. |
| All `Current Site` fields empty AND no Phase 2 active | Run full Steps 1 → 5. |
| `deployment: self-hosted` in `PROJECT_INDEX` | Skip Step 1's SaaS-URL constant; ask for workspace URL once at Step 1. |
| Env has no browser automation capability | Discovery cannot run. Fall back to v0.6 "ask the 4 values" path with one-line explanation: `我这台没有浏览器能力，只能请你手填 site_id / 前台域名`. |

## Step 1 — Constants (write + inline-report)

`workspace_url` is always `https://workspace.laicms.com/` for SaaS users (the default). `browser_profile` defaults to system's default profile.

Write both to `PROJECT_INDEX.md` **and inline-report in the same turn**:

> 我先把 `workspace_url` 默认填 `https://workspace.laicms.com/`（AllinCMS SaaS 标配），`browser_profile` 用系统默认。self-hosted 或要用别的浏览器 profile 请现在打断我。

This satisfies the v0.6 § Don't narrate § 必须报告 whitelist for "writing or modifying a file" — silent file edits are still banned; inline reports are fine.

If user pre-declared `deployment: self-hosted` in `PROJECT_INDEX`, skip this step's URL default and ask once: `你的 workspace URL 是？（self-hosted 部署）`. Write the answer + continue.

## Step 2 — Browser profile auto-detect

If env supports browser automation, use system's default profile. Don't ask. Only surface a question if Step 3 detects a login wall AND the user explicitly mentions "wrong account" — then offer to switch profiles.

## Step 3 — Open workspace_url

### Browser selection per host (added v0.8.0)

The AI must pick a browser tool. Per codex round v0.8.0-r1 Fproc.2, host detection by environment-variable guess is fragile — switch to **explicit confirm before launching**:

```
我打算用 <browser>，依据是 <signal>。
30 秒内回车确认，或输入 'manual' 让我给你 URL 自己开。
```

Then wait for the user's reply.

| Host | Primary browser | Fallback if primary fails |
|---|---|---|
| Codex CLI | Codex built-in preview tool | shell + system Chrome |
| Claude Code | Chrome MCP / Claude in Chrome / Control Chrome MCP | shell + Playwright |
| Cursor | shell + system Chrome (no built-in browser) | manual — give user the URL |
| Cline / Aider | usually no browser tool | manual |
| claude.ai web | **discovery cannot run** — env has no browser at all; fall back to v0.7 ask-4-values path |
| Unknown host | **manual: give the user the URL, ask them to open it, then paste back the rendered HTML or the page title + a sample of links so AI can parse with Step 4 logic** |

Cookie note: Codex's built-in browser session may not share login cookies with the user's system Chrome. If Step 3 hits a login wall using the built-in browser, the AI should offer one switch: `我这边的内置浏览器没登录态，要不你在系统 Chrome 登一下，然后告诉我 site_id / 前台域名？`. Don't loop — go to manual fallback.

### Detect outcome

Open the URL in the selected browser tool. Detect outcome with **≥ 2 independent signals** (URL pattern + DOM selector + page title — any two):

| Outcome | Signals (any 2 → confirmed) |
|---|---|
| Login wall | URL contains `/login` OR `/auth/`; page title matches `登录 / Sign in`; presence of password input field |
| Dashboard | URL matches `workspace.laicms.com/?` (root or with hash); presence of `[data-testid="site-card"]` OR similar list container; title matches `Dashboard / 工作台` |
| Other (CDN challenge / 5xx / wrong URL) | none of above match within 5 seconds → treat as failure |

### If login wall — Wait + Resume contract

Tell the user ONE line:

> 我开了 workspace.laicms.com，登录完告诉我（"好了 / done / 登好了" 都行）。

Then **wait silently** for the user's next message. Do not poll.

**Resume contract**: when the next user message contains any login-confirmation token (`好了` / `done` / `login done` / `登好了` / `已登录` / `OK` after this prompt), **run Step 4 first**, regardless of what else the message contains. If the message also mentions another task ("登好了，顺便那篇能发吗？"), complete Step 4–5 first, then answer the second part. Discovery interruption is forbidden.

If 2 consecutive Step 3 attempts hit "other" outcome (CDN / 5xx / unparseable), fall back to v0.6 ask-4-values path with explanation: `我开了 workspace 但看不到登录页或 dashboard（页面状态异常）；只能请你手填 site_id / 前台域名。`

### If dashboard — continue Step 4

## Step 4 — List sites

Scrape site cards from the dashboard. The expected DOM structure is documented in `audits/discovery-fixtures/dashboard-snapshot.md`. Use the same ≥ 2 signals rule (selector + URL pattern + visible text) for each card extracted.

Outcomes:

- **0 sites** → tell user: `你这账号下还没有站点。先在 workspace 里新建一个，回来告诉我。` Wait. On next user signal, restart Step 4.
- **1 site** → confirm before navigating: `看到你只有 1 个站点 \`<name>\` (id=\`<sid>\`)，开这个？`. Wait for confirm.
- **N sites** → list as bullets: `你有 N 个站点：1. <name1> (id=<sid1>) 2. <name2>...  哪个？`. Wait for pick.

## Step 5 — Navigate + auto-fill

When user confirms / picks:

1. Navigate to the selected site (URL pattern: `workspace.laicms.com/<site_id>/posts` or similar).
2. **Grab `site_id`** from the URL (matches `workspace.laicms.com/([a-z0-9-]+)/`).
3. **Grab `front_end_domain`** from the site's Domains panel or dashboard card. ≥ 2 signals: DOM selector + visible URL string + (optionally) Domains panel link.
4. Write both into `PROJECT_INDEX.md` Current Site section.
5. Inline-report (per v0.6 §必须报告): `已补：site_id=<sid> / front_end_domain=<domain>。PROJECT_INDEX 写好了。`
6. **Now resume the original user request** (e.g. continue to "open backend" — the site is already loaded).

If front_end_domain can't be found via signals → write `site_id` only, log a backlog row: `front_end_domain 待补：用户访问 Domains 设置后告诉我`. Don't block the original action.

## Failure budget

`discovery_failure_count` is a per-session counter. Increment on:

- Step 3 "other" outcome
- Step 4 zero-signal site list scraping
- Step 5 site_id pattern miss

When count reaches 2: fall back to v0.6 ask-4-values path with a one-line apology + explanation.

## Regression fixture

`audits/discovery-fixtures/dashboard-snapshot.md` captures the workspace.laicms.com structure that this protocol relies on. When workspace ships a redesign, that file is updated in the same PR as the discovery DOM selectors.

## What discovery does NOT do

- Discovery does **not** unlock `audit_content.py` blocking gates. Publish still requires `Current Site` to be fully written; discovery just removes the friction of asking the user upfront. Once discovery completes, all subsequent publishes find the fields populated.
- Discovery does **not** apply to the reviewer subagent in `codex-adversarial-reviewer.md`. That reviewer remains contract-isolated.
- Discovery does **not** modify `wiki/`, `web/`, or any user-edited content — only the `Current Site` block of `PROJECT_INDEX.md`.
