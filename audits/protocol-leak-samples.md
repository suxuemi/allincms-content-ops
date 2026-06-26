# Protocol Leak Samples

Real first-message screenshots from AI sessions, annotated for protocol-narration leaks. Maintainer pastes at least one sample per release; `audit_skill_meta.py` (`protocol-leak-samples-fresh` check) flags the file as stale if the latest entry is > 60 days old.

The purpose: behavior rules like "don't narrate the protocol" can't be greppedfor. The compensating mechanism is periodic sampling — read the actual first messages users see, note leaks, and feed corrections back into `first-contact.md`.

## Schema

```yaml
- date: YYYY-MM-DD
  release: vX.Y.Z
  status: leak | clean | mixed
  source: <short note, e.g. "user-reported screenshot v0.5 install">
  message: |
    <verbatim first-message text from the AI>
  annotations:
    - line: 1
      issue: protocol-narration | tier-paraphrase | missing-anchor | other
      note: <what's wrong + fix>
```

## Samples

### Sample 1 — v0.5.0 install screenshot (LEAK)

```yaml
- date: 2026-06-26
  release: v0.5.0
  status: leak
  source: real user-pasted screenshot — first AI message after `cd ~/skills` install prompt
  message: |
    已按要求处理：
    - /Users/tony/skills/allincms-content-ops 已存在，所以执行了 git pull --ff-only
    - 当前版本：v0.5.0，commit 6a8fbaf
    - 已读取 allincms-content-ops/SKILL.md 和 allincms-content-ops/references/first-contact.md
    - 没有 rm -rf，也没有污染当前项目

    环境诊断缓存是今天的，可复用：git, python, PicGo 是 strong；pdftotext, pandoc 缺失，所以 PDF / Word / PPT 抽取能力降级；Current Site 缺 Browser profile，后续涉及 AllinCMS 后台、发布、监控会先要求补字段。

    现在按 first-contact 从公司上下文开始。第一问，只答一句就行：你卖什么？
  annotations:
    - issue: tier-paraphrase
      note: |
        raw "strong / 缺失 / 降级" leaked to user.
        Should use `tooling-matrix.md` `user_facing_phrasing`: e.g. "想丢 PDF / Word 给我得装 pdftotext / pandoc，现在跳过没事".
    - issue: protocol-narration
      note: |
        Banned phrase: "现在按 first-contact 从公司上下文开始".
        Fixed in v0.6 § Self-check banned-phrase list.
    - issue: missing-anchor
      note: |
        "已读取 SKILL.md 和 first-contact.md" — drop the verb `已读取`,
        keep the file names on the anchor line per v0.6 Phase 0 shape:
        `✓ 装好了 (v0.5.0 @ 6a8fbaf · SKILL.md + first-contact.md)`.
    - issue: other
      note: |
        "没有 rm -rf，也没有污染当前项目" — this is a default behavior,
        not a user signal. Drop.
    - issue: protocol-narration
      note: |
        "第一问，只答一句就行：你卖什么？" — no progress (X/N),
        no scope ("产品名一句话就好"), no preview of upcoming questions.
        Fixed in v0.6 Phase 2 § Progress hint section.

<!-- entries-end -->
```
