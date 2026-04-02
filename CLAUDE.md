# dropbrain-studio

Static site for dropbrain.io, hosted on GitHub Pages.

## Repo structure

```
index.html              Main portfolio page listing all apps
support.html            Central support hub linking to per-app support
sitemap.xml             Sitemap (auto-updated by blog build script)
robots.txt
CNAME                   GitHub Pages custom domain (dropbrain.io)

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

Push to `main`. GitHub Pages serves the repo root at dropbrain.io.

## Style

All pages use a dark theme with consistent CSS variables (`--bg: #0c0c0e`, `--surface: #141416`, etc.). There is no shared CSS file — each HTML page inlines its styles. The blog build script embeds shared CSS into generated pages.

## Support pages

Each app has its own `support.html` with app-specific FAQ. The root `support.html` is a central hub linking to all per-app support pages. Both the app landing pages and the main index link to support.
