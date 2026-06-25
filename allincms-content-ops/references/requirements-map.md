# Requirements Map

This map ties the original user requirements to the skill files that implement them.

| # | Requirement | Where implemented |
|---:|---|---|
| 1 | Combine output with existing material and improve it from sources | `SKILL.md`, `references/sop.md`, `references/corpus-layout.md`, `references/llm-knowledge-base.md` |
| 2 | Cover website work plus SEO, competitor material collection, and PicGo batch uploads | `references/seo-geo.md`, `references/competitor-monitoring.md`, `references/media-picgo.md`, `scripts/monitor_competitors.py`, `scripts/picgo_batch_upload.py` |
| 3 | Complete website content, especially SEO | `references/seo-geo.md`, `references/search-intent.md`, `references/audits.md` |
| 4 | Remove AI smell and audit every item | `references/audits.md`, `references/search-intent.md`, `scripts/audit_content.py` |
| 5 | Analyze regional norms, edit images, upload, and fill content | `references/media-picgo.md`, `references/allincms-backend.md`, `wiki/regions/` skeleton |
| 6 | Keep content length and visual rhythm appropriate | `references/search-intent.md`, `references/audits.md` |
| 7 | Start from target customer and search intent | `references/search-intent.md`, `references/seo-geo.md` |
| 8 | Create `wiki`, `raw`, `web`, entry paths, and indexes | `references/corpus-layout.md`, `scripts/init_content_ops_project.py` |
| 9 | Extract monitored article topics, write and image from intent, and improve paths/categories/tags/descriptions | `references/competitor-monitoring.md`, `scripts/monitor_competitors.py`, `references/search-intent.md`, `references/allincms-backend.md` |
| 10 | Make `web` content fit AllinCMS backend data | `references/allincms-backend.md`, `web` frontmatter in `references/corpus-layout.md` |
| 11 | Extract PDF, PPT, MP4 and other files into Markdown raw, then wiki for company/product/methodology | `references/media-picgo.md`, `scripts/ingest_sources.py`, `references/corpus-layout.md`, `references/llm-knowledge-base.md` |
| 12 | Provide SOPs and sub-skills such as upload, aesthetic audit, and content audit | `references/sop.md`, `references/media-picgo.md`, `references/audits.md`, scripts |
| 13 | Adversarially improve until satisfactory before publishing | `references/audits.md`, `SKILL.md` hard gates |
| 14 | Recommend divergent next topics each round and index published content by category | `SKILL.md`, `references/sop.md`, `references/corpus-layout.md`, `wiki/content-opportunities.md` |
| 15 | Maintain competitor monitoring index and push new topics for user confirmation | `references/competitor-monitoring.md`, `scripts/monitor_competitors.py`, `raw/competitors/index.md`, `monitoring/index.md` |
| 16 | Include glossary | `references/glossary.md`, `wiki/glossary.md` skeleton |
| 17 | Apply Karpathy-style LLM knowledge-base theory | `references/llm-knowledge-base.md` |
| 18 | Make it portable beyond Codex for Claude, WorkBuddy, and generic agents | `AGENTS.md`, `CLAUDE.md`, `WORKBUDDY.md`, `references/corpus-layout.md` |

When updating this skill, keep this table current. If a requirement has no concrete file or script, the skill is incomplete.
