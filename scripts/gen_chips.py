#!/usr/bin/env python3
"""Tech-garden chips: one animated SVG per technology, a flower label per row,
and a "field guide" card per row that explains every chip. Icons come from
Simple Icons; the README block between the Tech Garden markers is rewritten.

    python3 scripts/gen_chips.py
"""
import hashlib
import html
import random
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "chips"
ICON_URL = "https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{}.svg"
FONT = "Segoe UI, Ubuntu, Helvetica, Arial, sans-serif"
CHIP_COLOURS = ["#D6762A", "#E8913F", "#F0A868", "#7FA36B"]  # cycles along each row
GREY = "#8b949e"

# (row label, petal colour, centre colour, chips)
# chip = (file slug, Simple Icons slug or None, label, description)
STACK = [
    ("AGENTS", "#7FA36B", "#5E8B4F", [
        ("langgraph", "langgraph", "LangGraph",
         "Graph-based agent orchestration with state and control flow. Used to build a LangGraph agent for a vinyl-record webshop."),
        ("crewai", "crewai", "CrewAI",
         "Multi-agent framework where role-based agents collaborate on a task. Compared against LangGraph on the same webshop use case."),
        ("claudecode", "claude", "Claude Code",
         "Agentic coding assistant in the terminal, used daily to plan, build and review features across my projects."),
        ("localllm", None, "Local LLMs",
         "Privacy-friendly, on-device language models: BlendSmart AI gives personalised nutrition advice without any data leaving the machine."),
    ]),
    ("FRONTEND", "#F0B484", "#D98828", [
        ("react", "react", "React",
         "Component-based UI library, used for the TripWise trip-planning, itinerary and budget app."),
        ("nextjs", "nextdotjs", "Next.js",
         "React framework with routing and server rendering, used for EduUpcycle (teacher and student portals) and the Kanosport website."),
        ("typescript", "typescript", "TypeScript",
         "JavaScript with static types: catches bugs at compile time and keeps larger frontends maintainable."),
        ("javascript", "javascript", "JavaScript",
         "The language of the web, used on both the client and server side of my Next.js projects."),
        ("tailwindcss", "tailwindcss", "Tailwind CSS",
         "Utility-first CSS framework for building consistent, responsive interfaces quickly without leaving the markup."),
        ("html5", "html5", "HTML / CSS",
         "The foundation of every web project, from static sites to fully designed landing pages."),
    ]),
    ("BACKEND", "#E8913F", "#C46A1F", [
        ("java", "openjdk", "Java",
         "Object-oriented, strongly typed language, used for the TripWise REST API."),
        ("springboot", "springboot", "Spring Boot",
         "Java framework for production-ready REST APIs: trips, budgets, bookings, expenses and authentication in TripWise."),
        ("csharp", "sharp", "C#",
         "Modern, typed language from Microsoft, used in two ASP.NET Core projects."),
        ("dotnet", "dotnet", "ASP.NET Core",
         "Web framework behind Retrogroove (a vinyl marketplace with Razor Pages) and a group Order Management System for Microsoft."),
        ("python", "python", "Python",
         "My go-to for AI, data and automation work: procurement agents, PDF extraction and LLM-powered apps."),
        ("kotlin", "kotlin", "Kotlin",
         "Modern language for Android: used for AppetIT, a self-service ordering system for restaurants."),
    ]),
    ("DATA / CLOUD", "#CC9060", "#A8703F", [
        ("postgresql", "postgresql", "PostgreSQL",
         "Reliable open-source relational database, the default choice for structured application data."),
        ("sqlserver", "microsoftsqlserver", "SQL Server",
         "Microsoft's relational database, paired with ASP.NET Core in my Order Management System project."),
        ("supabase", "supabase", "Supabase",
         "Postgres-based backend platform with auth and storage, powering EduUpcycle's teacher and student portals."),
        ("vercel", "vercel", "Vercel",
         "Deployment platform for Next.js apps: preview deployments for every change and zero-config hosting."),
    ]),
    ("TOOLS / OPS", "#6B6B6B", "#3B3B3B", [
        ("docker", "docker", "Docker",
         "Containers package code together with its environment: build once, run anywhere. The unit of deployment for modern services."),
        ("git", "git", "Git",
         "Version control for every project, with branching and pull requests in team and group work."),
        ("githubactions", "githubactions", "GitHub Actions",
         "Workflow automation built into GitHub: builds, tests and scheduled jobs straight from the repository."),
        ("jupyter", "jupyter", "Jupyter",
         "Notebooks for fast experiments, such as comparing agent frameworks side by side."),
    ]),
]

# Arial Bold advance widths (per 1000 em) — a safe upper bound for the Segoe/Helvetica stack
_W = {**{c: 722 for c in "ABCDHKNRU"}, "E": 667, "F": 611, "G": 778, "I": 278, "J": 556, "L": 611, "M": 833,
      "O": 778, "P": 667, "Q": 778, "S": 667, "T": 611, "V": 667, "W": 944, "X": 667, "Y": 667, "Z": 611,
      **{c: 556 for c in "acekssxyv"}, **{c: 611 for c in "bdghnopqu"}, "f": 333, "i": 278, "j": 278, "l": 278,
      "m": 889, "r": 389, "t": 333, "w": 778, "z": 500, " ": 278, ".": 278, "/": 278, "-": 333, "+": 584}


# Arial Regular advance widths, for the guide descriptions (Liberation Sans on Linux shares them)
_WR = {"A": 667, "B": 667, "C": 722, "D": 722, "E": 667, "F": 611, "G": 778, "H": 722, "I": 278, "J": 500, "K": 667,
       "L": 556, "M": 833, "N": 722, "O": 778, "P": 667, "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722, "V": 667,
       "W": 944, "X": 667, "Y": 667, "Z": 611, **{c: 556 for c in "abdeghnopqu"}, **{c: 500 for c in "cksvxyz"},
       "f": 278, "i": 222, "j": 222, "l": 222, "m": 833, "r": 333, "t": 278, "w": 722, " ": 278, "-": 333, "/": 278,
       "+": 584, "&": 667, "'": 191, '"': 355, "(": 333, ")": 333, "—": 1000, **{c: 278 for c in ".,:;!"},
       **{c: 556 for c in "0123456789?"}}


def text_width(s, size, table=None):
    table = table or _W
    return sum(table.get(c, 1000 if ord(c) > 127 else 611) for c in s) * size / 1000


def wrap_px(text, size, max_w):
    """Greedy word wrap on estimated pixel width, so lines fill the card instead
    of stopping at a character count that only fills two thirds of it."""
    lines, cur = [], ""
    for word in text.split():
        cand = f"{cur} {word}".strip()
        if cur and text_width(cand, size, _WR) > max_w:
            lines.append(cur)
            cur = word
        else:
            cur = cand
    return lines + [cur] if cur else lines




_icons = {}


def icon_path(slug):
    if slug not in _icons:
        with urllib.request.urlopen(ICON_URL.format(slug), timeout=20) as r:
            svg = r.read().decode()
        m = re.search(r'<path d="([^"]+)"', svg)
        if not m:
            raise SystemExit(f"no path in Simple Icons svg for {slug}")
        _icons[slug] = m.group(1)
    return _icons[slug]


def svg(w, h, title, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" font-family="{FONT}">'
            f'<title>{html.escape(title)}</title>{body}</svg>\n')


def flower(x, y, petal, centre, dur):
    petals = "".join(f'<circle cx="{cx}" cy="{cy}" r="3.4" fill="{petal}"/>'
                     for cx, cy in [(0, -6.5), (6.2, -2), (3.8, 5.3), (-3.8, 5.3), (-6.2, -2)])
    return (f'<g transform="translate({x},{y})"><g><animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="{dur}s" repeatCount="indefinite"/>'
            f'{petals}</g><circle r="2.8" fill="{centre}"/></g>')


def chip(slug, icon, label, colour):
    rnd = random.Random(label)
    dur, beg = 3.5 + rnd.random(), -rnd.random() * 4
    tw = int(text_width(label, 12)) + 2
    if icon:
        w = 32 + tw + 13
        inner = (f'<g transform="translate(12,8) scale(0.5833)"><path d="{icon_path(icon)}" fill="{colour}"/></g>'
                 f'<text x="32" y="19" font-size="12" font-weight="600" fill="{colour}">{html.escape(label)}</text>')
    else:
        w = 12 + tw + 12
        inner = f'<text x="{w / 2:g}" y="19" text-anchor="middle" font-size="12" font-weight="600" fill="{colour}">{html.escape(label)}</text>'
    body = ('<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="0s" dur="0.5s" fill="freeze"/>'
            f'<g><animateTransform attributeName="transform" type="translate" values="0 1.2;0 -1.2;0 1.2" calcMode="spline" keySplines="0.4 0 0.6 1;0.4 0 0.6 1" keyTimes="0;0.5;1" dur="{dur:.1f}s" begin="{beg:.1f}s" repeatCount="indefinite"/>'
            f'<rect x="1" y="4" width="{w - 2}" height="22" rx="11" fill="{colour}" fill-opacity="0.07" stroke="{colour}" stroke-width="1.3"/>'
            f'{inner}</g></g>')
    return svg(w, 30, label, body)


def label_chip(text, petal, centre):
    w = round(30 + len(text) * 7.6 + 5)
    return svg(w, 30, text, flower(14, 15, petal, centre, 14) +
               f'<text x="30" y="19" font-size="11" letter-spacing="1.5" fill="{GREY}">{html.escape(text)}</text>')


def guide(text, petal, centre, chips):
    """Field-guide card: one row per chip. Everything hangs off a 66px pitch so
    the icon tile, title, two description lines and the divider stay centred on
    each other; the card is tinted with the row's own flower colour."""
    P, X0, X1 = 66, 78, 812
    h = 50 + len(chips) * P
    parts = [f'\n<rect x="1" y="1" width="858" height="{h - 2}" rx="14" fill="{petal}" fill-opacity="0.05" stroke="{petal}" stroke-opacity="0.4" stroke-width="1.2"/>\n',
             flower(30, 26, centre, centre, 16) + "\n",
             f'<text x="48" y="30" font-size="11" letter-spacing="2" fill="{GREY}">{html.escape(text)}</text>\n']
    for i, (slug, icon, label, desc) in enumerate(chips):
        y, c = 52 + P * i, CHIP_COLOURS[i % 4]
        lines = wrap_px(desc, 13, X1 - X0 - 30)
        if len(lines) > 2:
            raise SystemExit(f"{label}: description needs {len(lines)} lines, max 2: {lines}")
        tile = f'<rect x="30" y="{y + 8}" width="34" height="34" rx="9" fill="{c}" fill-opacity="0.12"/>'
        if icon:
            glyph = f'<g transform="translate(38,{y + 16}) scale(0.75)"><path d="{icon_path(icon)}" fill="{c}"/></g>'
        else:  # no brand icon: a monogram in the same tile
            glyph = f'<text x="47" y="{y + 30}" text-anchor="middle" font-size="15" font-weight="700" fill="{c}">{html.escape(label[0].upper())}</text>'
        body = "".join(f'<text x="{X0}" y="{y + 29 + 17 * k}" font-size="13" fill="{GREY}">{html.escape(l)}</text>' for k, l in enumerate(lines))
        rule = f'<path d="M{X0} {y + 57} H {X1}" stroke="{c}" stroke-opacity="0.18" stroke-width="1"/>' if i < len(chips) - 1 else ""
        parts.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" begin="{0.15 + 0.09 * i:.2f}s" dur="0.5s" fill="freeze"/>'
                     f'{tile}{glyph}<text x="{X0}" y="{y + 11}" font-size="14" font-weight="700" fill="{c}">{html.escape(label)}</text>{body}{rule}</g>\n')
    return svg(860, h, f"{text} field guide", "".join(parts))


def readme_block():
    """Image URLs carry a content hash: GitHub's image proxy caches by URL, so a
    regenerated chip under the same path would otherwise stay stale for hours."""
    def img(name, alt):
        digest = hashlib.sha1((OUT / name).read_bytes()).hexdigest()[:8]
        return f'<img src="chips/{name}?v={digest}" alt="{html.escape(alt)}" />'

    rows, guides = [], []
    for i, (text, petal, centre, chips) in enumerate(STACK):
        imgs = [img(f"label-{i}.svg", text)] + [img(f"{slug}.svg", label) for slug, _, label, _ in chips]
        rows.append(" ".join(imgs))
        guides.append(img(f"guide-{i}.svg", f"{text} field guide") + "<br/>")
    return ('<!-- ============ Tech Garden ============ -->\n<div align="center">\n\n'
            + "\n<br/>\n".join(rows) + "\n\n<details>\n"
            '<summary>🌱 &nbsp;<b>Field guide</b> — open to read what every chip actually is</summary>\n<br/>\n<div align="center">\n'
            + "\n".join(guides) + "\n</div>\n</details>\n\n</div>\n")


def main():
    OUT.mkdir(exist_ok=True)
    keep = set()
    for i, (text, petal, centre, chips) in enumerate(STACK):
        for slug, icon, label, desc in chips:
            (OUT / f"{slug}.svg").write_text(chip(slug, icon, label, CHIP_COLOURS[chips.index((slug, icon, label, desc)) % 4]))
            keep.add(f"{slug}.svg")
        (OUT / f"label-{i}.svg").write_text(label_chip(text, petal, centre))
        (OUT / f"guide-{i}.svg").write_text(guide(text, petal, centre, chips))
        keep |= {f"label-{i}.svg", f"guide-{i}.svg"}
    stale = [p for p in OUT.glob("*.svg") if p.name not in keep]
    for p in stale:
        p.unlink()

    readme = ROOT / "README.md"
    s = readme.read_text()
    start = s.index("<!-- ============ Tech Garden ============ -->")
    end_marker = "</details>\n\n</div>\n"
    end = s.index(end_marker, start) + len(end_marker)
    readme.write_text(s[:start] + readme_block() + s[end:])
    print(f"{len(keep)} svgs written, {len(stale)} stale removed: {', '.join(p.name for p in stale) or '-'}")


if __name__ == "__main__":
    main()
