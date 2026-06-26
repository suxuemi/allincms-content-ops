#!/usr/bin/env python3
"""Fixture-based smoke test for suggest_internal_links.py.

Locks the ranking so future weight tweaks surface as a behavior change
in CI (Ffalsifiability.1 from codex round v0.4.0-r1).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "allincms-content-ops" / "scripts"))

from suggest_internal_links import parse_published_index, score_candidate  # noqa: E402


PUBLISHED_FIXTURE = """# Published Index

| Date | URL | Type | Category | Tags | Persona | Primary query | Cover | Audit score | Source draft |
|---|---|---|---|---|---|---|---|---|---|
| 2026-06-01 | /blog/warm-up-domain | article | deliverability | warmup, smtp | saas-founder | how to warm up a domain | | 8.7 | web/drafts/warm-up-domain.md |
| 2026-06-05 | /blog/cold-email-templates | article | playbook | templates, cold-email | saas-founder | cold email templates | | 8.6 | web/drafts/cold-email-templates.md |
| 2026-06-10 | /products/agently-mail | product | products | smtp, warmup, deliverability | dev | agently mail | | 8.9 | web/products/agently-mail.md |
| 2026-06-12 | /blog/foreign-trade-seo | article | seo | seo, foreign-trade | founder | foreign trade seo guide | | 8.5 | web/drafts/foreign-trade-seo.md |
"""

DRAFT_FM = {
    "tags": ["warmup", "smtp"],
    "persona": "saas-founder",
    "category": "deliverability",
    "secondary_queries": ["how to warm up domain", "smtp deliverability"],
}


def test_overlap_topscore():
    rows = parse_published_index(PUBLISHED_FIXTURE)
    assert len(rows) == 4
    scored = []
    for r in rows:
        s, _ = score_candidate(DRAFT_FM, r)
        scored.append((s, r["url"]))
    scored.sort(key=lambda x: x[0], reverse=True)
    print(scored)
    # warm-up-domain: shares warmup + smtp + persona + category + query tokens → highest
    assert scored[0][1] == "/blog/warm-up-domain", scored
    # agently-mail product: shares warmup + smtp tags (different persona / category) → second
    assert scored[1][1] == "/products/agently-mail", scored
    # foreign-trade-seo: no overlap → bottom or zero
    assert all(s > 0 for s, u in scored[:2])


def test_empty_draft_no_suggestions():
    rows = parse_published_index(PUBLISHED_FIXTURE)
    empty_fm = {"tags": [], "persona": "", "category": "", "secondary_queries": []}
    for r in rows:
        s, _ = score_candidate(empty_fm, r)
        assert s == 0, f"expected 0 score for empty draft, got {s} on {r['url']}"


if __name__ == "__main__":
    test_overlap_topscore()
    test_empty_draft_no_suggestions()
    print("test_suggest_links: 2/2 passed")
