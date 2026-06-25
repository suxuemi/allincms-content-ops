# SOP

## Mission

Turn scattered source material into useful AllinCMS web content that can rank in search, appear in generative answers, and satisfy real buyers. The operating unit is a content loop:

`raw -> wiki -> search intent -> web draft -> media -> AllinCMS -> audit -> publish -> index -> monitor -> next topic`

## Standard Run

1. **Open the project**
   - Read `PROJECT_INDEX.md`.
   - Confirm `raw/`, `wiki/`, `web/`, and `monitoring/` exist.
   - If missing, run `init_content_ops_project.py`.

2. **Ingest**
   - Store original files under `raw/YYYY-MM-DD/source-name/`.
   - Convert readable content to Markdown beside originals.
   - Add each item to `raw/index.md` with source type, date, owner, rights, extraction status, and downstream wiki links.
   - For repeatable ingestion, run `scripts/ingest_sources.py <project-root> <files-or-urls...> --rights <note>`.

3. **Compile**
   - Update `wiki/company.md`, `wiki/products/*.md`, `wiki/personas/*.md`, `wiki/methodology/*.md`, `wiki/competitors/*.md`, and `wiki/glossary.md`.
   - Link claims to raw source paths.
   - Separate facts, interpretation, and open questions.
   - Keep pages retrieval-friendly: one product, persona, region, competitor, or method per page when possible.

4. **Analyze intent**
   - Define buyer persona, region, funnel stage, query cluster, SERP/GEO angle, objections, and conversion.
   - Reject topics that do not map to customer pain or product value.

5. **Draft**
   - Write in `web/drafts/<category>/<slug>.md`.
   - Use existing wiki facts and monitored gaps.
   - Avoid generic intros. Start with the user's problem or a concrete use case.

6. **Image and media**
   - Pick source images first.
   - Repair/crop/annotate only when it improves comprehension.
   - Upload with PicGo when publishing externally.
   - Record final URLs in the draft and media manifest.

7. **AllinCMS fill (DRAFT only)**
   - Use browser logged-in session.
   - Fill body, summary, SEO fields, category, tags, cover, route, and modules.
   - Clear residue from old categories/tags/covers.
   - Use real article images as covers; avoid repeated covers unless topic cluster requires it.
   - Save with `status=draft`. Do NOT switch to published in this step.

8. **Adversarial audit (isolated reviewer)**
   - Run local audit script: `scripts/audit_content.py <project-root>`.
   - Spawn a fresh subagent as adversarial reviewer per `references/codex-adversarial-reviewer.md`. Reviewer sees ONLY: search-intent brief, rendered preview URL/HTML, top 3 competitor URLs. Reviewer does NOT see the draft markdown or author's self-assessment.
   - Reviewer must surface ≥ 5 objections; author records each as `accepted` (with diff) / `rejected` (with reasoning) / `deferred` (with issue id).
   - Score content, visual, SEO/GEO, mobile, and backend fit. Pass = total ≥ 8.5 AND every area ≥ 70% AND zero blocking-residue.
   - Write the audit file `audits/<slug>-<date>.md` with reviewer subagent id, score breakdown, objections, and responses.

9. **Publish (gated by audit file)**
   - Publish only after `audits/<slug>-<date>.md` exists and passes. Flip AllinCMS `status` to published.
   - Capture URL, timestamp, category, tags, canonical intent, target queries, cover URL, and audit score.
   - Update `web/published/index.md`.

10. **Recommend next work**
   - Add 3-7 next topic ideas with rationale, search intent, target persona, and source gaps.
   - Do not write or publish monitored topics without user confirmation.
   - If competitor monitoring is configured, run `scripts/monitor_competitors.py <project-root>` before proposing the next batch.

11. **Reflect, ask, and route**
   - **Mandatory user prompt** (full-mode only) — ask before declaring run complete: `本轮有想要保留的纠正、想试的新方向、或想加进 TODO 的事吗？`
   - Regardless of answer, scan the session for corrections / validated approaches / suggestions / out-of-scope ideas / open questions per `references/feedback-loop.md`.
   - Route each: durable rule → `wiki/lessons.md` (`status: proposed`); TODO / idea / question → `wiki/backlog.md` (`status: open`).
   - Do NOT edit SKILL.md or `references/*` directly. The next agent's Workflow step 0 will merge approved lessons.
   - Skip this step in light-mode (use light-mode exception in `feedback-loop.md` if user explicitly asks to remember).

## Stop Points

Stop for user input when:

- Login is expired.
- Source rights are unclear.
- Topic affects legal, medical, financial, safety, or compliance claims.
- Competitor monitoring produces a topic that requires strategic approval.
- The only available images are low-quality or misleading.
- The audit score cannot reach 8.5 without changing product positioning or claims.
- Region-specific requirements are unknown.
- The user has not approved a competitor-derived topic.
- A raw file's mtime is newer than its `collected_at` (raw was mutated; halt and create a new dated capture).
- Adversarial reviewer returned < 5 objections or refused to engage (re-run with a different subagent before proceeding).
