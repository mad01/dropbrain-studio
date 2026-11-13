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
from collections import Counter
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

/* Neutral palette (light default + dark) lives in /assets/theme.css */

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
    background: #282c34;
    padding: 16px 18px;
}

.post-content pre code {
    background: none;
    border: none;
    border-radius: 0;
    padding: 0;
    font-size: 0.85rem;
    line-height: 1.6;
    color: #abb2bf; /* atom-one-dark foreground — code blocks stay dark in both themes */
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
    <script>try{{if(localStorage.getItem('db-theme')==='dark')document.documentElement.setAttribute('data-theme','dark')}}catch(e){{}}</script>
    <link rel="stylesheet" href="/assets/theme.css">
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
    <script defer src="/assets/theme.js"></script>
</body>
</html>
"""

# ── Index page ──────────────────────────────────────────────────────────────
# Top: a "Latest" lead (one main card, LEAD_LEFT + LEAD_RIGHT side cards).
# Only the main card shows a post's `image`; side cards stay text so the
# columns keep an even height.
# Below: every post as a compact row, with tag filter, sort, search and
# "See more" (INDEX_JS). Without JS, all rows show and the controls stay hidden.

LEAD_LEFT = 2
LEAD_RIGHT = 2
MIN_TAG_POSTS = 2      # tags used by fewer posts stay out of the filter menu
ROW_TAGS_SHOWN = 2

INDEX_CSS = """\
[hidden] { display: none !important; }

.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
}

.page {
    max-width: 1160px;
    --chip: color-mix(in srgb, var(--border) 70%, var(--surface));
    --mono: 'SF Mono', SFMono-Regular, ui-monospace, 'Menlo', monospace;
}

/* ── Latest ── */

.lead-bar {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 16px;
    margin-top: 40px;
    padding: 16px 0;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    animation: fadeUp 0.6s ease 0.05s both;
}

.lead-bar h1 {
    font-size: 0.95rem;
    font-weight: 650;
    letter-spacing: -0.01em;
}

.lead-bar a {
    font-size: 0.88rem;
    color: var(--text-muted);
}

.lead {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1.85fr) minmax(0, 1fr);
    grid-template-areas: "left main right";
    gap: 40px;
    padding-top: 32px;
}

.lead-left { grid-area: left; }
.lead-right { grid-area: right; }

.lead-col .card + .card {
    margin-top: 28px;
    padding-top: 28px;
    border-top: 1px solid var(--border);
}

.card {
    position: relative;
    animation: fadeUp 0.55s ease both;
}

.card-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 4px 14px;
    margin-bottom: 12px;
    font-size: 0.82rem;
    color: var(--text-muted);
}

.card-meta .meta-tag { color: var(--text-secondary); }

.card-title {
    font-size: 1.28rem;
    font-weight: 650;
    line-height: 1.22;
    letter-spacing: -0.02em;
    margin-bottom: 10px;
    text-wrap: balance;
}

.card-title a { color: var(--text); }

/* The whole card is the link target. */
.card-title a::after {
    content: '';
    position: absolute;
    inset: 0;
}

.card:hover .card-title a { color: var(--text-secondary); }

.card-desc {
    font-size: 0.95rem;
    line-height: 1.6;
    color: var(--text-secondary);
    display: -webkit-box;
    -webkit-line-clamp: 4;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.card-image {
    display: block;
    width: 100%;
    aspect-ratio: 16 / 10;
    object-fit: cover;
    border: 1px solid var(--border);
    border-radius: 10px;
    margin-bottom: 18px;
}

.card-main {
    grid-area: main;
    display: flex;
    flex-direction: column;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 36px 40px 40px;
    transition: border-color 0.2s ease;
}

.card-main .card-body {
    display: flex;
    flex-direction: column;
    flex: 1;
}

.card-main:hover { border-color: var(--border-hover); }
.card-main:hover .card-title a { color: var(--text); }

.card-main .card-title {
    font-size: clamp(2rem, 3.4vw, 3rem);
    line-height: 1.08;
    letter-spacing: -0.035em;
    margin-bottom: 18px;
}

.card-main .card-desc {
    font-size: 1.12rem;
    max-width: 40em;
    margin-bottom: 32px;
    -webkit-line-clamp: 5;
}

.button {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font: inherit;
    font-size: 0.92rem;
    font-weight: 500;
    color: var(--text);
    background: var(--chip);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 9px 16px;
    cursor: pointer;
    transition: background 0.2s ease, border-color 0.2s ease;
}

.button svg {
    width: 15px;
    height: 15px;
    transition: transform 0.2s ease;
}

.card-main .button { margin-top: auto; align-self: flex-start; }
.card-main:hover .button,
.button:hover { background: var(--border); border-color: var(--border-hover); }
.card-main:hover .button svg { transform: translateX(3px); }
.see-more .button:hover svg { transform: translateY(2px); }

/* ── All posts ── */

.archive {
    margin-top: 104px;
    padding-bottom: 72px;
    scroll-margin-top: 24px;
}

.archive-title {
    font-size: clamp(2.4rem, 5.2vw, 3.8rem);
    font-weight: 650;
    line-height: 1;
    letter-spacing: -0.045em;
}

.archive-count {
    margin-top: 36px;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--border);
    font-size: 0.88rem;
    color: var(--text-muted);
    font-variant-numeric: tabular-nums;
}

.controls {
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
    padding-top: 22px;
}

.controls-right {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
}

.control {
    position: relative;
    display: inline-flex;
    align-items: center;
}

.control select,
.control input {
    -webkit-appearance: none;
    appearance: none;
    height: 40px;
    padding: 0 38px 0 14px;
    font: inherit;
    font-size: 0.9rem;
    color: var(--text);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    transition: border-color 0.2s ease;
}

.control select { cursor: pointer; }
.control input { width: 260px; }
.control input::placeholder { color: var(--text-muted); }
.control input::-webkit-search-cancel-button { -webkit-appearance: none; }

.control select:hover,
.control input:hover { border-color: var(--border-hover); }

.control select:focus-visible,
.control input:focus-visible,
.button:focus-visible,
.row:focus-visible {
    outline: 2px solid var(--text-secondary);
    outline-offset: 2px;
}

.control svg {
    position: absolute;
    right: 12px;
    width: 16px;
    height: 16px;
    color: var(--text-muted);
    pointer-events: none;
}

.table-head,
.row {
    display: grid;
    grid-template-columns: minmax(0, 1.45fr) minmax(0, 1.6fr) minmax(0, 0.8fr) 112px;
    gap: 28px;
    align-items: center;
}

.table-head {
    margin-top: 28px;
    padding: 0 14px 14px;
    border-bottom: 1px solid var(--border);
    font-family: var(--mono);
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
}

.row {
    padding: 20px 14px;
    border-bottom: 1px solid var(--border);
    font-size: 0.95rem;
    color: var(--text-secondary);
    transition: background 0.15s ease, box-shadow 0.15s ease;
}

.row:hover {
    color: var(--text-secondary);
    background: var(--surface);
    border-bottom-color: transparent;
    border-radius: 12px;
    box-shadow: 0 0 0 1px var(--border);
}

.cell {
    white-space: nowrap;
    overflow: hidden;
}

.cell-title,
.cell-desc,
.cell-tags {
    -webkit-mask-image: linear-gradient(to right, #000 calc(100% - 48px), transparent);
    mask-image: linear-gradient(to right, #000 calc(100% - 48px), transparent);
}

.cell-title {
    font-weight: 600;
    letter-spacing: -0.01em;
    color: var(--text);
}

.cell-date { font-variant-numeric: tabular-nums; }

.no-match {
    padding: 48px 14px;
    color: var(--text-muted);
}

.see-more {
    display: flex;
    justify-content: center;
    padding-top: 44px;
}

@media (max-width: 1020px) {
    .lead {
        grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
        grid-template-areas: "main main" "left right";
        gap: 40px 32px;
    }
}

@media (max-width: 900px) {
    .table-head,
    .row { grid-template-columns: minmax(0, 1.3fr) minmax(0, 1.5fr) 104px; }
    .cell-tags { display: none; }
}

@media (max-width: 640px) {
    .lead {
        grid-template-columns: minmax(0, 1fr);
        grid-template-areas: "main" "left" "right";
    }
    .lead-left,
    .lead-right {
        padding-top: 28px;
        border-top: 1px solid var(--border);
    }
    .card-main { padding: 26px 22px 28px; }
    .archive { margin-top: 72px; }
    .controls,
    .controls-right { flex-direction: column; align-items: stretch; }
    .control select,
    .control input { width: 100%; }
    .table-head { display: none; }
    .row {
        grid-template-columns: minmax(0, 1fr);
        gap: 4px;
        padding: 16px 6px;
    }
    .cell-desc { display: none; }
    .cell-title {
        white-space: normal;
        -webkit-mask-image: none;
        mask-image: none;
    }
    .cell-date { font-size: 0.82rem; color: var(--text-muted); }
}

@media (prefers-reduced-motion: reduce) {
    .lead-bar,
    .card { animation: none; }
}
"""

INDEX_JS = """\
(function () {
    var PAGE_SIZE = 12;
    var list = document.getElementById('post-rows');
    var controls = document.getElementById('post-controls');
    if (!list || !controls) return;

    var rows = Array.prototype.slice.call(list.querySelectorAll('.row'));
    var tagSelect = document.getElementById('filter-tag');
    var sortSelect = document.getElementById('filter-sort');
    var search = document.getElementById('filter-search');
    var more = document.getElementById('see-more');
    var noMatch = document.getElementById('no-match');
    var count = document.getElementById('post-count');
    var limit = PAGE_SIZE;

    function matches(row, tag, query) {
        if (tag && row.dataset.tags.split('|').indexOf(tag) === -1) return false;
        return !query || row.dataset.search.indexOf(query) !== -1;
    }

    function render() {
        var tag = tagSelect.value;
        var query = search.value.trim().toLowerCase();
        var dir = sortSelect.value === 'oldest' ? 1 : -1;
        rows.sort(function (a, b) {
            if (a.dataset.date === b.dataset.date) return 0;
            return a.dataset.date < b.dataset.date ? -dir : dir;
        });
        var total = 0;
        rows.forEach(function (row) {
            list.appendChild(row);
            var ok = matches(row, tag, query);
            if (ok) total += 1;
            row.hidden = !ok || total > limit;
        });
        count.textContent = total + (total === 1 ? ' post' : ' posts');
        noMatch.hidden = total > 0;
        more.hidden = total <= limit;
    }

    function restart() {
        limit = PAGE_SIZE;
        render();
    }

    tagSelect.addEventListener('change', restart);
    sortSelect.addEventListener('change', restart);
    search.addEventListener('input', restart);
    more.querySelector('button').addEventListener('click', function () {
        limit += PAGE_SIZE;
        render();
    });

    controls.hidden = false;
    render();
})();
"""

ICON_ATTRS = 'viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"'
ICON_CHEVRON = f'<svg {ICON_ATTRS}><path d="M4 6l4 4 4-4"/></svg>'
ICON_SEARCH = f'<svg {ICON_ATTRS}><circle cx="7" cy="7" r="4.5"/><path d="M10.5 10.5L14 14"/></svg>'
ICON_ARROW_RIGHT = f'<svg {ICON_ATTRS}><path d="M3 8h10M9 4l4 4-4 4"/></svg>'
ICON_ARROW_DOWN = f'<svg {ICON_ATTRS}><path d="M8 3v10M4 9l4 4 4-4"/></svg>'

INDEX_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Blog — dropbrain studio</title>
    <meta name="description" content="Blog from dropbrain studio. App updates, developer tools, and engineering notes going back to 2015.">
    <meta property="og:title" content="Blog — dropbrain studio">
    <meta property="og:description" content="Blog from dropbrain studio. App updates, developer tools, and engineering notes going back to 2015.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://dropbrain.io/blog/">
    <script>try{{if(localStorage.getItem('db-theme')==='dark')document.documentElement.setAttribute('data-theme','dark')}}catch(e){{}}</script>
    <link rel="stylesheet" href="/assets/theme.css">
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

        <section aria-labelledby="latest-title">
            <div class="lead-bar">
                <h1 id="latest-title">Latest posts</h1>
                <a href="#all-posts">All {post_count} posts &darr;</a>
            </div>
            <div class="lead">
{lead_cards}
            </div>
        </section>

        <section class="archive" id="all-posts" aria-labelledby="archive-title">
            <h2 class="archive-title" id="archive-title">All posts</h2>
            <p class="archive-count" id="post-count" aria-live="polite">{post_count} posts</p>

            <div class="controls" id="post-controls" hidden>
                <label class="control">
                    <span class="sr-only">Filter by tag</span>
                    <select id="filter-tag">
                        <option value="">All tags</option>
{tag_options}
                    </select>
                    {icon_chevron}
                </label>
                <div class="controls-right">
                    <label class="control">
                        <span class="sr-only">Sort</span>
                        <select id="filter-sort">
                            <option value="newest">Newest first</option>
                            <option value="oldest">Oldest first</option>
                        </select>
                        {icon_chevron}
                    </label>
                    <label class="control">
                        <span class="sr-only">Search posts</span>
                        <input type="search" id="filter-search" placeholder="Search posts…" autocomplete="off">
                        {icon_search}
                    </label>
                </div>
            </div>

            <div class="table-head" aria-hidden="true">
                <span>Title</span><span>Description</span><span class="cell-tags">Tags</span><span>Date</span>
            </div>
            <div id="post-rows">
{post_rows}
            </div>
            <p class="no-match" id="no-match" hidden>No posts match. Try another tag or search.</p>
            <div class="see-more" id="see-more" hidden>
                <button type="button" class="button">See more {icon_arrow_down}</button>
            </div>
        </section>

        <footer>
            <a href="/">&larr; dropbrain.studio</a>
            <a href="/">Home</a>
        </footer>
    </div>
    <script>
{index_js}
    </script>
    <script defer src="/assets/theme.js"></script>
</body>
</html>
"""

CARD_TEMPLATE = """\
                <article class="card card-{kind}" style="animation-delay: {delay}s;">
                    {image_html}
                    <div class="card-body">
                        <div class="card-meta">{tag_html}<time datetime="{date_iso}">{date}</time></div>
                        <h2 class="card-title"><a href="/blog/{slug}/">{title}</a></h2>
                        <p class="card-desc">{description}</p>
                        {button_html}
                    </div>
                </article>"""

ROW_TEMPLATE = """\
                <a class="row" href="/blog/{slug}/" data-date="{date_iso}" data-tags="{tags_data}" data-search="{search}">
                    <span class="cell cell-title">{title}</span>
                    <span class="cell cell-desc">{description}</span>
                    <span class="cell cell-tags">{tags}</span>
                    <time class="cell cell-date" datetime="{date_iso}">{date}</time>
                </a>"""


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


def format_short_date(date_str):
    """Format a YYYY-MM-DD date as 'Nov 1, 2026' for compact lists."""
    try:
        d = datetime.strptime(date_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        return date_str or ''
    return f'{d:%b} {d.day}, {d.year}'


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


# ── Index rendering ────────────────────────────────────────────────────────

def render_card(post, kind, delay):
    """One card in the Latest lead. kind is 'main' or 'side'."""
    image_html = ''
    if kind == 'main' and post['image']:
        image_html = f'<img class="card-image" src="{html.escape(post["image"])}" alt="">'
    tag_html = ''
    if post['tags']:
        tag_html = f'<span class="meta-tag">{html.escape(post["tags"][0])}</span>'
    button_html = ''
    if kind == 'main':
        button_html = f'<span class="button" aria-hidden="true">Read more {ICON_ARROW_RIGHT}</span>'
    return CARD_TEMPLATE.format(
        kind=kind,
        delay=delay,
        image_html=image_html,
        tag_html=tag_html,
        date_iso=html.escape(post['date']),
        date=format_short_date(post['date']),
        slug=html.escape(post['slug']),
        title=html.escape(post['title']),
        description=html.escape(post['description']),
        button_html=button_html,
    )


def render_lead(posts):
    """Newest post as the main card, the next ones in the left and right columns."""
    left = posts[1:1 + LEAD_LEFT]
    right = posts[1 + LEAD_LEFT:1 + LEAD_LEFT + LEAD_RIGHT]
    parts = [render_card(posts[0], 'main', 0.1)]
    for name, group, start in (('left', left, 0.18), ('right', right, 0.26)):
        if group:
            cards = '\n'.join(render_card(p, 'side', round(start + i * 0.08, 2))
                              for i, p in enumerate(group))
            parts.append(f'                <div class="lead-col lead-{name}">\n{cards}\n                </div>')
    return '\n'.join(parts)


def render_row(post):
    """One compact row in the All posts list."""
    search = ' '.join([post['title'], post['description'], *post['tags']]).lower()
    return ROW_TEMPLATE.format(
        slug=html.escape(post['slug']),
        date_iso=html.escape(post['date']),
        tags_data=html.escape('|'.join(post['tags'])),
        search=html.escape(search),
        title=html.escape(post['title']),
        description=html.escape(post['description']),
        tags=html.escape(', '.join(post['tags'][:ROW_TAGS_SHOWN])),
        date=format_short_date(post['date']),
    )


def render_tag_options(posts):
    """Filter menu entries: tags on at least MIN_TAG_POSTS posts, most used first."""
    counts = Counter(t for p in posts for t in p['tags'])
    tags = sorted((t for t, n in counts.items() if n >= MIN_TAG_POSTS),
                  key=lambda t: (-counts[t], t))
    return '\n'.join(
        f'                        <option value="{html.escape(t)}">{html.escape(t)} ({counts[t]})</option>'
        for t in tags
    )


def write_index(posts):
    """Write blog/index.html and return its path relative to the site root."""
    index_html = INDEX_TEMPLATE.format(
        shared_css=SHARED_CSS,
        index_css=INDEX_CSS,
        index_js=INDEX_JS,
        post_count=len(posts),
        lead_cards=render_lead(posts),
        tag_options=render_tag_options(posts),
        post_rows='\n'.join(render_row(p) for p in posts),
        icon_chevron=ICON_CHEVRON,
        icon_search=ICON_SEARCH,
        icon_arrow_down=ICON_ARROW_DOWN,
    )
    index_path = BLOG_DIR / 'index.html'
    index_path.write_text(index_html, encoding='utf-8')
    return str(index_path.relative_to(SITE_ROOT))


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
            content=post['content'],
            ai_context_section=ai_context_section,
            json_ld=json.dumps(json_ld_data, indent=4),
        )

        out_path = slug_dir / 'index.html'
        out_path.write_text(post_html, encoding='utf-8')
        generated.append(str(out_path.relative_to(SITE_ROOT)))

    # Generate index page
    generated.append(write_index(posts))

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
