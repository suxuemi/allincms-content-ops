# Workspace Dashboard Snapshot — Regression Fixture

Captures the DOM structure of `https://workspace.laicms.com/` that `references/current-site-discovery.md` relies on. When workspace ships a redesign, update this file in the same PR as the discovery selectors.

## Login wall structure (Step 3 signal)

```html
<!-- expected when not logged in -->
<title>登录 - AllinCMS</title>
<form action="/auth/login" method="post">
  <input type="email" name="email" />
  <input type="password" name="password" />
  <button type="submit">登录</button>
</form>
```

Signals for "login wall":
1. URL contains `/login` or `/auth/`
2. `<title>` matches `登录` or `Sign in`
3. `<input type="password">` present

≥ 2 of these → confirmed login wall.

## Dashboard structure (Step 4 signal)

```html
<!-- expected when logged in, listing sites -->
<title>工作台 - AllinCMS</title>
<div class="site-list" data-testid="site-list">
  <a href="/<site_id>/" class="site-card" data-site-id="<site_id>">
    <h3>站点名称</h3>
    <p class="domain">https://example.com</p>
  </a>
  <!-- more cards -->
</div>
```

Signals for "dashboard":
1. URL matches `workspace.laicms.com/?` (root)
2. `<title>` matches `工作台` or `Dashboard`
3. `data-testid="site-list"` OR class `site-list` exists

≥ 2 → confirmed dashboard.

Per-card signals (Step 4 list scraping):
1. `<a class="site-card">` with `data-site-id` attribute
2. Direct child `<h3>` with site name
3. `<p class="domain">` with `https://` URL

≥ 2 → confirmed site card.

## Site detail page structure (Step 5 site_id grab)

```html
<!-- expected after clicking into a site -->
<title>{site_name} - AllinCMS</title>
<!-- URL pattern: workspace.laicms.com/<site_id>/{section} -->
```

Signals for site_id extraction:
1. URL matches `workspace\.laicms\.com/([a-z0-9-]+)/`
2. Page has a back link to dashboard

front_end_domain extraction:
- Look for the site's "Domains" section (sidebar nav)
- Or grab from dashboard site card before navigating

## Update protocol

When workspace.laicms.com structure changes:

1. Capture new HTML in the relevant section above (replace old).
2. Update DOM selectors in `references/current-site-discovery.md`.
3. Verify `audit_skill_meta.py` `discovery-fixtures-current` check still passes.
4. Note the change in CHANGELOG `## [Unreleased]`.
5. Bump version per `CONTRIBUTING.md` decision tree (likely PATCH if behavior unchanged, MINOR if signals augmented).

## Last verified

Date: 2026-06-26
Verified against: `workspace.laicms.com` as of v0.7.0 release.
