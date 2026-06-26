# Project Index

This is the root index for the AllinCMS content operations kit.

## Human Entry

- [README.md](README.md)：概览（[English](docs/en/README.md)）
- [INSTALL.md](INSTALL.md)：安装与验证（[English](docs/en/INSTALL.md)）
- [QUICKSTART.md](QUICKSTART.md)：新手流程（[English](docs/en/QUICKSTART.md)）

**默认中文**（根目录三份）；English 翻译在 `docs/en/`。**agent 操作契约**（SKILL.md / references / scripts）只维护英文，单一规则源不分叉。

## Agent Entry

- [AGENTS.md](AGENTS.md): Codex and generic agents.
- [CLAUDE.md](CLAUDE.md): Claude.
- [WORKBUDDY.md](WORKBUDDY.md): WorkBuddy.
- [allincms-content-ops/SKILL.md](allincms-content-ops/SKILL.md): reusable skill.

## Content System

- [raw/index.md](raw/index.md): original sources and extracted Markdown.
- [raw/competitors/index.md](raw/competitors/index.md): competitor captures.
- [wiki/index.md](wiki/index.md): distilled knowledge.
- [wiki/glossary.md](wiki/glossary.md): terminology.
- [wiki/lessons.md](wiki/lessons.md): run-time corrections (proposed → approved → merged); single channel for skill iteration.
- [wiki/content-opportunities.md](wiki/content-opportunities.md): proposed, approved, rejected, drafting, and published topics.
- [web/index.md](web/index.md): website content.
- [web/published/index.md](web/published/index.md): published URLs.
- [web/categories/index.md](web/categories/index.md): category index.
- [web/tags/index.md](web/tags/index.md): tag index.
- [monitoring/index.md](monitoring/index.md): monitoring runs.
- [media/index.md](media/index.md): image assets and uploads.
- [audits/index.md](audits/index.md): audit evidence and scores.

## Current Site

> **Hard prerequisite.** If any field below is empty, STOP and request values before any other action. Do not proceed with placeholders.

- AllinCMS site id:
- Front-end domain:
- Workspace URL: https://workspace.laicms.com/
- Browser profile (which logged-in profile to use): system default
- Default content language: zh-CN
- deployment: saas

> `Default content language` is site-wide (drives `new_draft.py` body template + `site_health.py` `<html lang>` check). Per-draft `region:` lives in each draft's frontmatter — different axis, not overridden.
> `deployment` is read by `references/current-site-discovery.md`. Default `saas` opens workspace.laicms.com; change to `self-hosted` if you run AllinCMS yourself.
- Default content language: zh-CN

## Operating Rule

Mode-select first (light vs full per SKILL.md). Full-mode: ingest → wiki → search intent → web draft → media → AllinCMS draft → adversarial audit (isolated subagent) → publish gated by `audits/<slug>-<date>.md` `pass: true` → index → reflect to `wiki/lessons.md`.

Pass criteria: total ≥ 8.5 AND every area ≥ 70% AND zero blocking-residue AND ≥ 5 logged objections with responses.
