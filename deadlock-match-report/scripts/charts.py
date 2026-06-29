#!/usr/bin/env python3
"""
charts.py - build interactive Plotly charts from a digest.

Exposes build_all_charts(digest) -> {chart_id: html_div_string}. The dashboard injects
these divs. plotly.js is loaded once by the dashboard (these divs exclude it).

Styling: the Deadlock "Brass HUD" skin - brass/gold on deep teal-black, Barlow tick/legend
fonts, cyan soul-lead, red death markers, brass "your" series, green/red damage, amber->red
death cost. The _layout/_axis helpers are the restyle recipe; mirror them anywhere new charts
are added so the palette stays consistent with dashboard.py.

Charts:
  soul_lead          - your team's soul lead over time, with your deaths + mid-boss marked
  networth_all       - net worth of all 12 players over time (your line bold/brass)
  economy_sources    - your souls by source, stacked, per phase
  dmg_over_time      - your hero damage dealt vs taken over time
  accuracy_phases    - your shooting accuracy per phase
  targeting_heatmap  - cross-team damage among you + the enemies who beat you
  death_cost         - each of your deaths over time, bar height = seconds spent dead
"""
import json, sys
from pathlib import Path

import plotly.graph_objects as go
from plotly.offline import plot

# ---- Brass HUD palette (kept in sync with dashboard.py) ---------------------
SOULS   = "#2ADFFC"   # souls / economy lead reads cyan
BRASS   = "#C8A24A"   # primary gold accent / "your" series
GOOD    = "#6FA84B"   # vitality green / damage dealt
BAD     = "#C8413B"   # death red / damage taken
CAUTION = "#D9A441"   # amber
SPIRIT  = "#B07BD6"   # spirit violet
WEAPON  = "#C56B2C"   # weapon amber
TXT     = "#e8e0cf"
MUT     = "#978d77"
GRID    = "#1e2636"
ZERO    = "#3a4250"
LINE    = "#2a3242"
FONT    = "'Barlow', system-ui, sans-serif"

# muted line colours for the other 11 players in the net-worth chart
OTHERS = ["#5f7a86", "#8a6f55", "#7a6b9a", "#6b7280", "#5f8a6f", "#9a7d8a",
          "#7e7a5a", "#6a8a86", "#8a6a6a", "#6f7a9a", "#8a8a6a"]


def _sec(ts):  # "m:ss" -> seconds
    m, s = ts.split(":"); return int(m) * 60 + int(s)


def _axis(**extra):
    base = dict(gridcolor=GRID, zerolinecolor=ZERO, linecolor=LINE,
                tickfont=dict(color=MUT, size=12.5), automargin=True)
    base.update(extra)
    return base


def _style(fig, margin=None, legend=True, xaxis=None, yaxis=None, height=340):
    # An explicit height is essential: in the 2-column grid the chart's container has no definite
    # height when Plotly first renders, so without this the plot collapses to a sliver.
    fig.update_layout(
        height=height, autosize=True,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,0.012)",
        font=dict(family=FONT, color="#a89f8a", size=13),
        margin=margin or dict(l=56, r=18, t=12, b=44),
        showlegend=legend,
        legend=dict(orientation="h", y=-0.18, font=dict(color="#a89f8a", size=12.5)),
        hoverlabel=dict(bgcolor="#11151d", bordercolor=BRASS, font=dict(color=TXT)),
        xaxis=_axis(**(xaxis or {})), yaxis=_axis(**(yaxis or {})),
    )
    return fig


def _div(fig):
    return plot(fig, output_type="div", include_plotlyjs=False,
                config={"displayModeBar": False, "responsive": True})


def _me(digest):
    return next(p for p in digest["players"] if p["is_me"])


def _title(text, color):
    return dict(text=text, font=dict(color=color, size=12.5))


def soul_lead(digest):
    xs = [_sec(t) / 60 for t, _ in digest["soul_lead_series"]]
    ys = [v for _, v in digest["soul_lead_series"]]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=SOULS, width=3),
                             fill="tozeroy", fillcolor="rgba(42,223,252,0.10)",
                             name="Soul lead",
                             hovertemplate="%{x:.0f} min · %{y:,} souls<extra></extra>"))
    fig.add_hline(y=0, line=dict(color="#5a6172", width=1, dash="dot"))
    me = _me(digest)
    for d in me.get("deaths", []):
        fig.add_vline(x=_sec(d["t"]) / 60, line=dict(color=BAD, width=1, dash="dot"))
    for b in digest.get("mid_boss", []):
        fig.add_vline(x=_sec(b["t"]) / 60, line=dict(color=GOOD, width=1))
    _style(fig, legend=False, xaxis=dict(title=_title("minute", MUT), dtick=5),
           yaxis=dict(title=_title("souls ahead (+) / behind (−)", MUT), tickformat=",d"))
    return _div(fig)


def networth_all(digest):
    fig = go.Figure()
    others = [(h, s) for h, s in digest["networth_all"].items() if "(you)" not in h]
    you = [(h, s) for h, s in digest["networth_all"].items() if "(you)" in h]
    for i, (hero, series) in enumerate(others):
        fig.add_trace(go.Scatter(x=[t / 60 for t, _ in series], y=[v for _, v in series],
                                 mode="lines", name=hero, line=dict(width=1.4, color=OTHERS[i % len(OTHERS)]),
                                 hovertemplate=hero + " · %{y:,}<extra></extra>"))
    for hero, series in you:  # draw your line last so it sits on top
        fig.add_trace(go.Scatter(x=[t / 60 for t, _ in series], y=[v for _, v in series],
                                 mode="lines", name=hero, line=dict(width=4, color=BRASS),
                                 hovertemplate=hero + " · %{y:,}<extra></extra>"))
    _style(fig, xaxis=dict(title=_title("minute", MUT), dtick=5),
           yaxis=dict(title=_title("net worth", MUT), tickformat="~s"))
    return _div(fig)


def economy_sources(digest):
    me = _me(digest); phases = me.get("phases", {})
    order = [p for p in ["Laning", "Early-mid", "Mid", "Late"] if p in phases]
    srcs = [("Lane creeps", "gold_lane_creep", BRASS),
            ("Neutrals", "gold_neutral_creep", GOOD),
            ("Mid-boss", "gold_boss", CAUTION),
            ("Denies", "gold_denied", SOULS),
            ("Lost on death", "gold_death_loss", BAD)]
    fig = go.Figure()
    for label, key, col in srcs:
        sign = -1 if key == "gold_death_loss" else 1
        fig.add_trace(go.Bar(name=label, x=order, y=[sign * phases[p].get(key, 0) for p in order],
                             marker_color=col, marker_line=dict(color="#0a0d13", width=1)))
    fig.update_layout(barmode="relative")
    _style(fig, xaxis=dict(title=_title("phase", MUT)),
           yaxis=dict(title=_title("souls gained / lost", MUT), tickformat="~s"))
    return _div(fig)


def dmg_over_time(digest):
    me = _me(digest)
    dd = me.get("dmg_series_dealt"); dt = me.get("dmg_series_taken")
    fig = go.Figure()
    if dd and dt:
        fig.add_trace(go.Scatter(x=[t / 60 for t, _ in dd], y=[v for _, v in dd], name="Dealt",
                                 mode="lines", line=dict(color=GOOD, width=3),
                                 hovertemplate="Dealt · %{y:,}<extra></extra>"))
        fig.add_trace(go.Scatter(x=[t / 60 for t, _ in dt], y=[v for _, v in dt], name="Taken",
                                 mode="lines", line=dict(color=BAD, width=3),
                                 hovertemplate="Taken · %{y:,}<extra></extra>"))
    _style(fig, xaxis=dict(title=_title("minute", MUT), dtick=5),
           yaxis=dict(title=_title("cumulative hero damage", MUT), tickformat="~s"))
    return _div(fig)


def accuracy_phases(digest):
    me = _me(digest); phases = me.get("phases", {})
    order = [p for p in ["Laning", "Early-mid", "Mid", "Late"] if p in phases]
    ys = [phases[p].get("accuracy_pct") or 0 for p in order]
    fig = go.Figure(go.Bar(x=order, y=ys, marker_color=BRASS, marker_line=dict(color="#0a0d13", width=1),
                           text=[f"{v}%" for v in ys], textposition="outside",
                           textfont=dict(color="#bcae92", size=12.5, family=FONT)))
    _style(fig, legend=False, xaxis=dict(title=_title("phase", MUT)),
           yaxis=dict(title=_title("shots hit %", MUT)))
    return _div(fig)


def targeting_heatmap(digest):
    me = _me(digest)
    focus = digest["focus_enemies"]
    names = [me["hero"] + " (you)"] + focus
    deep = {p["hero"]: p for p in digest["players"] if "damage_dealt_to" in p}

    def dealt(dealer_hero, target_hero):
        src = deep.get(dealer_hero)
        if not src:
            return 0
        return src.get("damage_dealt_to", {}).get(target_hero, 0)

    rows = []
    for r in names:
        dealer = me["hero"] if "(you)" in r else r
        rows.append([dealt(dealer, (c.replace(" (you)", "") if "(you)" in c else c)) for c in names])
    fig = go.Figure(go.Heatmap(
        z=rows, x=names, y=names,
        colorscale=[[0, "#11151d"], [0.5, "#5a4a26"], [1, BRASS]],
        text=[[f"{v:,}" if v else "" for v in row] for row in rows],
        texttemplate="%{text}", textfont=dict(color=TXT, size=12, family=FONT),
        hovertemplate="%{y} → %{x}<br>%{z:,}<extra></extra>",
        colorbar=dict(outlinewidth=0, tickfont=dict(color=MUT, size=11))))
    _style(fig, legend=False, xaxis=dict(title=_title("damage dealt to →", MUT)),
           yaxis=dict(title=_title("dealt by", MUT)))
    return _div(fig)


def death_cost(digest):
    me = _me(digest); deaths = me.get("deaths", [])
    labels = [f'{d["killer"]} {d["t"]}' for d in deaths]
    ys = [d.get("down_s") or 0 for d in deaths]
    fig = go.Figure(go.Bar(
        x=labels, y=ys,
        marker=dict(color=ys, colorscale=[[0, CAUTION], [1, BAD]], cmin=0,
                    cmax=(max(ys) if ys else 1), line=dict(color="#0a0d13", width=1)),
        text=[f"{v}s" for v in ys], textposition="outside",
        textfont=dict(color="#bcae92", size=12.5, family=FONT),
        hovertemplate="%{x} · %{y}s dead<extra></extra>"))
    _style(fig, legend=False, margin=dict(l=46, r=14, t=18, b=96),
           xaxis=dict(tickangle=-40, tickfont=dict(color=MUT, size=11.5)),
           yaxis=dict(title=_title("seconds dead", MUT),
                      range=[0, (max(ys) * 1.18) if ys else 1]))
    return _div(fig)


def build_all_charts(digest):
    return {
        "soul_lead": soul_lead(digest),
        "networth_all": networth_all(digest),
        "economy_sources": economy_sources(digest),
        "dmg_over_time": dmg_over_time(digest),
        "accuracy_phases": accuracy_phases(digest),
        "targeting_heatmap": targeting_heatmap(digest),
        "death_cost": death_cost(digest),
    }


if __name__ == "__main__":
    digest = json.loads(Path(sys.argv[1]).read_text())
    charts = build_all_charts(digest)
    Path(sys.argv[2] if len(sys.argv) > 2 else "charts.json").write_text(json.dumps(charts))
    print("charts:", ", ".join(charts))
