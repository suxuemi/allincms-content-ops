[English](docs/en/INSTALL.md) | 中文

# 安装

本文同时面向新用户和 AI agent。Agent 应先识别当前工具，再走对应安装路径。

## 安装内容

可复用的 skill 目录：

`allincms-content-ops/`

包含：

- `SKILL.md`（操作契约，英文，单一源）
- `agents/openai.yaml`
- `references/`（细分规范）
- `scripts/`（init / ingest / monitor / audit / picgo 脚本）

## Codex 安装

如果该目录不在 Codex skill 目录下，软链或复制：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
ln -sfn "$(pwd)/allincms-content-ops" "${CODEX_HOME:-$HOME/.codex}/skills/allincms-content-ops"
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" "$(pwd)/allincms-content-ops"
```

不允许软链就用复制：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R "$(pwd)/allincms-content-ops" "${CODEX_HOME:-$HOME/.codex}/skills/allincms-content-ops"
```

## Claude 安装

Claude 按顺序读：

1. [CLAUDE.md](CLAUDE.md)
2. [allincms-content-ops/SKILL.md](allincms-content-ops/SKILL.md)
3. [PROJECT_INDEX.md](PROJECT_INDEX.md)

用 Claude Code 项目 skill 时，把 `allincms-content-ops/` 复制或软链到该环境的项目 skill 位置。**根目录这份保留为权威源**，除非显式要求分叉。

## WorkBuddy 安装

WorkBuddy 按顺序读：

1. [WORKBUDDY.md](WORKBUDDY.md)
2. [allincms-content-ops/SKILL.md](allincms-content-ops/SKILL.md)
3. [PROJECT_INDEX.md](PROJECT_INDEX.md)

## 初始化新内容项目

```bash
python3 allincms-content-ops/scripts/init_content_ops_project.py .
```

会创建 `raw/`、`wiki/`、`web/`、`monitoring/`、`media/`、`audits/` 及各自的 `index.md`。

## 验证安装

```bash
python3 -m py_compile allincms-content-ops/scripts/*.py
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" allincms-content-ops
python3 allincms-content-ops/scripts/audit_content.py .
```

期望：

- skill 校验输出 `Skill is valid!`
- 脚本编译无错
- audit 报告 0 issue（除非真有 web 草稿缺元数据 / 含 AI 味 / 含残留 / 图片问题）

## 关键 CLI

```bash
# 全量审核（默认 full 模式）
python3 allincms-content-ops/scripts/audit_content.py .

# 微调（typo、单字段）只检查残留 + AI 味 + 图片，不卡 frontmatter
python3 allincms-content-ops/scripts/audit_content.py --light path/to/file.md

# raw 不可变校验
python3 allincms-content-ops/scripts/audit_content.py --check-raw-immutable .

# web → wiki 反向链校验
python3 allincms-content-ops/scripts/audit_content.py --check-backlinks .

# 发布前最后一道：检查指定 slug 的 audit 文件是否 pass: true
python3 allincms-content-ops/scripts/audit_content.py --require-audit-file my-slug .
```
