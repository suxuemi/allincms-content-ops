# SEO and GEO Rules

## Source Principles

Use people-first SEO as the baseline. Google Search Central describes SEO as helping search engines understand content and helping users decide whether to visit. It also warns there are no secrets that guarantee first ranking. Apply SEO to useful content, not search-engine-first filler.

For generative search, Google states that core SEO remains relevant because generative AI features are grounded in search ranking and retrieval systems. Its guidance emphasizes unique, non-commodity content, clear structure, high-quality images/video, and avoiding mass pages made only for query variations.

The GEO paper formalizes optimization for generative engines and reports that visibility improvements depend on domain-specific methods. Treat GEO as a visibility layer on top of helpful SEO, not a reason to stuff citations or keywords.

Verify current search documentation before making high-stakes SEO claims. Search systems and AI answer surfaces change; keep durable rules here and collect live evidence in `raw/` when the decision depends on current behavior.

## Page Requirements

Each page or article needs:

- One clear primary intent.
- Descriptive URL/slug.
- Useful title and H1.
- Meta title and meta description written for clicks, not stuffing.
- Clear headings that follow the buyer's decision path.
- Internal links to relevant product, guide, category, and contact pages.
- Evidence, screenshots, examples, or workflows that competitors do not provide.
- Image filename, alt, caption, and nearby context.
- Schema recommendation when relevant: `Article`, `Product`, `BreadcrumbList`, `FAQPage`, `Organization`, or `VideoObject`.

## Search Intent Matrix

Classify every topic:

- **Problem aware**: "why is my export website not getting inquiries"
- **Solution aware**: "AI website builder for exporters"
- **Product aware**: "AllinCMS product catalog module"
- **Implementation**: "bind Cloudflare domain AllinCMS"
- **Comparison**: "AllinCMS vs WordPress for export website"
- **Troubleshooting**: "HTTPS not active after domain binding"
- **Commercial**: "export website builder pricing"

The article structure must match the intent. Do not write a broad essay for a troubleshooting query.

## GEO Additions

To be useful in AI answers:

- Put concise answer blocks near the top.
- Include exact definitions and distinctions.
- Use tables for comparisons and decision criteria.
- Add source-backed facts and practical examples.
- Use consistent terminology from `wiki/glossary.md`.
- Include entity-rich context: product names, roles, workflows, regions, tools, and constraints.
- Avoid unsupported statistics. If a number matters, cite or mark as estimated.
- Make concise extractable passages that can stand alone in an AI answer.

## Image SEO

Follow these rules:

- Use short descriptive filenames.
- Write alt text that describes the image in context.
- Place images near relevant text.
- Avoid generic names such as `image1.jpg`.
- Prefer stable image URLs; do not use changing temporary URLs.
- Use the same important images on desktop and mobile.
- Use high-quality images and supported formats.

## Mobile and Indexing

Mobile content must be equivalent to desktop:

- Same primary content and meaningful headings.
- Same metadata intent.
- Same structured data when AllinCMS supports it.
- Same image alt text.
- No horizontal overflow at 390px.
- Primary content must not require interaction to load.

## Anti-Spam

Reject content that:

- Exists only to target query variants.
- Summarizes competitors without adding product-specific insight.
- Uses AI-generated filler, fake expertise, fake people, fake metrics, or unverified awards.
- Promises unsupported outcomes.
- Uses keyword repetition instead of useful headings and examples.
