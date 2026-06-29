#!/usr/bin/env python3
"""
dl_lib.py - shared core for the deadlock-match-report skill.

Responsibilities:
  - talk to the open Deadlock APIs (match metadata, match history, asset name tables)
  - join numeric item/hero IDs to current display names (no hashing, no stale localisation)
  - build a phase-segmented digest: per-phase economy / combat / survivability metrics
  - reconstruct the full player-vs-player damage matrix over time (targeting analysis)
  - reconstruct the death log (who, when, where, how fast you were bursted)

Everything downstream (charts, dashboard, the LLM analysis) reads the digest this produces.
Standard library only.
"""

import json, os, sys, time, urllib.request, urllib.error, urllib.parse
from pathlib import Path
from collections import Counter, defaultdict

# ---- endpoints (verified against the deadlock-api source) -------------------
MATCH_META   = "https://api.deadlock-api.com/v1/matches/{mid}/metadata"
MATCH_HIST   = "https://api.deadlock-api.com/v1/players/{acc}/match-history"
ITEM_STATS   = "https://api.deadlock-api.com/v1/analytics/item-win-loss-stats"
HERO_STATS   = "https://api.deadlock-api.com/v1/analytics/hero-win-loss-stats"
ASSET_ITEMS  = "https://assets.deadlock-api.com/v2/items?language=english"
ASSET_HEROES = "https://assets.deadlock-api.com/v2/heroes?language=english"
ASSET_MAP    = "https://api.deadlock-api.com/v1/assets/map"
CACHE_DIR    = Path(os.environ.get("DL_CACHE", Path.home() / ".cache" / "deadlock"))
# world coordinates are centred on the map origin; the play area spans +/- this radius. Used to
# project (x, y) onto the minimap image. Falls back to these if the /v1/map API is unreachable.
MAP_RADIUS_FALLBACK = 10752
MAP_PLAIN_FALLBACK  = "https://assets-bucket.deadlock-api.com/assets-api-res/images/maps/minimap_plain.png"

# ---- phase windows in seconds (approximate; phases also depend on game-state) -
PHASES = [
    ("Laning",     0,    600),
    ("Early-mid",  600,  1080),
    ("Mid",        1080, 1680),
    ("Late",       1680, 10**9),
]

# ---- http -------------------------------------------------------------------
def get_json(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "deadlock-match-report/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (429, 500, 502, 503):   # transient, back off
                time.sleep(2 * (i + 1)); continue
            raise
        except urllib.error.URLError as e:
            last = e; time.sleep(2 * (i + 1))
    raise last

# ---- name tables (cached locally, refreshable) ------------------------------
def load_names(refresh=False):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    items_f, heroes_f = CACHE_DIR / "items.json", CACHE_DIR / "heroes.json"
    if refresh or not items_f.exists():
        items_f.write_text(json.dumps(get_json(ASSET_ITEMS)))
    if refresh or not heroes_f.exists():
        heroes_f.write_text(json.dumps(get_json(ASSET_HEROES)))
    items  = json.loads(items_f.read_text())
    heroes = json.loads(heroes_f.read_text())
    item_by_id = {it["id"]: {"name": it.get("name") or it.get("class_name"),
                             "slot": it.get("item_slot_type"), "tier": it.get("item_tier"),
                             "type": it.get("type"), "class_name": it.get("class_name"),
                             "image": _item_image(it)}
                  for it in items if "id" in it}
    hero_by_id = {h["id"]: h.get("name", f"hero_{h['id']}") for h in heroes if "id" in h}
    return item_by_id, hero_by_id

def _item_image(it):
    """Absolute icon URL for an item from the assets JSON (the reliable field, per the API)."""
    for k in ("shop_image_small_webp", "shop_image_small", "shop_image", "image_webp", "image"):
        v = it.get(k)
        if v:
            return v
    return None

def hero_images(refresh=False):
    """id -> portrait/card image URL, read from the cached heroes table.

    The assets heroes table exposes an ``images`` dict; we prefer the upright hero "card"
    portrait used in the report header, falling back through the other available art.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    heroes_f = CACHE_DIR / "heroes.json"
    if refresh or not heroes_f.exists():
        heroes_f.write_text(json.dumps(get_json(ASSET_HEROES)))
    heroes = json.loads(heroes_f.read_text())
    out = {}
    for h in heroes:
        if "id" not in h:
            continue
        imgs = h.get("images") or {}
        url = None
        if isinstance(imgs, dict):
            for k in ("icon_hero_card", "icon_hero_card_webp", "selection_image",
                      "selection_image_webp", "top_bar_vertical", "minimap_image"):
                if imgs.get(k):
                    url = imgs[k]; break
            if not url:
                url = next((v for v in imgs.values() if isinstance(v, str) and v), None)
        out[h["id"]] = url
    return out

def load_map(refresh=False):
    """Map background image URL + world radius, for projecting (x, y) coords onto the minimap.
    Reads the /v1/map asset (cached); falls back to known constants if the API is unreachable."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    f = CACHE_DIR / "map.json"
    d = {}
    try:
        if refresh or not f.exists():
            f.write_text(json.dumps(get_json(ASSET_MAP)))
        d = json.loads(f.read_text())
    except Exception:
        d = {}
    images = d.get("images") if isinstance(d.get("images"), dict) else {}
    image = (images.get("plain") or images.get("minimap")
             or d.get("plain") or d.get("minimap") or MAP_PLAIN_FALLBACK)
    radius = d.get("radius") or MAP_RADIUS_FALLBACK
    return {"image": image, "radius": radius}

# ---- match loading ----------------------------------------------------------
def load_match(match_id=None, file=None, out_dir="."):
    if file:
        return json.loads(Path(file).read_text())
    cache = Path(out_dir) / f"{match_id}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    try:
        data = get_json(MATCH_META.format(mid=match_id))
    except urllib.error.HTTPError as e:
        sys.exit(f"Match {match_id} fetch failed ({e.code}). It may not be ingested yet. "
                 f"Open it on deadlocklabs.gg or tracklock.gg to trigger ingestion, then retry.")
    cache.write_text(json.dumps(data))
    return data

def latest_match_id(account_id):
    hist = get_json(MATCH_HIST.format(acc=account_id))
    if not hist:
        sys.exit(f"No match history for account {account_id}.")
    return max(h["match_id"] for h in hist)

def match_history(account_id):
    return get_json(MATCH_HIST.format(acc=account_id))

# ---- helpers ----------------------------------------------------------------
def mmss(s):
    s = int(s); return f"{s//60}:{s%60:02d}"

def phase_of(t):
    for name, a, b in PHASES:
        if a <= t < b:
            return name
    return "Late"

def _interp_at(series, t):
    """Cumulative value of a (time, value) series at-or-before time t."""
    val = 0
    for ts, v in series:
        if ts <= t:
            val = v
        else:
            break
    return val

# ---- digest builders --------------------------------------------------------
def player_items(p, item_by_id):
    """Purchasable upgrades only, in purchase order, with sold time + phase."""
    out = []
    for ev in sorted(p["items"], key=lambda x: x["game_time_s"]):
        m = item_by_id.get(ev["item_id"])
        if not m or m["type"] != "upgrade":
            continue
        out.append({"t": ev["game_time_s"], "id": ev["item_id"], "name": m["name"], "slot": m["slot"],
                    "tier": m["tier"], "image": m.get("image"), "sold_t": ev.get("sold_time_s") or 0,
                    "imbued": bool(ev.get("imbued_ability_id")), "phase": phase_of(ev["game_time_s"])})
    return out

def stat_series(p, key):
    return [(s["time_stamp_s"], s.get(key, 0)) for s in (p.get("stats") or [])]

def phase_metrics(p):
    """Per-phase deltas from the sampled stat time series."""
    stats = p.get("stats") or []
    if not stats:
        return {}
    keys = ["net_worth", "kills", "deaths", "assists", "last_hits", "denies",
            "player_damage", "player_damage_taken", "player_healing", "self_healing",
            "shots_hit", "shots_missed", "neutral_kills",
            "gold_lane_creep", "gold_neutral_creep", "gold_boss", "gold_denied", "gold_death_loss"]
    out = {}
    for name, a, b in PHASES:
        # cumulative value at phase start (just before a) and end (b or last sample)
        def cum(key, t):
            return _interp_at([(s["time_stamp_s"], s.get(key, 0)) for s in stats], t)
        end_t = min(b, stats[-1]["time_stamp_s"])
        if end_t <= a and name != "Laning":
            continue
        seg = {}
        for k in keys:
            seg[k] = cum(k, end_t) - cum(k, a)
        dur_min = max((end_t - a) / 60.0, 1e-6)
        seg["souls_per_min"] = round(seg["net_worth"] / dur_min)
        sh, sm = seg["shots_hit"], seg["shots_missed"]
        seg["accuracy_pct"] = round(100 * sh / (sh + sm), 1) if (sh + sm) else None
        seg["window"] = f"{mmss(a)}-{mmss(end_t)}"
        out[name] = seg
    return out

def damage_matrix(mi, slot_to_acc, hero_by_id, acc_to_hero):
    """Return per-dealer -> per-target final damage and per-phase damage (heroes only)."""
    dm = mi.get("damage_matrix") or {}
    sample_t = dm.get("sample_time_s") or []
    # phase index boundaries within the sample array
    def dmg_in_phase(arr, a, b):
        # arr is cumulative, aligned to sample_t from index 0; trailing samples clamp to last
        # value. Final totals (arr[-1]) are exact; phase splits are a close approximation.
        if not arr or not sample_t:
            return 0
        def cum(t):
            v = 0
            for i, ts in enumerate(sample_t):
                if ts <= t:
                    v = arr[i] if i < len(arr) else arr[-1]
                else:
                    break
            return v
        return max(cum(b) - cum(a), 0)
    valid_slots = set(slot_to_acc)
    final = defaultdict(lambda: defaultdict(int))      # dealer_slot -> target_slot -> total
    byphase = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))  # phase -> dealer -> target
    for dealer in dm.get("damage_dealers", []):
        ds = dealer["dealer_player_slot"]
        if ds not in valid_slots:
            continue
        for src in dealer.get("damage_sources", []):
            for tp in src.get("damage_to_players", []):
                ts_slot = tp["target_player_slot"]
                if ts_slot not in valid_slots:
                    continue
                arr = tp["damage"]
                if not arr:
                    continue
                final[ds][ts_slot] += arr[-1]
                for name, a, b in PHASES:
                    byphase[name][ds][ts_slot] += dmg_in_phase(arr, a, b)
    return final, byphase

def damage_window(mi, my_slot, enemy_slots, slot_to_hero, t0, t1):
    """Approximate damage dealt to my_slot by each enemy between game-times t0 and t1, using the
    cumulative periodic damage_matrix samples (no per-event log exists, so this is a close
    approximation of the window around a death). Returns {hero: damage} sorted desc."""
    dm = mi.get("damage_matrix") or {}
    sample_t = dm.get("sample_time_s") or []
    if not sample_t:
        return {}
    def cum(arr, t):
        v = 0
        for i, ts in enumerate(sample_t):
            if ts <= t:
                v = arr[i] if i < len(arr) else arr[-1]
            else:
                break
        return v
    out = defaultdict(int)
    for dealer in dm.get("damage_dealers", []):
        ds = dealer["dealer_player_slot"]
        if ds not in enemy_slots:
            continue
        for src in dealer.get("damage_sources", []):
            for tp in src.get("damage_to_players", []):
                if tp.get("target_player_slot") != my_slot:
                    continue
                arr = tp.get("damage") or []
                if arr:
                    out[slot_to_hero.get(ds, "?")] += max(cum(arr, t1) - cum(arr, t0), 0)
    return dict(sorted(((h, v) for h, v in out.items() if v > 0), key=lambda kv: -kv[1]))

def build_digest(match, item_by_id, hero_by_id, me_acc, refresh_names=False):
    mi = match.get("match_info", match)
    players = mi["players"]
    try:
        hero_img_by_id = hero_images()
    except Exception:
        hero_img_by_id = {}
    win = mi["winning_team"]
    dur = mi["duration_s"]
    slot_to_acc  = {p["player_slot"]: p["account_id"] for p in players}
    acc_to_hero  = {p["account_id"]: hero_by_id.get(p["hero_id"], f"hero_{p['hero_id']}") for p in players}
    slot_to_hero = {p["player_slot"]: acc_to_hero[p["account_id"]] for p in players}

    me = next((p for p in players if p["account_id"] == me_acc), None)
    if me is None:
        sys.exit(f"Account {me_acc} is not in this match. Players: "
                 + ", ".join(str(p['account_id']) for p in players))
    my_team = me["team"]
    my_slot = me["player_slot"]

    # who beat me: enemies who killed me most, then by net worth
    kills_on_me = Counter(d.get("killer_player_slot") for d in me.get("death_details", []))
    enemies = [p for p in players if p["team"] != my_team]
    def threat_key(p):
        return (-kills_on_me.get(p["player_slot"], 0), -p["net_worth"])
    enemies_sorted = sorted(enemies, key=threat_key)
    focus = [p for p in enemies_sorted if kills_on_me.get(p["player_slot"], 0) >= 2]
    if len(focus) < 2:
        focus = enemies_sorted[:2]
    focus_accts = [p["account_id"] for p in focus]

    final_dmg, phase_dmg = damage_matrix(mi, slot_to_acc, hero_by_id, acc_to_hero)

    def player_block(p, deep):
        items = player_items(p, item_by_id)
        final_build = [x for x in items if not x["sold_t"]]
        split = Counter(x["slot"] for x in final_build)
        blk = {
            "account_id": p["account_id"], "hero": acc_to_hero[p["account_id"]],
            "hero_image": hero_img_by_id.get(p["hero_id"]),
            "is_me": p["account_id"] == me_acc, "team": p["team"], "won": p["team"] == win,
            "kda": [p["kills"], p["deaths"], p["assists"]],
            "net_worth": p["net_worth"], "souls_per_min": round(p["net_worth"] / (dur/60)),
            "last_hits": p["last_hits"], "denies": p["denies"], "level": p["level"],
            "lane": p.get("assigned_lane"),
            "split": {"weapon": split["weapon"], "spirit": split["spirit"], "vitality": split["vitality"]},
            "final_build": [f'T{x["tier"]} {x["slot"]} {x["name"]}' + (" (imbued)" if x["imbued"] else "")
                            for x in final_build],
            "final_build_items": [{"id": x["id"], "name": x["name"], "slot": x["slot"], "tier": x["tier"],
                                   "image": x.get("image"), "imbued": x["imbued"]} for x in final_build],
            "kills_on_me": kills_on_me.get(p["player_slot"], 0),
        }
        if deep:
            blk["purchase_timeline"] = [
                {"t": mmss(x["t"]), "phase": x["phase"], "item": f'T{x["tier"]} {x["slot"]} {x["name"]}',
                 "sold": mmss(x["sold_t"]) if x["sold_t"] else None} for x in items]
            blk["phases"] = phase_metrics(p)
            blk["networth_series"] = [[t, v] for t, v in stat_series(p, "net_worth")]
            myslot = p["player_slot"]
            enemy_team_p = 1 - p["team"]
            dealt = {}; self_dmg = 0
            for ts, dmg in final_dmg[myslot].items():
                if ts == myslot:
                    self_dmg = dmg; continue
                tp = next((pl for pl in players if pl["player_slot"] == ts), None)
                if tp and tp["team"] == enemy_team_p:
                    dealt[acc_to_hero[slot_to_acc[ts]]] = dmg
            blk["damage_dealt_to"] = dict(sorted(dealt.items(), key=lambda kv: -kv[1]))
            blk["self_damage"] = self_dmg
            taken = {}
            for ds, targets in final_dmg.items():
                if ds == myslot or myslot not in targets:
                    continue
                dp = next((pl for pl in players if pl["player_slot"] == ds), None)
                if dp and dp["team"] == enemy_team_p:
                    taken[acc_to_hero[slot_to_acc[ds]]] = targets[myslot]
            blk["damage_taken_from"] = dict(sorted(taken.items(), key=lambda kv: -kv[1]))
            if p["account_id"] == me_acc:
                enemy_slots = {pl["player_slot"] for pl in players if pl["team"] == enemy_team_p}
                sample_t = (mi.get("damage_matrix") or {}).get("sample_time_s") or []
                def _win(gt):
                    # the ~3-min sample interval bracketing the death (cumulative samples are sparse)
                    prev = max([s for s in sample_t if s < gt], default=0)
                    later = [s for s in sample_t if s >= gt]
                    return damage_window(mi, myslot, enemy_slots, slot_to_hero,
                                         prev, min(later) if later else gt)
                blk["deaths"] = [{
                    "t": mmss(d["game_time_s"]), "phase": phase_of(d["game_time_s"]),
                    "game_time_s": d["game_time_s"],
                    "killer": slot_to_hero.get(d.get("killer_player_slot"), "?"),
                    "focused_s": round(d.get("time_to_kill_s") or 0, 1),
                    "down_s": d.get("death_duration_s"),
                    "pos": [round(d["death_pos"][k]) for k in ("x", "y", "z")] if d.get("death_pos") else None,
                    "killer_pos": [round(d["killer_pos"][k]) for k in ("x", "y")] if d.get("killer_pos") else None,
                    "dmg_window": _win(d["game_time_s"]),
                } for d in p.get("death_details", [])]
                # my kills: any enemy death where I was the killer (position = where they died)
                kills = []
                for vp in players:
                    if vp["player_slot"] == myslot:
                        continue
                    for d in vp.get("death_details", []):
                        if d.get("killer_player_slot") == myslot and d.get("death_pos"):
                            kills.append((d["game_time_s"], {
                                "t": mmss(d["game_time_s"]), "phase": phase_of(d["game_time_s"]),
                                "victim": slot_to_hero.get(vp["player_slot"], "?"),
                                "pos": [round(d["death_pos"][k]) for k in ("x", "y")]}))
                blk["kills"] = [k for _, k in sorted(kills, key=lambda x: x[0])]
                dpp = Counter(phase_of(d["game_time_s"]) for d in p.get("death_details", []))
                for ph in blk["phases"]:
                    blk["phases"][ph]["deaths_actual"] = dpp.get(ph, 0)
                blk["dmg_series_dealt"] = [[t, v] for t, v in stat_series(p, "player_damage")]
                blk["dmg_series_taken"] = [[t, v] for t, v in stat_series(p, "player_damage_taken")]
        return blk

    deep_accts = {me_acc, *focus_accts}
    digest = {
        "match_id": mi.get("match_id"), "duration": mmss(dur), "duration_s": dur,
        "winning_team": win, "my_team": my_team, "i_won": my_team == win,
        "my_account": me_acc, "my_hero": acc_to_hero[me_acc],
        "my_hero_image": hero_img_by_id.get(me["hero_id"]),
        "avg_badge": {"team0": mi.get("average_badge_team0"), "team1": mi.get("average_badge_team1")},
        "focus_enemies": [acc_to_hero[a] for a in focus_accts],
        "players": [player_block(p, p["account_id"] in deep_accts) for p in players],
        # name -> {slot, image, tier} for every upgrade item, so the dashboard can resolve
        # real icons + category colours for any item named in the analysis (suggestions, etc.).
        "item_index": {m["name"]: {"id": iid, "slot": m["slot"], "image": m.get("image"), "tier": m["tier"]}
                       for iid, m in item_by_id.items()
                       if m.get("type") == "upgrade" and m.get("name")},
        # map background image + world radius for the deaths map (projects x/y onto the minimap)
        "map": load_map(),
    }
    # team soul lead over time (my_team minus enemy)
    series = {0: defaultdict(int), 1: defaultdict(int)}
    for p in players:
        for t, nw in stat_series(p, "net_worth"):
            series[p["team"]][t] += nw
    times = sorted(set(series[0]) & set(series[1]))
    enemy_team = 1 - my_team
    digest["soul_lead_series"] = [[mmss(t), series[my_team][t] - series[enemy_team][t]] for t in times]
    # compact per-player net worth series for the all-players chart
    digest["networth_all"] = {acc_to_hero[p["account_id"]] + (" (you)" if p["account_id"] == me_acc else ""):
                              [[t, v] for t, v in stat_series(p, "net_worth")] for p in players}
    # objectives + mid boss
    digest["objectives"] = [{"t": mmss(o["destroyed_time_s"]), "team": o.get("team"),
                             "obj_id": o.get("team_objective_id")} for o in mi.get("objectives", [])
                            if o.get("destroyed_time_s")]
    digest["mid_boss"] = [{"t": mmss(b["destroyed_time_s"]), "claimed_by_team": b.get("team_claimed")}
                          for b in (mi.get("mid_boss") or []) if b.get("destroyed_time_s")]
    return digest

# ---- cli (used by fetch.py) -------------------------------------------------
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--match"); ap.add_argument("--file"); ap.add_argument("--account", type=int)
    ap.add_argument("--latest", action="store_true"); ap.add_argument("--me", type=int)
    ap.add_argument("--out", default="."); ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    item_by_id, hero_by_id = load_names(refresh=a.refresh)
    if a.latest:
        if not a.account: ap.error("--latest needs --account")
        a.match = str(latest_match_id(a.account))
    match = load_match(a.match, a.file, a.out)
    me_acc = a.me or a.account or 0
    d = build_digest(match, item_by_id, hero_by_id, me_acc)
    Path(a.out, f'{d["match_id"]}_digest.json').write_text(json.dumps(d, indent=1))
    print(json.dumps({"match_id": d["match_id"], "my_hero": d["my_hero"],
                      "i_won": d["i_won"], "focus_enemies": d["focus_enemies"]}, indent=1))
