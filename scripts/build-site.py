#!/usr/bin/env python3
"""Build site/ from docs/ - a static HTML handbook with sidebar.

No dependencies, no network: plain Python stdlib. Run from repo root:
    python3 scripts/build-site.py
Output lands in site/ (index.html, one page per docs chapter).
"""

from __future__ import annotations

import html
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, "docs")
SITE = os.path.join(ROOT, "site")

# ---------------------------------------------------------------------------
# Minimal markdown -> HTML (headings, lists, tables, code, emphasis, links)
# ---------------------------------------------------------------------------

def inline(md: str) -> str:
    text = html.escape(md, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text
    )
    return text


def markdown_to_html(md: str) -> str:
    lines = md.splitlines()
    out: list[str] = []
    in_code = False
    para: list[str] = []
    list_type: str | None = None
    table_rows: list[list[str]] = []

    def close_para() -> None:
        if para:
            out.append(f"<p>{inline(' '.join(para))}</p>")
            para.clear()

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            out.append(f"</{list_type}>")
            list_type = None

    def close_table() -> None:
        nonlocal table_rows
        if table_rows:
            head, *body = table_rows
            out.append("<table><thead><tr>"
                       + "".join(f"<th>{inline(c)}</th>" for c in head)
                       + "</tr></thead>")
            if body:
                out.append("<tbody><tr>"
                           + "".join(f"<td>{inline(c)}</td>" for c in body[0])
                           + "</tr>")
                for row in body[1:]:
                    out.append("<tr>"
                               + "".join(f"<td>{inline(c)}</td>" for row2 in [row] for c in row2)
                               + "</tr>")
                out.append("</tbody>")
            out.append("</table>")
            table_rows = []

    i = 0
    while i < len(lines):
        line = lines[i]
        fence = re.match(r"^```(\w*)\s*$", line)
        if fence and not in_code:
            close_para(); close_list(); close_table()
            in_code = True
            out.append(f"<pre><code class=\"lang-{fence.group(1) or 'text'}\">")
        elif in_code:
            if fence:
                out.append("</code></pre>")
                in_code = False
            else:
                out.append(html.escape(line))
        elif line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:-|]+\|$", lines[i + 1]):
            close_para(); close_list()
            cells = [c.strip() for c in line.strip("|").split("|")]
            table_rows.append(cells)
        elif re.match(r"^\|[\s:|-]+\|$", line):
            pass  # table separator row
        elif line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            table_rows.append(cells)
        elif line.startswith("### "):
            close_para(); close_list(); close_table()
            out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            close_para(); close_list(); close_table()
            out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("# "):
            close_para(); close_list(); close_table()
            out.append(f"<h1>{inline(line[2:])}</h1>")
        elif re.match(r"^\s*[-*] ", line):
            close_para(); close_table()
            if list_type != "ul":
                close_list()
                out.append("<ul>")
                list_type = "ul"
            out.append(f"<li>{inline(re.sub(r'^\s*[-*] ', '', line))}</li>")
        elif re.match(r"^\s*\d+\. ", line):
            close_para(); close_table()
            if list_type != "ol":
                close_list()
                out.append("<ol>")
                list_type = "ol"
            out.append(f"<li>{inline(re.sub(r'^\s*\d+\. ', '', line))}</li>")
        elif line.strip() == "":
            close_para(); close_list(); close_table()
        elif list_type and out and out[-1].startswith("<li>"):
            # continuation line belonging to the previous list item
            out[-1] = out[-1].replace("</li>", f" {inline(line.strip())}</li>")
        elif list_type or True:
            close_list()
            para.append(line.strip())
        i += 1

    if in_code:
        out.append("</code></pre>")
    close_para(); close_list(); close_table()
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Site assembly
# ---------------------------------------------------------------------------

def first_heading(md: str, fallback: str) -> tuple[str, str]:
    for line in md.splitlines():
        if line.startswith("# "):
            return line[2:].strip(), fallback
    return fallback, fallback


def slug(name: str) -> str:
    return re.sub(r"\.md$", "", name) + ".html"


def build() -> int:
    os.makedirs(SITE, exist_ok=True)
    chapters = sorted(f for f in os.listdir(DOCS) if f.endswith(".md"))
    pages: list[dict] = []
    for name in chapters:
        with open(os.path.join(DOCS, name), "r", encoding="utf-8") as fh:
            md = fh.read()
        title, _ = first_heading(md, name)
        pages.append({
            "file": name,
            "slug": slug(name),
            "title": title,
            "body": markdown_to_html(md),
        })

    for page in pages:
        nav_items = "\n".join(
            f'<li><a href="{p["slug"]}" class="{"active" if p is page else ""}">{html.escape(p["title"])}</a></li>'
            for p in pages
        )
        nav_extra = (
            '<li class="nav-section">Project</li>'
            '<li><a href="../README.md">README</a></li>'
            '<li><a href="https://ollama.com" rel="noopener">Ollama (external)</a></li>'
        )
        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(page["title"])} - RAG Your Docs Handbook</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="layout">
<aside class="sidebar">
  <div class="brand">RAG Your<br>Docs Handbook</div>
  <nav><ul>
{nav_items}
{nav_extra}
  </ul></nav>
  <p class="foot">Local-first. No secrets.<br>
  &copy; 2026 Asdale Dynamics, LLC</p>
</aside>
<main>
{page["body"]}
</main>
</div>
</body>
</html>
"""
        with open(os.path.join(SITE, page["slug"]), "w", encoding="utf-8") as fh:
            fh.write(html_doc)

    chapter_links = "\n".join(
        f'<li><a href="{p["slug"]}">{html.escape(p["title"])}</a></li>'
        for p in pages
    )
    landing = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RAG Your Docs Handbook</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="layout">
<aside class="sidebar">
  <div class="brand">RAG Your<br>Docs Handbook</div>
  <p class="foot">Local-first. No secrets.<br>
  &copy; 2026 Asdale Dynamics, LLC</p>
</aside>
<main>
<h1>Chat with your own files - in plain English</h1>
<p>A friendly, step-by-step manual for building a <strong>local-first
retrieval assistant</strong>: chunking, embeddings, vector stores, local
models (Ollama/llama.cpp), and citation sanity checks. Your files never
leave your machine.</p>
<h2>Start here</h2>
<ul>
<li>Read the 8 chapters in the sidebar.</li>
<li>Run the pipeline: <code>python3 examples/01-index.py docs --index /tmp/opencode/idx.json</code></li>
<li>Ask it something: <code>python3 examples/02-ask.py /tmp/opencode/idx.json "How much overlap?"</code></li>
<li>Check yourself: <code>python3 examples/03-tests.py --index /tmp/opencode/idx.json --run-suite</code></li>
</ul>
<h2>Chapters</h2>
<ul>
{chapter_links}
</ul>
</main>
</div>
</body>
</html>
"""
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(landing)

    shutil.copy(os.path.join(ROOT, "site-src", "style.css"),
                os.path.join(SITE, "style.css"))
    print(f"built {len(pages)} pages into site/: {[p['slug'] for p in pages]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(build())
