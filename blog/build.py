#!/usr/bin/env python3
"""
Blog build script for dropbrain.io
Converts markdown posts in _posts/ to static HTML matching the site's dark design.
Only dependency: markdown (auto-installed if missing).
"""

import os
import sys
import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

try:
    import markdown
except ImportError:
    import subprocess
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--user', 'markdown'])
    except subprocess.CalledProcessError:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install',
                               '--break-system-packages', 'markdown'])
    import markdown

BLOG_DIR = Path(__file__).resolve().parent
POSTS_DIR = BLOG_DIR / '_posts'
SITE_ROOT = BLOG_DIR.parent
SITE_URL = 'https://dropbrain.io'

# ── Shared CSS ──────────────────────────────────────────────────────────────

SHARED_CSS = """\
*, *::before, *::after {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    --bg: #0c0c0e;
    --surface: #141416;
    --text: #e8e8ec;
    --text-secondary: #9898a0;
    --text-muted: #5a5a64;
    --border: #222226;
    --border-hover: #333338;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

body::before {
    content: '';
    display: block;
    height: 3px;
    background: linear-gradient(
        to right,
        #61BB46, #FDB827, #F5821F, #E03A3E, #963D97, #009DDC
    );
}

a {
    color: var(--text-secondary);
    text-decoration: none;
    transition: color 0.2s ease;
}

a:hover {
    color: var(--text);
}

.page {
    max-width: 720px;
    margin: 0 auto;
    padding: 0 24px;
}

header {
    padding: 44px 0 0;
    animation: fadeDown 0.7s ease both;
}

.wordmark {
    font-family: 'SF Mono', SFMono-Regular, ui-monospace, 'Menlo', 'Monaco', 'Cascadia Mono', monospace;
    font-size: 1.3rem;
    font-weight: 500;
    letter-spacing: -0.02em;
    color: var(--text);
}

.wordmark span {
    color: var(--text-muted);
    font-weight: 400;
    font-size: 0.75em;
    margin-left: 2px;
}

footer {
    border-top: 1px solid var(--border);
    padding: 28px 0 36px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    animation: fadeUp 0.55s ease 0.55s both;
}

footer a {
    font-size: 0.82rem;
    color: var(--text-muted);
}

footer a:hover {
    color: var(--text);
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(14px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeDown {
    from { opacity: 0; transform: translateY(-8px); }
    to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 680px) {
    header {
        padding: 32px 0 0;
    }
    footer {
        flex-direction: column;
        gap: 6px;
        text-align: center;
    }
}

@media (max-width: 400px) {
    .page {
        padding: 0 16px;
    }
}
"""

# ── Post page CSS ───────────────────────────────────────────────────────────

POST_CSS = """\
.post-header {
    padding: 56px 0 32px;
    animation: fadeUp 0.7s ease 0.1s both;
}

.post-title {
    font-size: clamp(1.8rem, 5vw, 2.6rem);
    font-weight: 600;
    line-height: 1.15;
    letter-spacing: -0.03em;
    color: var(--text);
}

.post-meta {
    margin-top: 16px;
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
}

.post-date {
    font-family: 'SF Mono', SFMono-Regular, ui-monospace, 'Menlo', monospace;
    font-size: 0.82rem;
    color: var(--text-muted);
}

.post-tags {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}

.post-tags .tag {
    font-size: 0.72rem;
    font-weight: 500;
    color: var(--text-muted);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 3px 10px;
    letter-spacing: 0.01em;
}

.post-content {
    padding-bottom: 56px;
    animation: fadeUp 0.7s ease 0.2s both;
}

.post-content h1 {
    font-size: 1.8rem;
    font-weight: 600;
    letter-spacing: -0.025em;
    margin: 48px 0 16px;
    color: var(--text);
}

.post-content h2 {
    font-size: 1.45rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    margin: 40px 0 14px;
    color: var(--text);
}

.post-content h3 {
    font-size: 1.15rem;
    font-weight: 600;
    letter-spacing: -0.015em;
    margin: 32px 0 12px;
    color: var(--text);
}

.post-content h4 {
    font-size: 1rem;
    font-weight: 600;
    margin: 28px 0 10px;
    color: var(--text-secondary);
}

.post-content p {
    font-size: 1rem;
    line-height: 1.72;
    color: var(--text-secondary);
    margin-bottom: 18px;
    font-weight: 300;
    letter-spacing: -0.01em;
}

.post-content ul,
.post-content ol {
    margin: 0 0 18px 24px;
    color: var(--text-secondary);
    font-weight: 300;
    line-height: 1.72;
}

.post-content li {
    margin-bottom: 6px;
}

.post-content li::marker {
    color: var(--text-muted);
}

.post-content blockquote {
    border-left: 3px solid var(--border-hover);
    margin: 24px 0;
    padding: 12px 20px;
    background: var(--surface);
    border-radius: 0 8px 8px 0;
}

.post-content blockquote p {
    color: var(--text-secondary);
    font-style: italic;
    margin-bottom: 0;
}

.post-content code {
    font-family: 'SF Mono', SFMono-Regular, ui-monospace, 'Menlo', monospace;
    font-size: 0.88em;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 5px;
    padding: 2px 6px;
    color: var(--text);
}

.post-content pre {
    margin: 24px 0;
    border-radius: 10px;
    overflow-x: auto;
}

.post-content pre code {
    background: none;
    border: none;
    border-radius: 0;
    padding: 0;
    font-size: 0.85rem;
    line-height: 1.6;
}

.post-content img {
    max-width: 100%;
    height: auto;
    border-radius: 10px;
    margin: 24px 0;
    display: block;
}

.post-content .image-caption {
    text-align: center;
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-top: -16px;
    margin-bottom: 24px;
    font-style: italic;
}

.post-content a {
    color: var(--text);
    text-decoration: underline;
    text-underline-offset: 3px;
    text-decoration-color: var(--border-hover);
    transition: text-decoration-color 0.2s ease;
}

.post-content a:hover {
    text-decoration-color: var(--text);
}

.post-content table {
    width: 100%;
    border-collapse: collapse;
    margin: 24px 0;
    font-size: 0.92rem;
}

.post-content th {
    text-align: left;
    font-weight: 600;
    color: var(--text);
    padding: 10px 14px;
    border-bottom: 2px solid var(--border);
}

.post-content td {
    padding: 10px 14px;
    color: var(--text-secondary);
    border-bottom: 1px solid var(--border);
}

.post-content hr {
    border: none;
    border-top: 1px solid var(--border);
    margin: 40px 0;
}
"""

# ── Index page CSS ──────────────────────────────────────────────────────────

INDEX_CSS = """\
.blog-header {
    padding: 56px 0 40px;
    animation: fadeUp 0.7s ease 0.1s both;
}

.blog-title {
    font-size: clamp(2rem, 5vw, 2.8rem);
    font-weight: 600;
    letter-spacing: -0.035em;
    color: var(--text);
}

.post-list {
    padding-bottom: 56px;
}

.post-item {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 24px 28px;
    margin-bottom: 16px;
    transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    opacity: 0;
    animation: fadeUp 0.55s ease both;
}

.post-item:hover {
    border-color: var(--border-hover);
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(255,255,255,0.02);
}

.post-item-title {
    font-size: 1.3rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    margin-bottom: 4px;
}

.post-item-title a {
    color: var(--text);
    text-decoration: none;
}

.post-item-title a:hover {
    color: var(--text);
}

.post-item-date {
    font-family: 'SF Mono', SFMono-Regular, ui-monospace, 'Menlo', monospace;
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-bottom: 10px;
}

.post-item-desc {
    font-size: 0.92rem;
    color: var(--text-secondary);
    line-height: 1.6;
    font-weight: 300;
    letter-spacing: -0.01em;
}

.post-item-tags {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-top: 12px;
}

.post-item-tags .tag {
    font-size: 0.7rem;
    font-weight: 500;
    color: var(--text-muted);
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 2px 9px;
    letter-spacing: 0.01em;
}

@media (max-width: 400px) {
    .post-item {
        padding: 18px 16px;
    }
}
"""


# ── Templates ───────────────────────────────────────────────────────────────

POST_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — dropbrain blog</title>
    <meta name="description" content="{description_attr}">
    <meta property="og:title" content="{title_attr}">
    <meta property="og:description" content="{description_attr}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{url}">
    {og_image}
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11/build/styles/atom-one-dark.min.css">
    <style>
{shared_css}
{post_css}
    </style>
</head>
<body>
    <div class="page">
        <header>
            <a href="/blog/" class="wordmark">&larr; dropbrain<span>.studio/blog</span></a>
        </header>

        <div class="post-header">
            <h1 class="post-title">{title}</h1>
            <div class="post-meta">
                <span class="post-date">{date}</span>
                {tags_html}
            </div>
        </div>

        <article class="post-content">
{content}
        </article>

        <footer>
            <a href="/blog/">&larr; Back to blog</a>
            <a href="/">dropbrain.studio</a>
        </footer>
    </div>

    {ai_context_section}

    <script type="application/ld+json">
{json_ld}
    </script>

    <script src="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11/build/highlight.min.js"></script>
    <script>hljs.highlightAll();</script>
</body>
</html>
"""

INDEX_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blog — dropbrain studio</title>
    <meta name="description" content="Development blog from dropbrain studio. App updates, feature deep-dives, and behind-the-scenes.">
    <meta property="og:title" content="Blog — dropbrain studio">
    <meta property="og:description" content="Development blog from dropbrain studio. App updates, feature deep-dives, and behind-the-scenes.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://dropbrain.io/blog/">
    <style>
{shared_css}
{index_css}
    </style>
</head>
<body>
    <div class="page">
        <header>
            <a href="/" class="wordmark">dropbrain<span>.studio</span></a>
        </header>

        <div class="blog-header">
            <h1 class="blog-title">Blog</h1>
        </div>

        <div class="post-list">
{post_items}
        </div>

        <footer>
            <a href="/">&larr; dropbrain.studio</a>
            <a href="/">Home</a>
        </footer>
    </div>
</body>
</html>
"""

POST_ITEM_TEMPLATE = """\
            <div class="post-item" style="animation-delay: {delay}s;">
                <h2 class="post-item-title"><a href="/blog/{slug}/">{title}</a></h2>
                <div class="post-item-date">{date}</div>
                <p class="post-item-desc">{description}</p>
                {tags_html}
            </div>"""


# ── Frontmatter parsing ────────────────────────────────────────────────────

def parse_frontmatter(text):
    """Parse YAML-like frontmatter between --- markers. No pyyaml needed."""
    if not text.startswith('---'):
        return {}, text

    end = text.find('---', 3)
    if end == -1:
        return {}, text

    raw = text[3:end].strip()
    body = text[end + 3:].strip()
    meta = {}

    for line in raw.split('\n'):
        line = line.strip()
        if not line or ':' not in line:
            continue
        key, _, value = line.partition(':')
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        meta[key] = value

    return meta, body


def parse_tags(tags_str):
    """Parse comma-separated tags."""
    if not tags_str:
        return []
    return [t.strip() for t in tags_str.split(',') if t.strip()]


def format_date(date_str):
    """Format a YYYY-MM-DD date for display."""
    try:
        d = datetime.strptime(date_str, '%Y-%m-%d')
        return d.strftime('%B %d, %Y')
    except (ValueError, TypeError):
        return date_str or ''


# ── Image caption post-processing ──────────────────────────────────────────

def add_image_captions(html_content):
    """Convert img alt text to visible captions below images."""
    def replace_img(match):
        full = match.group(0)
        alt_match = re.search(r'alt="([^"]+)"', full)
        if alt_match:
            alt = alt_match.group(1)
            if alt and alt.lower() not in ('image', 'img', ''):
                return full + f'\n<p class="image-caption">{html.escape(alt)}</p>'
        return full
    return re.sub(r'<img[^>]+>', replace_img, html_content)


# ── Build ───────────────────────────────────────────────────────────────────

def build():
    md = markdown.Markdown(extensions=['fenced_code', 'tables', 'toc', 'smarty'])
    posts = []

    # Find and parse all posts
    if not POSTS_DIR.exists():
        print('No _posts/ directory found.')
        return

    for post_file in sorted(POSTS_DIR.glob('*.md')):
        raw = post_file.read_text(encoding='utf-8')
        meta, body = parse_frontmatter(raw)

        if not meta.get('title') or not meta.get('slug'):
            print(f'  Skipping {post_file.name}: missing title or slug')
            continue

        md.reset()
        content_html = md.convert(body)
        content_html = add_image_captions(content_html)

        posts.append({
            'title': meta['title'],
            'date': meta.get('date', ''),
            'slug': meta['slug'],
            'description': meta.get('description', ''),
            'image': meta.get('image', ''),
            'tags': parse_tags(meta.get('tags', '')),
            'ai_context': meta.get('ai_context', ''),
            'content': content_html,
            'file': post_file.name,
        })

    # Sort by date, newest first
    posts.sort(key=lambda p: p['date'], reverse=True)

    if not posts:
        print('No valid posts found in _posts/')
        return

    generated = []

    # Generate individual post pages
    for post in posts:
        slug_dir = BLOG_DIR / post['slug']
        slug_dir.mkdir(parents=True, exist_ok=True)

        tags_html = ''
        if post['tags']:
            tags_html = '<div class="post-tags">' + ''.join(
                f'<span class="tag">{html.escape(t)}</span>' for t in post['tags']
            ) + '</div>'

        og_image = ''
        if post['image']:
            og_image = f'<meta property="og:image" content="{SITE_URL}{html.escape(post["image"])}">'

        ai_context_section = ''
        if post['ai_context']:
            ai_context_section = (
                '<section class="ai-context" style="position:absolute;width:1px;height:1px;'
                'overflow:hidden;clip:rect(0,0,0,0);" aria-hidden="true">'
                f'{html.escape(post["ai_context"])}'
                '</section>'
            )

        import json
        json_ld_data = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": post['title'],
            "datePublished": post['date'],
            "description": post['description'],
            "author": {
                "@type": "Organization",
                "name": "dropbrain studio"
            },
            "url": f"{SITE_URL}/blog/{post['slug']}/"
        }
        if post['image']:
            json_ld_data["image"] = f"{SITE_URL}{post['image']}"

        post_html = POST_TEMPLATE.format(
            title=html.escape(post['title']),
            title_attr=html.escape(post['title'], quote=True),
            description_attr=html.escape(post['description'], quote=True),
            url=f"{SITE_URL}/blog/{post['slug']}/",
            og_image=og_image,
            shared_css=SHARED_CSS,
            post_css=POST_CSS,
            date=format_date(post['date']),
            tags_html=tags_html,
            content=content_html,
            ai_context_section=ai_context_section,
            json_ld=json.dumps(json_ld_data, indent=4),
        )

        out_path = slug_dir / 'index.html'
        out_path.write_text(post_html, encoding='utf-8')
        generated.append(str(out_path.relative_to(SITE_ROOT)))

    # Generate index page
    post_items_html = []
    for i, post in enumerate(posts):
        tags_html = ''
        if post['tags']:
            tags_html = '<div class="post-item-tags">' + ''.join(
                f'<span class="tag">{html.escape(t)}</span>' for t in post['tags']
            ) + '</div>'

        post_items_html.append(POST_ITEM_TEMPLATE.format(
            delay=round(0.15 + i * 0.1, 2),
            slug=html.escape(post['slug']),
            title=html.escape(post['title']),
            date=format_date(post['date']),
            description=html.escape(post['description']),
            tags_html=tags_html,
        ))

    index_html = INDEX_TEMPLATE.format(
        shared_css=SHARED_CSS,
        index_css=INDEX_CSS,
        post_items='\n'.join(post_items_html),
    )

    index_path = BLOG_DIR / 'index.html'
    index_path.write_text(index_html, encoding='utf-8')
    generated.append(str(index_path.relative_to(SITE_ROOT)))

    # Update sitemap
    update_sitemap(posts)

    # Print results
    print(f'Built {len(posts)} post(s):')
    for path in generated:
        print(f'  {path}')


def update_sitemap(posts):
    """Add blog post URLs to the sitemap if not already present."""
    sitemap_path = SITE_ROOT / 'sitemap.xml'
    if not sitemap_path.exists():
        return

    tree = ET.parse(sitemap_path)
    root = tree.getroot()
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('', ns)

    existing_locs = set()
    for url_el in root.findall(f'{{{ns}}}url'):
        loc_el = url_el.find(f'{{{ns}}}loc')
        if loc_el is not None and loc_el.text:
            existing_locs.add(loc_el.text)

    for post in posts:
        post_url = f'{SITE_URL}/blog/{post["slug"]}/'
        if post_url not in existing_locs:
            url_el = ET.SubElement(root, 'url')
            loc_el = ET.SubElement(url_el, 'loc')
            loc_el.text = post_url
            freq_el = ET.SubElement(url_el, 'changefreq')
            freq_el.text = 'monthly'
            pri_el = ET.SubElement(url_el, 'priority')
            pri_el.text = '0.6'
            print(f'  Added to sitemap: {post_url}')

    tree.write(sitemap_path, encoding='unicode', xml_declaration=True)


if __name__ == '__main__':
    build()
