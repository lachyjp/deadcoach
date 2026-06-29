#!/usr/bin/env python3
"""
meta.py - pull CURRENT item meta per hero so suggestions reflect this patch, not training data.

For each hero id, query the analytics item-win-loss endpoint filtered to a recent time window and
the lobby's rank band, then rank items by win rate. Also flags "underrated" items: high win rate
but low pick (few matches relative to the hero's most-picked items) - the obscure picks worth trying.

Usage:
  python3 meta.py --heroes 25,4,65 --min-badge 18 --max-badge 31 --days 30 --out meta.json

Writes meta.json: {hero_id: {"top": [...], "underrated": [...]}}, item entries carry name/slot/tier/win_rate/matches.
Standard library only. Run after fetch.py (which populates the name cache).
"""
import argparse, json, time, urllib.parse, urllib.request, urllib.error
from pathlib import Path
import dl_lib as L

def fetch_item_stats(hero_id, min_badge, max_badge, min_unix, min_matches):
    params = [("hero_ids", str(hero_id)), ("min_matches", str(min_matches)),
              ("min_unix_timestamp", str(min_unix))]
    if min_badge is not None: params.append(("min_average_badge", str(min_badge)))
    if max_badge is not None: params.append(("max_average_badge", str(max_badge)))
    url = L.ITEM_STATS + "?" + urllib.parse.urlencode(params)
    try:
        return L.get_json(url)
    except urllib.error.HTTPError as e:
        print(f"  item-stats for hero {hero_id} failed ({e.code}); skipping")
        return []

def build_meta(hero_ids, min_badge, max_badge, days, min_matches, item_by_id):
    min_unix = int(time.time()) - days * 86400
    meta = {}
    for hid in hero_ids:
        rows = fetch_item_stats(hid, min_badge, max_badge, min_unix, min_matches)
        items = []
        for r in rows:
            m = item_by_id.get(r["item_id"])
            if not m or m["type"] != "upgrade":
                continue
            matches = r.get("matches") or (r.get("wins", 0) + r.get("losses", 0))
            if not matches:
                continue
            items.append({"name": m["name"], "slot": m["slot"], "tier": m["tier"],
                          "win_rate": round(100 * r.get("wins", 0) / matches, 1), "matches": matches})
        if not items:
            meta[str(hid)] = {"top": [], "underrated": [], "note": "no item stats returned"}
            continue
        max_picks = max(i["matches"] for i in items)
        top = sorted(items, key=lambda i: -i["win_rate"])[:15]
        # underrated: win rate well above average, pick volume low
        avg_wr = sum(i["win_rate"] for i in items) / len(items)
        underrated = sorted([i for i in items if i["win_rate"] >= avg_wr + 3
                             and i["matches"] <= 0.25 * max_picks],
                            key=lambda i: -i["win_rate"])[:8]
        meta[str(hid)] = {"top": top, "underrated": underrated, "avg_win_rate": round(avg_wr, 1)}
    return meta

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--heroes", required=True, help="comma-separated hero ids")
    ap.add_argument("--min-badge", type=int)
    ap.add_argument("--max-badge", type=int)
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--min-matches", type=int, default=50)
    ap.add_argument("--out", default="meta.json")
    a = ap.parse_args()
    item_by_id, _ = L.load_names()
    hero_ids = [int(x) for x in a.heroes.split(",") if x.strip()]
    meta = build_meta(hero_ids, a.min_badge, a.max_badge, a.days, a.min_matches, item_by_id)
    Path(a.out).write_text(json.dumps(meta, indent=1))
    for hid, m in meta.items():
        print(f"hero {hid}: {len(m.get('top',[]))} ranked items, {len(m.get('underrated',[]))} underrated")
