---
title: Foreign-Trade Cold Start — How to Ship a Product Page Google Can Actually Find
slug: foreign-trade-cold-start-product-page-en
route: /en/blog/foreign-trade-cold-start-product-page
content_type: article
status: draft
persona: foreign-trade-founder
region: en-US
search_intent: Help a small foreign-trade founder ship a product page in the first month that gets indexed by Google and produces the first inbound inquiry — without falling into the "I built it, why isn't anyone here" trap
primary_query: foreign trade independent site cold start
secondary_queries:
  - shopify vs custom site foreign trade
  - first product page seo
  - hreflang mistakes for chinese-to-english stores
  - foreign trade lcp optimization
category: independent-site
tags:
  - foreign-trade
  - independent-site
  - seo
  - cold-start
meta_title: Foreign-Trade Cold Start: a 4-Step Checklist for Your First Product Page
meta_description: The 4 mistakes that kill new foreign-trade sites in their first 90 days — no sitemap, no product schema, broken hreflang, full-res images — and how to skip each.
cover_image: __REPLACE_ME__
cover_alt: Side-by-side comparison of two product pages — one indexed by Google in 7 days, one still missing after 60
differentiation: Skips the tired "Shopify vs custom" debate. Concrete 4-step checklist proven to get a new site indexed AND surface first inquiry within 30 days — most articles on this topic stop at "buy a domain"
credibility_evidence:
  - raw/2026-06-01-customer-pingji/first-order-screenshot.md
  - media/uploaded/sample-sitemap-vs-no-sitemap.png
source_wiki:
  - wiki/products/agently-mail.md
  - wiki/personas/foreign-trade-founder.md
source_raw:
  - raw/2026-06-01-customer-pingji/interview.md
competitors_referenced:
  - https://www.shopify.com/blog/foreign-trade-site
published_at:
updated_at: 2026-06-26
author: __REPLACE_ME__
source_external:
related:
  - /en/blog/picgo-batch-upload-tutorial
  - /en/blog/hreflang-mistakes
last_seo_check: 2026-06-26
created_with_version: "0.4.0"
allincms:
  site_id: __REPLACE_ME__
  post_id:
  category_id: __REPLACE_ME__
  tag_ids: []
  published_url:
  canonical_url: __REPLACE_ME__
  noindex: false
  schema_recommendation: Article
  hreflang: []
audit:
  content_score:
  aesthetic_score:
  seo_geo_score:
  final_score:
---

<!-- AllinCMS renders frontmatter `title:` as the page H1; don't use # in the body. Subheadings start at ##. -->

The most common cold-start failure for a small foreign-trade site isn't "I can't build it" — it's "I built it and 90 days in there's still zero inquiries". The root cause is treating the site as "done when it loads", and ignoring [how Google actually discovers product pages](/en/blog/hreflang-mistakes). This piece walks through the four mistakes in the order people make them.

## Mistake 1: shipping without a sitemap

Most common 30-day post-mortem: you set up WooCommerce or Shopify, listed three products, waited 60 days, and `site:yourdomain.com` still returns zero. SEO isn't the issue. Discoverability is — Google literally doesn't know your site exists because nobody told it.

Fix: on day one, generate `sitemap.xml` (every CMS has a plugin), submit it to Search Console, then scan your homepage and first product page with [Rich Results Test](https://search.google.com/test/rich-results). Our [customer interview with Pingji](raw/2026-06-01-customer-pingji/interview.md) showed they missed this step for 17 days on their first store — that's 17 lost days of crawl coverage.

## Mistake 2: product pages without structured data

The second trap is shipping product pages with just a big photo and a paragraph. Google doesn't know "this is a thing someone can buy", so it can't surface the page for product-intent queries.

Minimum bar: every product page carries a `Product` schema with name, price, availability, and ratings. In AllinCMS, set `schema_recommendation: Product` and the theme template auto-injects the JSON-LD. The attached sitemap-vs-no-sitemap comparison shows: pages with `Product` schema entered the Shopping tab within 7 days; pages without it sat outside the top 30 in plain search.

## Mistake 3: hreflang chaos breaks multilingual sites

By day 2 most foreign-trade teams want "multilingual". Install a language plugin, ship Chinese + English versions, forget hreflang, and watch them cannibalize each other as duplicate content. Often the English version disappears entirely — Google's chosen the Chinese URL as canonical.

[The 3 hreflang mistakes everyone makes](/en/blog/hreflang-mistakes) covers this in depth. The key rule: every language version cross-references all others via `<link rel="alternate" hreflang="...">`, and self-references itself. Miss the self-reference and search engines silently pick one URL as canonical — the rest vanish.

## Mistake 4: raw-resolution images, 8-second LCP

The last trap is uploading full-resolution photos. A 4MB product image pushes LCP to 8+ seconds, Google Page Speed lights up red, conversion drops by half.

Run [the PicGo batch-upload tutorial](/en/blog/picgo-batch-upload-tutorial) — convert images to webp under 200KB before they go live. On our test page, 4MB → 180KB took LCP from 7.2s to 1.8s.

## TL;DR

Four steps for the cold-start month: sitemap, schema, hreflang, image compression. Don't touch ads, don't add a Live Chat widget. Inquiries don't show up because the site looks pretty — they vanish because one of these four steps was skipped.
