#!/usr/bin/env python3
"""Đóng gói blog: posts/ + site.json → _site/. GitHub Actions chạy sau mỗi lần push và mỗi sáng (đưa lên bài hẹn ngày).

Bài: posts/<slug>.html (một file HTML đầy đủ) hoặc posts/<slug>/index.html (kèm file js/css/ảnh).
Ngày đăng: site.json → posts.<slug>.date, không có thì <meta name="date" content="YYYY-MM-DD"> trong bài.
  không có ngày = nháp · ngày tương lai = hẹn ngày · hôm nay trở về trước = đăng.
Link video: site.json → posts.<slug>.youtube / tiktok / facebook, điền vào <div class="phone" ...> của bài.
Chạy thử: python3 scripts/build.py && python3 -m http.server -d _site 8000
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS, OUT = ROOT / "posts", ROOT / "_site"
LINKS = ("youtube", "tiktok", "facebook")
PHONE = re.compile(r'<(div|figure) class="phone"([^>]*)>')
esc = html.escape

CSS = """
:root{--paper:#F6F3EC;--ink:#12173A;--ink-soft:#4A5078;--ink-faint:#8A8FAE;--rule:rgba(18,23,58,.12);--marker:#FFD84A;
--marker-ink:#8A6A00;--pending-soft:rgba(255,216,74,.30);--truth:#148A5C;--truth-soft:rgba(20,138,92,.11);
--font:"Be Vietnam Pro",system-ui,-apple-system,"Segoe UI",sans-serif;--mono:"JetBrains Mono",ui-monospace,Menlo,monospace}
@media (prefers-color-scheme:dark){:root{--paper:#0A0F2C;--ink:#F3EFE8;--ink-soft:#A7AFD3;--ink-faint:#6E77A3;
--rule:rgba(210,220,255,.14);--marker-ink:#FFD84A;--pending-soft:rgba(255,216,74,.17);--truth:#3DDC97;--truth-soft:rgba(61,220,151,.13)}}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--font);font-size:18px;line-height:1.65}
a{color:inherit}
:focus-visible{outline:3px solid var(--marker);outline-offset:3px;border-radius:6px}
.wrap{max-width:860px;margin:0 auto;padding:0 20px}
.top{border-bottom:1px solid var(--rule)}
.top .wrap{display:flex;align-items:center;height:58px}
.brand{display:flex;align-items:center;gap:9px;font-weight:800;font-size:15px;text-decoration:none}
.brand .dot{width:11px;height:11px;border-radius:50%;background:var(--marker);box-shadow:0 0 0 4px var(--pending-soft)}
.intro{padding:64px 0 40px}
.intro h1{font-size:clamp(36px,1.4rem + 3vw,58px);line-height:1.07;letter-spacing:-.027em;margin:0 0 18px;max-width:13em}
.intro p{color:var(--ink-soft);font-size:19px;max-width:34em;margin:0}
.posts{list-style:none;margin:0;padding:0;border-top:3px solid var(--ink)}
.posts li{border-bottom:1px solid var(--rule)}
.posts a{display:grid;grid-template-columns:112px minmax(0,1fr);gap:6px 24px;padding:24px 0;text-decoration:none}
.posts time{font-family:var(--mono);font-size:13px;color:var(--ink-faint);padding-top:6px}
.posts h2{font-size:23px;line-height:1.3;letter-spacing:-.012em;margin:0 0 8px}
.posts h2 span{background:linear-gradient(var(--marker),var(--marker)) 0 100%/0 3px no-repeat;transition:background-size .25s ease}
.posts a:hover h2 span,.posts a:focus-visible h2 span{background-size:100% 3px}
.posts p{margin:0 0 10px;color:var(--ink-soft);font-size:16px;line-height:1.55}
.chips{display:flex;gap:8px;flex-wrap:wrap}
.chip{font-family:var(--mono);font-size:12px;font-weight:600;padding:1px 8px;border-radius:6px;background:var(--pending-soft);color:var(--marker-ink)}
.chip.v{background:var(--truth-soft);color:var(--truth)}
.empty{padding:40px 0;color:var(--ink-soft)}
footer{margin-top:56px;padding:24px 0 44px;border-top:1px solid var(--rule);font-size:14px;color:var(--ink-faint)}
@media (max-width:640px){.posts a{grid-template-columns:1fr;padding:20px 0}.posts time{padding-top:0}.intro{padding:40px 0 28px}}
@media (prefers-reduced-motion:reduce){.posts h2 span{transition:none}}
"""

PAGE = """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">{canonical}
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='%2312173A'/%3E%3Ccircle cx='16' cy='16' r='7' fill='%23FFD84A'/%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>{css}</style>
</head>
<body>
<header class="top"><div class="wrap"><a class="brand" href="{home}"><span class="dot" aria-hidden="true"></span>{name}</a></div></header>
<main class="wrap">
{main}
</main>
<footer><div class="wrap">{footer}</div></footer>
</body>
</html>
"""


def site_url(site: dict) -> str:
    """site.json url; trống thì suy từ repo đang chạy Actions: <user>.github.io hoặc <user>.github.io/<repo>."""
    if site.get("url"):
        return site["url"].rstrip("/")
    owner, _, repo = os.environ.get("GITHUB_REPOSITORY", "").partition("/")
    if not repo:
        return ""
    base = f"https://{owner.lower()}.github.io"
    return base if repo.lower() == f"{owner.lower()}.github.io" else f"{base}/{repo}"


def find_posts() -> list[tuple[str, Path]]:
    found = [(p.stem, p) for p in POSTS.glob("*.html")] + [(p.parent.name, p) for p in POSTS.glob("*/index.html")]
    for slug, _ in found:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
            raise SystemExit(f'posts/{slug}: tên bài chỉ dùng chữ thường không dấu, số, gạch ngang')
    return found


def meta(doc: str, name: str) -> str:
    m = re.search(rf'<meta\s+name="{name}"\s+content="([^"]*)"', doc, re.I)
    return html.unescape(m.group(1)).strip() if m else ""


def with_links(doc: str, links: dict) -> str:
    m = PHONE.search(doc)
    if not m or not any(links.get(k) for k in LINKS):
        return doc
    rest = re.sub(r'\s*data-(?:youtube|tiktok|facebook)="[^"]*"', "", m.group(2))
    attrs = "".join(f' data-{k}="{esc(links.get(k, ""), quote=True)}"' for k in LINKS)
    return f'{doc[:m.start()]}<{m.group(1)} class="phone"{attrs}{rest}>{doc[m.end():]}'


def build_post(slug: str, path: Path, info: dict, today: str) -> dict | None:
    doc = path.read_text(encoding="utf-8")
    day = info.get("date") or meta(doc, "date")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day or ""):
        print(f"  · nháp (chưa có ngày đăng): {slug}")
        return None
    if day > today:
        print(f"  · hẹn ngày {day}: {slug}")
        return None
    folder = path.name == "index.html"
    if folder:
        shutil.copytree(path.parent, OUT / slug)
    doc = re.sub(r'<video src="\.\./videos/[^"]*"[^>]*>\s*</video>', "", with_links(doc, info))
    (OUT / slug / "index.html" if folder else OUT / f"{slug}.html").write_text(doc, encoding="utf-8")
    t = re.search(r"<title>(.*?)</title>", doc, re.S | re.I)
    title, _, group = (html.unescape(t.group(1)).strip() if t else slug).partition(" · ")
    video = bool(re.search(r'data-youtube="https?://|youtube(?:-nocookie)?\.com/embed/[\w-]{11}', doc))
    return {"href": f"{slug}/" if folder else f"{slug}.html", "title": title, "group": group, "date": day,
            "description": meta(doc, "description"), "video": video}


def row(p: dict) -> str:
    y, m, d = p["date"].split("-")
    chips = (f'<span class="chip">{esc(p["group"])}</span>' if p["group"] else "") + \
            ('<span class="chip v">▶ có video</span>' if p["video"] else "")
    desc = f'<p>{esc(p["description"])}</p>' if p["description"] else ""
    return (f'<li><a href="{esc(p["href"])}"><time datetime="{p["date"]}">{d}/{m}/{y}</time>'
            f'<div><h2><span>{esc(p["title"])}</span></h2>{desc}<div class="chips">{chips}</div></div></a></li>')


def page(site: dict, title: str, main: str, home: str = "./", canonical: str = "") -> str:
    link = f'\n<link rel="canonical" href="{esc(canonical)}">' if canonical else ""
    return PAGE.format(title=esc(title), description=esc(site["intro"]), canonical=link, css=CSS, home=esc(home),
                       name=esc(site["name"]), main=main, footer=esc(site.get("footer", "")))


def main() -> None:
    site = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
    today = date.today().isoformat()
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir()
    posts = [p for slug, path in find_posts() if (p := build_post(slug, path, site.get("posts", {}).get(slug, {}), today))]
    posts.sort(key=lambda p: (p["date"], p["title"]), reverse=True)
    base = site_url(site)
    rows = "\n".join(row(p) for p in posts) or '<li class="empty">Chưa có bài nào.</li>'
    intro = f'<section class="intro"><h1>{esc(site["headline"])}</h1><p>{esc(site["intro"])}</p></section>'
    (OUT / "index.html").write_text(page(site, site["name"], f'{intro}\n<ol class="posts">\n{rows}\n</ol>',
                                         canonical=f"{base}/" if base else ""), encoding="utf-8")
    home = f"{base}/" if base else "/"  # trang 404 hiện ở mọi đường dẫn nên cần link tuyệt đối
    (OUT / "404.html").write_text(page(site, "Không tìm thấy trang", '<section class="intro"><h1>Không có trang này.</h1>'
                                       f'<p><a href="{esc(home)}">Về trang chủ →</a></p></section>', home), encoding="utf-8")
    robots = "User-agent: *\nAllow: /\n"
    if base:
        locs = "".join(f"  <url><loc>{base}/{esc(re.sub(r'[.]html$', '', p['href']))}</loc></url>\n" for p in posts)
        (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/'
                                         f'schemas/sitemap/0.9">\n  <url><loc>{base}/</loc></url>\n{locs}</urlset>\n', encoding="utf-8")
        robots += f"Sitemap: {base}/sitemap.xml\n"
    (OUT / "robots.txt").write_text(robots, encoding="utf-8")
    print(f"→ _site: trang chủ + {len(posts)} bài · {base or '(chưa biết địa chỉ)'}")


if __name__ == "__main__":
    main()
