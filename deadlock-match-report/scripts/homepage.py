#!/usr/bin/env python3
"""
homepage.py - build the Deadcoach site homepage (index.html) from a matches manifest.

The homepage wears the same "Brass HUD" skin as the reports: an overall stats strip (games, win
rate, most-played hero, average K/D/A) above a responsive grid of match tiles. Each tile links to
that match's report at <match_id>/.

Usage:
  python3 scripts/homepage.py --manifest docs/matches.json --out docs/index.html
"""
import argparse, html, json
from collections import Counter
from pathlib import Path

CSS = """
*{box-sizing:border-box}html,body{margin:0}
body{background:#0a0d13;color:#e8e0cf;font-family:'Barlow',system-ui,sans-serif;line-height:1.5}
a{text-decoration:none;color:inherit}
.tex{position:fixed;inset:0;pointer-events:none;z-index:1;opacity:.045;mix-blend-mode:overlay;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");background-size:180px 180px}
.vig{position:fixed;inset:0;pointer-events:none;z-index:1;background:radial-gradient(120% 80% at 50% -10%,#15243033,transparent 60%),radial-gradient(100% 60% at 50% 120%,#1a140833,transparent 60%)}
.wrap{position:relative;z-index:2;max-width:1100px;margin:0 auto;padding:0 26px 70px}
header.site{position:relative;z-index:2;border-bottom:1px solid #6c552a55;background:rgba(10,13,19,.9)}
.hwrap{max-width:1100px;margin:0 auto;padding:26px 26px 22px}
.brand{font-family:'Big Shoulders Display',sans-serif;font-weight:900;font-size:40px;letter-spacing:.03em;line-height:1;background:linear-gradient(180deg,#F4D888,#C8A24A 60%,#7d6128);-webkit-background-clip:text;background-clip:text;color:transparent}
.tag{color:#a89f8a;font-size:14.5px;letter-spacing:.03em;margin-top:6px}
.eyebrow{font-family:'Barlow Semi Condensed',sans-serif;font-weight:600;font-size:12px;letter-spacing:.28em;color:#9a7b3d;text-transform:uppercase}
.statstrip{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:26px 0 6px}
.stat{background:linear-gradient(180deg,#1b2130,#11151e);border:1px solid #2a3144;border-top:2px solid #C8A24A;padding:12px 14px}
.stat .k{font-size:11.5px;letter-spacing:.1em;color:#978d77;text-transform:uppercase;font-weight:700}
.stat .v{font-family:'Big Shoulders Display',sans-serif;font-weight:700;font-size:26px;color:#e8e0cf;display:flex;align-items:center;gap:8px}
.stat .v img{width:26px;height:26px;border-radius:50%;object-fit:cover;object-position:center top;border:1px solid #6c552a}
.sec-head{display:flex;align-items:center;gap:12px;margin:34px 0 16px}
.sec-title{font-family:'Big Shoulders Display',sans-serif;font-weight:800;font-size:22px;letter-spacing:.06em;color:#e8e0cf;margin:0;text-transform:uppercase}
.rule{flex:1;height:2px;background:linear-gradient(90deg,#C8A24A,#C8A24A22 60%,transparent)}
.dia{color:#7d6128}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}
.tile{position:relative;display:flex;gap:13px;background:linear-gradient(180deg,#141925,#0e121b);border:1px solid #232a3a;border-top:2px solid #C8A24A;padding:14px;transition:border-color .12s,transform .12s}
.tile:hover{border-color:#C8A24A;transform:translateY(-2px)}
.tile.loss{border-top-color:#C04A3C}
.portrait{width:62px;height:78px;flex:0 0 auto;border:1px solid #6c552a;background:#0b0e14;overflow:hidden;position:relative}
.portrait img{width:100%;height:100%;object-fit:cover;object-position:center top}
.tinfo{flex:1;min-width:0}
.tname{font-family:'Big Shoulders Display',sans-serif;font-weight:800;font-size:21px;letter-spacing:.02em;color:#e8e0cf;line-height:1}
.tres{font-family:'Big Shoulders Display',sans-serif;font-weight:600;font-size:11px;letter-spacing:.22em;text-transform:uppercase;margin:4px 0 8px}
.tres.win{color:#6FA84B}.tres.loss{color:#C04A3C}
.tkda{font-size:14px;color:#cabd9f}.tkda b{color:#F4D888}
.tmeta{color:#847c6a;font-size:12.5px;letter-spacing:.03em;margin-top:6px}
.tmeta .souls{color:#2ADFFC}
.footer{position:relative;z-index:2;margin-top:36px;padding-top:18px;border-top:1px solid #1c2231;color:#7a7160;font-size:13px;letter-spacing:.04em;text-align:center}
.footer b{color:#978d77}
@media(max-width:680px){.statstrip{grid-template-columns:repeat(2,1fr)}.brand{font-size:32px}}
"""


def esc(s):
    return html.escape(str(s))


def _avatar(url, cls):
    return f'<img class="{cls}" src="{esc(url)}" alt="">' if url else ""


def build_homepage(matches, title="Deadcoach", subtitle="Deadlock match reports"):
    ms = sorted(matches, key=lambda m: m.get("start_time") or m.get("match_id") or 0, reverse=True)
    games = len(ms)
    wins = sum(1 for m in ms if m.get("won"))
    wr = round(100 * wins / games) if games else 0
    hero_counts = Counter(m.get("hero", "?") for m in ms)
    top_hero, _ = (hero_counts.most_common(1)[0] if hero_counts else ("-", 0))
    top_hero_img = next((m.get("hero_image") for m in ms if m.get("hero") == top_hero), None)
    k = sum(m["kda"][0] for m in ms if m.get("kda"))
    d = sum(m["kda"][1] for m in ms if m.get("kda"))
    a = sum(m["kda"][2] for m in ms if m.get("kda"))
    avg = (f'{k/games:.1f} / {d/games:.1f} / {a/games:.1f}' if games else "-")

    strip = "".join([
        f'<div class="stat"><div class="k">Games</div><div class="v">{games}</div></div>',
        f'<div class="stat"><div class="k">Win rate</div><div class="v">{wr}%</div></div>',
        f'<div class="stat"><div class="k">Most played</div><div class="v">{_avatar(top_hero_img,"")}{esc(top_hero)}</div></div>',
        f'<div class="stat"><div class="k">Avg K / D / A</div><div class="v">{esc(avg)}</div></div>',
    ])

    tiles = ""
    for m in ms:
        won = m.get("won")
        rcls = "win" if won else "loss"
        res = "Victory" if won else "Defeat"
        kk, dd, aa = (m.get("kda") or [0, 0, 0])
        url = m.get("url") or f'{m["match_id"]}/'
        tiles += (
            f'<a class="tile {rcls}" href="{esc(url)}">'
            f'<div class="portrait">{_avatar(m.get("hero_image"),"")}</div>'
            f'<div class="tinfo">'
            f'<div class="tname">{esc(m.get("hero","?"))}</div>'
            f'<div class="tres {rcls}">&#9670; {res}</div>'
            f'<div class="tkda"><b>{kk}</b> / {dd} / {aa}</div>'
            f'<div class="tmeta">{esc(m.get("date",""))} &nbsp;·&nbsp; {esc(m.get("duration",""))} '
            f'&nbsp;·&nbsp; <span class="souls">{int(m.get("net_worth",0)):,} souls</span></div>'
            f'</div></a>')

    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<meta name="googlebot" content="noindex, nofollow">
<title>{esc(title)} — {esc(subtitle)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@400;600;700;800;900&family=Barlow:wght@400;500;600;700&family=Barlow+Semi+Condensed:wght@500;600;700&display=swap" rel="stylesheet">
<style>{CSS}</style></head>
<body>
<div class="tex"></div><div class="vig"></div>
<header class="site"><div class="hwrap">
  <div class="eyebrow">Deadlock coaching</div>
  <div class="brand">{esc(title)}</div>
  <div class="tag">{esc(subtitle)}</div>
</div></header>
<div class="wrap">
  <div class="statstrip">{strip}</div>
  <div class="sec-head"><h2 class="sec-title">Matches</h2><span class="rule"></span><span class="dia">&#9670;</span></div>
  <div class="grid">{tiles or '<p style="color:#978d77">No matches published yet.</p>'}</div>
  <div class="footer">Generated by <b>deadcoach</b> · data via deadlock-api.com · {games} matches</div>
</div>
</body></html>'''


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--title", default="Deadcoach")
    a = ap.parse_args()
    matches = json.loads(Path(a.manifest).read_text())
    Path(a.out).write_text(build_homepage(matches, title=a.title))
    print("wrote", a.out, f"({len(matches)} matches)")
