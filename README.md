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

## 给 AI 用（一句话安装）

复制下面这段贴给 Claude Code / Codex / Cursor / 任何 AI 编程助手——AI 会自己装好、用你的语言介绍这套 skill、列几个常见用法，再问你想从哪儿开始：

````text
帮我装这套 skill 并按它的 first-contact 协议带我入门：
https://github.com/suxuemi/allincms-content-ops

请在 ~/skills 下 clone（不要污染我当前项目），然后读 allincms-content-ops/SKILL.md + allincms-content-ops/references/first-contact.md，按 first-contact 的脚本跟我开始对话。环境注意：没 shell 就告诉我手动跑、不要假装；Windows 用 python 不要 python3；已 clone 就 git pull、禁 rm -rf。
````

> 装完 AI 会：① 用你说话的语言（中文/英文自动判断）一句话讲清楚这套 skill 解决什么问题 → ② 列 3-5 个具体起点场景（起草发布 / 监控竞品 / 审已有页 / 初始化新项目 / 先逛逛） → ③ 问你一个 meta 问题让你说清现在最想做什么。回答后才进 SKILL.md 正式 Workflow。

> 想跳过启发式、直接给 AI 一个具体任务？见 [INSTALL.md](INSTALL.md) 的"直给任务版"。

> **已经装过想拉最新版**？把这段贴给 AI：
> ```
> 帮我把这套已经装好的 skill 拉到最新版：
> cd ~/skills/allincms-content-ops
> python3 allincms-content-ops/scripts/update_skill.py
> ```
> AI 会跑 dry-run、列变更、问你要不要更新；同意后真更新；拉到的新 SKILL.md / references 会被 AI 重读后再按新规则继续。冲突或异常（detached HEAD、本地未推送的 skill commit、网络不通）会停下来报错，不会硬上覆盖你的内容。

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
