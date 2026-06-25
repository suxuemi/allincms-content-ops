[English](docs/en/QUICKSTART.md) | 中文

# 快速上手

第一次发一篇 AllinCMS 文章 / 页面，按这条线走，不丢源、不丢 SEO、不丢图、不丢审核。

## 0. 先分类：light-mode 还是 full-mode？

- **light-mode**：改 typo、补 alt 文本、换残留词、修单个字段。只读目标文件 + `wiki/glossary.md`，跑 `audit_content.py --light <file>`，过了就提交，不写 lessons，不动其他索引。
- **full-mode**：新增 / 发布 / 重构 / 改分类区域 / 改封面或搜索意图。下面 1-11 步全部走。

拿不准 → 默认 light，问一句再扩大。**严禁**自己把 light 升级成 full。

## 1. 看索引

读 [PROJECT_INDEX.md](PROJECT_INDEX.md)。**`Current Site` 任一字段为空 → 立刻停下，找用户要值**，不要拿占位符往下跑。

## 2. 入库素材

```bash
python3 allincms-content-ops/scripts/ingest_sources.py . path/to/file.pdf --rights "owned"
python3 allincms-content-ops/scripts/ingest_sources.py . https://example.com/source --rights "public web source"
```

检查 [raw/index.md](raw/index.md)。**`raw/` 是只追加的**——已入库的文件永远不动，源更新就建新的 dated capture。

## 3. 蒸馏到 wiki

把素材拆成稳定页：

- 公司：[wiki/company.md](wiki/company.md)
- 产品：`wiki/products/`
- 人物：`wiki/personas/`
- 方法：`wiki/methodology/`
- 区域：`wiki/regions/`
- 术语：[wiki/glossary.md](wiki/glossary.md)

每页 frontmatter 加 `consumed_by: []`（哪些 web 草稿引用了我）；wiki 事实更新时按 `consumed_by` 找受影响的 web 页重审。

只在聊天里出现的说法不能发布，先落进 `raw/` 或 `wiki/`。

## 4. 定搜索意图

写之前先答：

- 目标客户是谁？
- 他们搜什么？
- 触发搜索的痛点 / 任务是什么？
- 区域 / 语言规则？
- `raw/` 或 `wiki/` 哪些证据支持？
- 读者下一步该做什么？

用 [search-intent.md](allincms-content-ops/references/search-intent.md) 模板。

## 5. 起 web 草稿

放在：

- 文章：`web/drafts/`
- 页面：`web/pages/`
- 帖子：`web/posts/`
- 产品：`web/products/`

**Frontmatter 必填**：title / slug / route / category / tags / meta_title / meta_description / cover_image / cover_alt / source_wiki / source_raw / **differentiation**（这页比借鉴的最强竞品强在哪——空着会被 audit 卡）。

## 6. 处理图

优先用源图。不够再裁 / 标注 / 生成。

PicGo 批传：

```bash
python3 allincms-content-ops/scripts/picgo_batch_upload.py media/processed --out media/uploaded/picgo-manifest.json
```

更新 [media/index.md](media/index.md)。

## 7. 跑竞品监控（可选）

```bash
python3 allincms-content-ops/scripts/monitor_competitors.py .
```

新选题进 [raw/competitors/index.md](raw/competitors/index.md) 和 `wiki/content-opportunities.md`。**用户没点头不许写不许发**。

## 8. 填 AllinCMS（先 DRAFT）

登录 workspace，填：title / slug / route / summary / body / category / tags / cover / SEO 标题 / SEO 描述。**保存为 draft，不要直接发布**。清掉旧分类 / 标签 / 封面残留。

## 9. 对抗审查（隔离审稿人）

```bash
python3 allincms-content-ops/scripts/audit_content.py .
```

然后**派一个全新的 subagent**（Claude: `Agent` 工具 `subagent_type=general-purpose`；Codex: 新会话）当审稿人，prompt 用 [codex-adversarial-reviewer.md](allincms-content-ops/references/codex-adversarial-reviewer.md)。

**审稿人只看**：搜索意图 brief + 渲染后 URL/HTML + 3 个竞品 URL。
**审稿人不看**：草稿 markdown、wiki 源、作者自评、历史 audit。

审稿人必须提 ≥ 5 条反对意见，作者每条标 accepted / rejected / deferred。

通过条件（4 条全要）：总分 ≥ 8.5 **且** 每个维度 ≥ 70% **且** 残留词 0 命中 **且** ≥ 5 条 objections 全部有回应。

把结果写进 `audits/<slug>-<date>.md`（schema 见 [audits.md](allincms-content-ops/references/audits.md)）。

## 10. 发布（被 audit 文件卡住）

发布前最后一道闸：

```bash
python3 allincms-content-ops/scripts/audit_content.py --require-audit-file <slug> .
```

通过才能在 AllinCMS 把 status 翻 published。更新 [web/published/index.md](web/published/index.md) / categories / tags / [web/index.md](web/index.md)。

## 11. 回填 lessons（full-mode 必做）

把这轮发生的**用户纠正 / 新场景 / 审计失败模式 / 竞品新角度**，每条作为 `proposed` 条目追加到 [wiki/lessons.md](wiki/lessons.md)，按 [Lessons File Contract](allincms-content-ops/references/llm-knowledge-base.md) 字段格式。

**禁止直接改 SKILL.md 或 `references/*` 来记录 lesson**——必须走 proposed → 用户审批 → 下次 agent merge 这条路径。

每轮收尾给 3-7 个下一步选题候选 + 选题理由。
