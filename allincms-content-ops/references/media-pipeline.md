# Media Pipeline

Where uploaded image URLs come from and the rule about not mixing hosts.

## Choose one host per project, stick with it

The skill supports two image hosts:

1. **PicGo** (desktop app + plugin ecosystem) — see `references/media-picgo.md`
2. **Cloudflare R2** (S3-compatible, cheap, no desktop app needed) — set up via `scripts/r2_setup.py`

Both are valid. **Don't mix them in one project.** If you publish 30 articles with PicGo-uploaded URLs (`cos.files.maozhishi.com`) and then switch new articles to R2 (`r2.dev` or your custom domain), you end up with:

- Two domains in `media/index.md`
- Old articles linking to old host, new ones to new host
- Risk: if you stop paying for the old host, half your images 404 silently
- `library_health.py` won't catch this because URLs validate independently

`doctor.py` has a `media_mix × media` check that warns when it sees ≥ 2 distinct image-host domains in `media/index.md`. If you see that warning, decide one of:

- **Stay split** (e.g. old PicGo for legacy posts, R2 for new): acknowledge by adding a comment to `media/index.md` explaining the cutoff date; `doctor.py` warn stays but you've consciously accepted it
- **Migrate** (run `scripts/migrate_media.py` — planned for v0.9+; for now do it manually):
  1. Download all images from old host into `media/uploaded-migrated/`
  2. Re-upload via new host (`r2_upload.py` or PicGo)
  3. `find` + `sed` to rewrite URLs in `web/published/*.md` and `web/drafts/*.md`
  4. Update `media/index.md` rows
  5. Verify with `library_health.py --check dead_links`

## Choosing PicGo vs R2

| Concern | PicGo | R2 |
|---|---|---|
| Setup | install desktop app + plugin | 4 clicks on Cloudflare + paste 4 values once |
| Recurring cost | depends on host plugin (some free, some paid) | free up to 10 GB storage, generous egress allowance |
| Cross-platform | Mac / Win / Linux desktops | Windows / Linux servers, headless OK |
| Custom domain | per-plugin | yes, via Cloudflare custom domain bind |
| Public URL stability | depends on host TOS (e.g. some cancel free tier) | Cloudflare R2 + custom domain = stable |
| Native AI agent | shell call to `picgo_batch_upload.py` | shell call to `r2_upload.py` |

For **new projects**, R2 is the lower-friction choice — no desktop app needed, headless-friendly, AI agents on any host can call it.

For **existing PicGo projects**, keep PicGo unless you have a reason to switch (cost, plugin abandoned, etc.).

## `media/index.md` schema (both hosts)

Each row is one uploaded file, regardless of host:

| Source | Processed file | Uploaded URL | Alt | Used in |
|---|---|---|---|---|
| local path | (optional) | full URL | alt text | comma-list of consumer drafts |

`library_health.py` orphan_media check: rows with empty `Used in` after N days (default 90) → warning. Not host-specific.

## Configuration files

- PicGo: relies on its desktop app; no skill-side credentials file
- R2: `~/.config/allincms-content-ops/r2.toml` (gitignored at `~`-level by default; **never** committed)

If you accidentally commit `r2.toml` to a project: rotate the access key in the Cloudflare dashboard immediately (don't just `git rm` — git history retains it).
