#!/usr/bin/env python3
"""Regenerate the portfolio from _portfolio/projects.json.

- index.html: the 3 newest projects, between the PROJECTS:START/END markers,
  plus a link to the full portfolio.
- portfolio.html: every project, built from index.html's head, nav, contact
  section and footer so it always matches the homepage styling.
- sitemap.xml: lists both pages.

Projects are listed newest first in projects.json. Run from anywhere:
    python3 _portfolio/build.py
"""
import datetime
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://sussexleadcraftltd.com"
HOME_LIMIT = 3
START = "<!-- PROJECTS:START"
END = "<!-- PROJECTS:END -->"

e = lambda s: html.escape(s, quote=True)


def feature(p, heading="h3"):
    ph = p["photos"]
    main = ph[0]
    thumbs = "\n".join(
        f'          <a href="{e(x["file"])}"><img src="{e(x["thumb"])}" width="{x["tw"]}" height="{x["th"]}" loading="lazy" alt="{e(x["alt"])}"></a>'
        for x in ph[1:]
    )
    specs = "\n".join(f"          <li>{e(s)}</li>" for s in p.get("specs", []))
    desc = f'\n        <p class="pf-desc">{e(p["description"])}</p>' if p.get("description") else ""
    return f'''    <article class="project-feature" id="project-{e(p["id"])}">
      <div class="pf-gallery">
        <a class="pf-main" href="{e(main["file"])}"><img src="{e(main["file"])}" width="{main["w"]}" height="{main["h"]}" alt="{e(main["alt"])}"></a>
        <div class="pf-thumbs">
{thumbs}
        </div>
      </div>
      <div class="pf-info">
        <p class="portfolio-type">{e(p["category"])}</p>
        <{heading} class="pf-title">{e(p["title"])}</{heading}>
        <p class="portfolio-meta">{e(p["summary"])}</p>{desc}
        <ul class="pf-spec">
{specs}
        </ul>
      </div>
    </article>'''


def row(p):
    return (f'    <div class="project-row" id="project-{e(p["id"])}"><p class="portfolio-proj">{e(p["title"])}</p>'
            f'<p class="portfolio-meta">{e(p["summary"])}</p><p class="portfolio-type">{e(p["category"])}</p></div>')


def render(projects, heading="h3"):
    feats = [feature(p, heading) for p in projects if p["photos"]]
    rows = [row(p) for p in projects if not p["photos"]]
    out = []
    if feats:
        out.append('  <div class="project-features">\n' + "\n".join(feats) + "\n  </div>")
    if rows:
        out.append('  <div class="project-list">\n' + "\n".join(rows) + "\n  </div>")
    return "\n".join(out)


def replace_region(doc, body):
    i = doc.index(START)
    i = doc.index("-->", i) + 3
    j = doc.index(END)
    return doc[:i] + "\n" + body + "\n" + doc[j:]


def main():
    projects = json.load(open(os.path.join(ROOT, "_portfolio", "projects.json")))["projects"]
    projects.sort(key=lambda p: p["added"], reverse=True)
    for p in projects:
        assert re.fullmatch(r"[a-z0-9-]+", p["id"]), p["id"]
        for x in p["photos"]:
            for k in ("file", "thumb"):
                assert os.path.isfile(os.path.join(ROOT, x[k])), x[k]

    # ---- homepage
    idx_path = os.path.join(ROOT, "index.html")
    idx = open(idx_path).read()
    home = render(projects[:HOME_LIMIT])
    n = len(projects)
    home += (f'\n  <p class="pf-all-wrap"><a href="portfolio.html" class="hero-navlink">View full portfolio ({n} project{"s" if n != 1 else ""}) '
             '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 8h10M9 4l4 4-4 4"/></svg></a></p>')
    idx = replace_region(idx, home)
    open(idx_path, "w").write(idx)

    # ---- portfolio page, assembled from the homepage
    head_end = idx.index("<section class=\"hero\"")
    head = idx[:head_end]
    head = re.sub(r"<title>.*?</title>", "<title>Portfolio | Sussex Leadcraft Ltd</title>", head, count=1)
    desc = "Completed leadwork projects by Sussex Leadcraft Ltd: heritage, civic, listed building and new build lead roofing across London, the South East and South West."
    head = re.sub(r'(<meta name="description" content=")[^"]*', r"\g<1>" + desc, head, count=1)
    head = re.sub(r'(<meta property="og:description" content=")[^"]*', r"\g<1>" + desc, head, count=1)
    head = re.sub(r'(<meta property="og:title" content=")[^"]*', r"\g<1>Portfolio | Sussex Leadcraft Ltd", head, count=1)
    head = head.replace(f'<link rel="canonical" href="{SITE}/">', f'<link rel="canonical" href="{SITE}/portfolio.html">')
    head = head.replace(f'<meta property="og:url" content="{SITE}/">', f'<meta property="og:url" content="{SITE}/portfolio.html">')
    head = re.sub(r'<script type="application/ld\+json">.*?</script>\n?', "", head, count=1, flags=re.S)

    contact_start = idx.index('<section id="contact">')
    tail = idx[contact_start:]

    def fix_links(s):
        s = s.replace('href="#" class="logo-link"', 'href="./" class="logo-link"')
        return re.sub(r'href="#(about|services|accreditation)"', r'href="./#\1"', s)

    head, tail = fix_links(head), fix_links(tail)
    body = f'''<section id="portfolio" class="portfolio-page"><div class="container">
  <div class="portfolio-header">
    <div><p class="eyebrow">Portfolio</p><h1 class="pf-page-title">All projects</h1></div>
    <p class="portfolio-note">Every project we have published, newest first. Contact us to discuss specific project types or sector experience.</p>
  </div>
{render(projects, "h2")}
</div></section>
<hr class="divider">
'''
    open(os.path.join(ROOT, "portfolio.html"), "w").write(head + body + tail)

    # ---- sitemap
    today = datetime.date.today().isoformat()
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{SITE}/</loc><lastmod>{today}</lastmod></url>\n"
        f"  <url><loc>{SITE}/portfolio.html</loc><lastmod>{today}</lastmod></url>\n</urlset>\n")
    print(f"Built: {min(n, HOME_LIMIT)} on homepage, {n} on portfolio.html")


if __name__ == "__main__":
    main()
