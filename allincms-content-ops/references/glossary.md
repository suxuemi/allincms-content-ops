# Glossary

Bilingual term map. Use the English term as the canonical id in code, frontmatter, and SKILL.md. Use the Chinese rendering for team-facing docs and Chinese website copy. **One concept, one English name, one Chinese name** — never let synonyms drift.

## Core Terms

| English (canonical) | 中文 | One-line meaning |
|---|---|---|
| raw | 原始素材 | immutable original material and extraction outputs. Append-only. 不可变，只追加。 |
| wiki | 蒸馏知识 | compiled, linked knowledge derived from raw. Rewritable. 可重写。 |
| web | 网站产物 | publishable drafts and published indexes. One-shot per slug. |
| lessons | 经验回填 | `wiki/lessons.md` entries (proposed → approved → merged). Single channel for skill iteration. |
| search intent | 搜索意图 | the job behind a query, not just the keyword. |
| GEO | 生成式引擎优化 | generative engine optimization — visibility in AI-generated answers. |
| AEO | 答案引擎优化 | answer-oriented content structure. |
| E-E-A-T | E-E-A-T | experience, expertise, authoritativeness, trustworthiness. 体验 / 专长 / 权威 / 可信。 |
| fan-out query | 扩散查询 | related queries a generative search system may issue to satisfy a broader question. |
| commodity content | 同质化内容 | generic content with no unique insight. |
| AllinCMS residue | 模板残留 | default template or Copilot copy that does not belong to the current site. |
| PicGo | PicGo | local image upload service to a remote host. |
| content opportunity | 选题机会 | monitored or discovered topic that may become a page/post/guide. |
| publish gate | 发布闸 | required audit checks before content can go live. |
| differentiation | 差异化承诺 | required frontmatter field: how this draft beats the strongest competitor URL it borrows from. |
| reviewer isolation | 审稿人隔离 | adversarial review runs in a fresh subagent without access to draft markdown, wiki sources, or author self-assessment. |
| light-mode | 轻模式 | typo / single-field / alt-text edits — skip full ceremony. |
| full-mode | 全模式 | create / publish / restructure — full SOP + Hard Gates. |
| consumed_by | 反向链 | wiki frontmatter field listing web drafts that cite this page. |
| Pass Criteria | 通过条件 | total ≥ 8.5 AND every area ≥ 70% AND zero residue AND ≥ 5 logged objections. |

## Preferred Language (English copy)

Use:

- export website
- product catalog
- inquiry flow
- domain launch
- AllinCMS workspace
- launch checklist
- buyer questions
- setup guide

Avoid unless backed by evidence:

- guaranteed ranking
- best in the world
- enterprise-grade if no proof
- seamless
- cutting-edge
- revolutionary
- 24/7 support unless true
- customer names or countries not sourced

## 偏好用语（中文文案）

用：

- 外贸独立站
- 产品目录
- 询盘链路
- 上线 checklist
- AllinCMS 工作台
- 买家关注点
- 配置指南

避免（除非有证据）：

- 排名保证 / 包上首页
- 全球第一 / 行业领先
- 无脑用「企业级」
- 「无缝」「赋能」「打通」「闭环」
- 「革命性」「颠覆式」
- 7×24 服务（如果做不到）
- 拿不到授权的客户名 / 国别

## Drift Guard

When a new term appears in `wiki/lessons.md` or in real drafts, add a row here before merging the lesson. Two synonyms for the same concept = bug; pick one, deprecate the other with a `(deprecated, use X)` note.
