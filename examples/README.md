# Examples

Reference drafts a newbie can read alongside `references/markdown-style-guide.md` to see "what does a complete, well-filled draft look like?"

## Files

- `sample-article-zh/article.md` — Chinese article reference
- `sample-article-en/article.md` — English article reference

Each is a fully filled `web/drafts/*.md`-shaped file:

- All 20 frontmatter fields populated with realistic example values
- ~400-word body with 3 H2 sections, internal links, and one credibility evidence reference
- Comments inline explaining each non-obvious choice

## ⚠️ DO NOT COPY identity fields literally

The examples use the literal string **`__REPLACE_ME__`** for every field that's unique to your AllinCMS site:

```yaml
allincms:
  site_id: __REPLACE_ME__
  canonical_url: __REPLACE_ME__
author: __REPLACE_ME__
```

`audit_content.py` has a Hard Gate (added v0.5.0): any frontmatter still containing `__REPLACE_ME__` blocks publish. This prevents accidentally shipping an example file's identity by forgetting to override it.

## How to use

```bash
# 1. Copy the example into your drafts directory
cp examples/sample-article-zh/article.md web/drafts/my-first-real-article.md

# 2. Replace every __REPLACE_ME__ with your real value
#    (audit_content.py will tell you exactly which lines)
python3 allincms-content-ops/scripts/check_draft.py web/drafts/my-first-real-article.md

# 3. Once frontmatter is filled, write your real body and run the full audit
python3 allincms-content-ops/scripts/audit_content.py web/drafts/my-first-real-article.md
```

## Why examples beat documentation

A 20-field frontmatter spec is hard to internalize. A fully-filled real-shape example shows:

- How long should `meta_description` actually be in practice?
- How does `credibility_evidence:` look as a YAML list?
- How explicit should `differentiation:` be?
- Where do internal links go in the body?

Read the example once; the spec becomes obvious.
