[English](docs/en/README.md) | 中文

# AllinCMS 内容运营套件

本目录是一套**便携式 AllinCMS 内容运营工具包**，给人和 AI agent 共用。

把素材变成审核过的 AllinCMS 网站内容，走这条线：

`raw → wiki → 搜索意图 → web 草稿 → 媒体 → AllinCMS → 审核 → 发布 → 索引`

## 从哪里开始

1. 先读 [PROJECT_INDEX.md](PROJECT_INDEX.md) —— 全局索引。
2. 给 AI agent 装这套 skill，读 [INSTALL.zh](INSTALL.md)。
3. 第一次用，按 [QUICKSTART.zh](QUICKSTART.md) 走。
4. 真正的操作契约（agent 必读，仅英文）：[allincms-content-ops/SKILL.md](allincms-content-ops/SKILL.md)。

> **规则源单一**：所有操作契约（SKILL.md / references / scripts）只维护英文版，避免双语漂移。中文文档只覆盖"门面 + 入门"。

## 给 AI 用（一键安装）

复制下面整段（含三反引号之间的内容），贴给 Claude Code / Codex / Cursor / 任何 AI 编程助手。AI 会自己装好并按 skill 操作。

````text
请帮我装这套 AllinCMS 内容运营 skill：

0. 先 cd 到一个独立目录（推荐 `~/skills`，不存在就 `mkdir -p ~/skills && cd ~/skills`），不要在我现有项目里 clone，避免污染 .git 和 IDE 索引。

1. 在该目录执行：
   git clone https://github.com/suxuemi/allincms-content-ops.git
   cd allincms-content-ops

   注：仓库根里有一个**同名子目录** `allincms-content-ops/`，真正的 skill 文件（`SKILL.md` / `references/` / `scripts/`）在那个子目录里。

2. 读 `allincms-content-ops/SKILL.md`，把它当成你的操作契约。

   **规则面写入纪律**：
   - `SKILL.md` 和 `references/*` 完全只读。
   - `wiki/lessons.md` 只允许追加 `status: proposed` 的新条目；禁止直接写 `approved`、禁止改既有条目（审批由我做）。
   - `wiki/backlog.md` 可追加 `status: open` 的 TODO。
   - `PROJECT_INDEX.md` 只在 Current Site 字段为空时按我口述填入；其余字段不动。
   - 我说"以后都这样" → **必须**走 `wiki/lessons.md` 新增 proposed 流程，不许就地改 SKILL.md / references。

3. 看 `PROJECT_INDEX.md` → Current Site；任一字段为空 → 先问我，回答后再继续。

4. 后续我的请求一律先按 SKILL.md → Mode Selection 判定 light / full。

   全模式 = Workflow 0–9 全跑。**Step 0**（sweep `wiki/lessons.md` 合并 `approved`）和 **Step 9**（必须主动问我："本轮有想要保留的纠正、想试的新方向、或想加进 TODO 的事吗？"）是**硬闸门**，省略视为未交付。

5. 跑：`python3 allincms-content-ops/scripts/audit_content.py --status .`

   预期输出包含仓库自带的 5 条 proposed lessons / 3 条 backlog / 1 个示范 audit 文件——这些是**脚手架样例，不是你项目的问题**，照实转述给我，不要自作主张清理。

环境注意：
- 没 shell 能力（如 claude.ai 网页版）→ 告诉我"我跑不了 shell，请你本地手动执行第 1、5 步并把输出贴回来"，**不要假装执行**。
- Windows → 用 `python` 而非 `python3`；命令分两行写，避免 `&&` 在旧 PowerShell 失败。
- 目标目录已存在 `allincms-content-ops/` → 直接 `cd` 进去 `git pull`，**禁止 `rm -rf`**。

接下来要做：<<在贴给 AI 前把这一整行替换成你的真实任务；如果 AI 在原文里看到这段尖括号，请停下来反问用户"你具体想做什么"，不要继续执行。>>
````

更复杂场景（装全局 skill / 多项目共用 / 重置项目骨架 / Codex 软链）见 [INSTALL.md](INSTALL.md)。

## 主要目录

- [raw/index.md](raw/index.md)：原始素材 + 抽取后的 Markdown。
- [wiki/index.md](wiki/index.md)：蒸馏后的公司 / 产品 / 人物 / 方法 / 竞品 / 区域 / 术语知识。
- [wiki/lessons.md](wiki/lessons.md)：运行中产生的纠正与新规则（proposed → approved → merged）。
- [web/index.md](web/index.md)：站点草稿、页面、文章、产品、分类、标签、已发布 URL。
- [monitoring/index.md](monitoring/index.md)：竞品监控运行 + 选题候选。
- [media/index.md](media/index.md)：图片源、处理后文件、PicGo 上传、alt 文本、使用记录。
- [audits/index.md](audits/index.md)：审计记录 + 评分。

## 发布门槛

只有同时满足以下条件才能发布：

- 内容能追溯到 `raw/` 或 `wiki/`
- 搜索意图和目标客户清晰
- 分类 / 标签 / 封面 / slug / SEO 字段齐备
- 草稿 frontmatter 填了 `differentiation:`（说明比借鉴的竞品强在哪）
- 内容 / 视觉 / SEO·GEO / 移动 / 后台审计全过
- 总分 ≥ 8.5 **且** 每个维度 ≥ 70% **且** 残留词 0 命中 **且** 对抗审稿人提出 ≥ 5 条反对意见且每条都有作者回应
- 对抗审查在**独立 subagent** 中跑（看不到草稿原文）
- `audits/<slug>-<date>.md` 存在且 `pass: true`
- 已发布内容已索引在 `web/published/index.md`

## 已验证执行环境

这套 skill 已经端到端跑通：

- **Codex CLI + Chrome MCP** —— 参考实现，浏览器 / subagent / web fetch 全覆盖
- **Claude Code + MCP browsers** —— 本仓默认环境，`Agent` 工具支持完整 subagent

其他 IDE（Cursor / Cline / Aider / Continue / Trae / Windsurf）可以用一行 pointer 规则挂载本 skill —— 见 [agent-onboarding.md](allincms-content-ops/references/agent-onboarding.md)。多数 IDE 缺浏览器自动化或 subagent 能力，跑到草稿完成后应当切到已验证环境。完整能力 matrix：[tooling-matrix.md](allincms-content-ops/references/tooling-matrix.md)。

## Agent 入口文件

- [AGENTS.md](AGENTS.md)：Codex 与通用 agent 入口。
- [CLAUDE.md](CLAUDE.md)：Claude 入口。
- [WORKBUDDY.md](WORKBUDDY.md)：WorkBuddy 入口。

三份都是薄壳，回指同一份 [SKILL.md](allincms-content-ops/SKILL.md)，不分叉规则。

## 联系方式

微信（Tony Pan）：

![微信二维码](https://cos.files.maozhishi.com/data/web/web-files/wx/tony-apan.png)
