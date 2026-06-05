# dropbrain-studio

Static site for dropbrain.io, hosted on GitHub Pages.

## Repo structure

```
index.html              Main portfolio page listing all apps
support.html            Central support hub linking to per-app support
sitemap.xml             Sitemap (auto-updated by blog build script)
robots.txt
CNAME                   GitHub Pages custom domain (dropbrain.io)
assets/                 Shared assets
  theme.css             Shared light/dark palette + toggle button styles (every page links it)
  theme.js              Injects the sun/moon toggle, persists choice to localStorage
  (App Store badge SVG, etc.)

hemsaga/                App landing pages — each app has its own directory
dropbrain/                containing index.html, support.html, and
migraineme/               privacy_policy.html
lookupsilly/
airmustacheman/

blog/
  _posts/               Markdown source files for blog posts
  build.py              Build script — converts markdown to static HTML
  index.html            Generated blog index (do not edit by hand)
  images/               Blog post images
  <slug>/index.html     Generated post pages (do not edit by hand)

.github/workflows/
  pages.yml             GitHub Actions deploy workflow
```

## Apps

| App | Directory | Status |
|-----|-----------|--------|
| Hemsaga | `hemsaga/` | Live on App Store |
| DropBrain | `dropbrain/` | Live on App Store |
| Migraine Me | `migraineme/` | Live on App Store |
| Look Up, Silly! | `lookupsilly/` | Coming soon |
| Air Mustache Man | `airmustacheman/` | Live on App Store |

Each app directory has `index.html` (landing page), `support.html`, and `privacy_policy.html`. The main `index.html` at the repo root links to all of them.

## Blog

### Adding a new blog post

1. Create a markdown file in `blog/_posts/` (any filename, must end in `.md`).

2. Add frontmatter at the top:

```yaml
---
title: "Post Title Here"
date: 2026-04-02
slug: post-url-slug
description: "One-line description for index and meta tags."
tags: tag1, tag2, tag3
image: "/blog/images/optional-og-image.png"
ai_context: "Optional hidden context for AI crawlers. Not shown to users."
---
```

Required fields: `title`, `slug`. The `slug` determines the URL (`/blog/<slug>/`).

3. Write the post body in markdown below the frontmatter. Supports fenced code blocks, tables, and images. Image alt text becomes a visible caption.

4. Run the build script:

```bash
python3 blog/build.py
```

This generates:
- `blog/<slug>/index.html` — the post page
- `blog/index.html` — updated blog index (sorted newest first)
- `sitemap.xml` — new post URL added if missing

5. Commit both the markdown source and the generated HTML files.

### Editing existing posts

Edit the markdown in `blog/_posts/`, then re-run `python3 blog/build.py`. The generated HTML files in `blog/<slug>/` and `blog/index.html` will be overwritten.

### Blog images

Place images in `blog/images/` and reference them as `/blog/images/filename.png` in markdown.

## Deployment

Push to `main`. A GitHub Actions workflow (`.github/workflows/pages.yml`) builds and deploys the site to dropbrain.io.

**Important:** The workflow explicitly lists which files and directories get copied into `_site/`. If you add a new root-level file or directory, you must add it to the `cp -r` lines in `pages.yml` or it will not be deployed (you'll get a 404).

Current deploy list:
- Root files: `index.html`, `support.html`, `CNAME`, `llms.txt`, `robots.txt`, `sitemap.xml`
- Directories: `assets`, `airmustacheman`, `dropbrain`, `hemsaga`, `lookupsilly`, `migraineme`
- Blog: copied via `rsync` excluding `build.py` and `_posts/`

## Style

All pages use a warm theme that is **light by default** with a **dark toggle**. Per-page styles are still inlined in each HTML file's `<style>` block (there is no shared component CSS), but the **color palette and theme toggle are shared** via `assets/theme.css` and `assets/theme.js` — see Theming below.

## Theming (light/dark)

The palette comes from the `/present` skill: warm cream light default (`--bg: #FAF9F7`), warm dark (`--bg: #1A1916`). Light is always the first-visit default; the user's toggle choice is remembered in `localStorage` (key `db-theme`). OS `prefers-color-scheme` is intentionally **not** followed.

**How it works — single source of truth in `assets/`:**

- `assets/theme.css` defines the neutral palette under `:root` (light) and `[data-theme="dark"]` (dark), mapped onto the variable names every page already uses (`--bg`, `--surface`, `--text`, `--text-secondary`, `--text-muted`, `--border`, `--border-hover`). It also styles the fixed top-right `.theme-toggle` button and its sun/moon icon swap. **Change the site-wide palette here, in one place.**
- `assets/theme.js` injects the toggle button into `<body>`, flips the `data-theme` attribute on `<html>`, and writes `db-theme` to `localStorage`. Loaded with `<script defer src="/assets/theme.js"></script>` before `</body>`.

**Every page wires the theme with the same three additions:**

1. In `<head>`, a tiny inline FOUC guard (must be inline + synchronous, before the page renders, so a saved-dark choice doesn't flash light):
   ```html
   <script>try{if(localStorage.getItem('db-theme')==='dark')document.documentElement.setAttribute('data-theme','dark')}catch(e){}</script>
   ```
2. In `<head>`, `<link rel="stylesheet" href="/assets/theme.css">` (absolute path — works from root, `/<app>/`, and `/blog/<slug>/`).
3. Before `</body>`, `<script defer src="/assets/theme.js"></script>`.

Pages must **not** redefine the neutral palette variables in their inline `:root` — those come from `theme.css`. Only per-app accents stay inline.

**Per-app accent colors** (`--accent` on app pages; `--dropbrain`/`--migraineme`/… on the root index) are tuned per theme: a darker value in `:root` for contrast on cream, and the brighter original under `[data-theme="dark"]`. Pattern on an app page:
```css
:root { --accent: #2D6CB8; }            /* deeper, readable on cream */
[data-theme="dark"] { --accent: #7AB8FF; } /* original bright value */
```

**Adding a new page:** copy the three additions above, drop the neutral palette from its inline `:root`, and give any accent a light + dark value. **Adding a new app:** also add light/dark values for its token to the root `index.html` `:root` and `[data-theme="dark"]` blocks.

**Blog:** `blog/build.py` injects the same three additions into `POST_TEMPLATE` and `INDEX_TEMPLATE`; the neutral palette is **not** in `SHARED_CSS` (it comes from `theme.css`). Code blocks use the `atom-one-dark` highlight theme, so they're given an explicit dark background (`#282c34`) and light foreground (`#abb2bf`) in `POST_CSS` — they stay dark in both themes (don't make them follow `--surface`, or un-highlighted code goes invisible on a light page). Rebuild with `python3 blog/build.py` after any palette/template change.

## Support pages

Each app has its own `support.html` with app-specific FAQ. The root `support.html` is a central hub linking to all per-app support pages. Both the app landing pages and the main index link to support.
