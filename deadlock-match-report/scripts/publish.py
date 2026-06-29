#!/usr/bin/env python3
"""
publish.py - assemble the static Deadcoach website into the repo's docs/ folder for GitHub Pages.

For each match it copies the generated report to docs/<match_id>/index.html (clean URL), builds
docs/matches.json (a manifest with NO account id), regenerates docs/index.html (the homepage), and
writes docs/robots.txt (keeps the site out of search engines). With --push it commits and pushes
docs/ so GitHub Pages updates.

Usage:
  # publish specific matches:
  python3 scripts/publish.py --ids 91282802,90475136 [--push]
  # or publish every report found under the reports root:
  python3 scripts/publish.py --all [--push]
"""
import argparse, datetime, json, os, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dl_lib as L
import homepage as H

REPO = Path(__file__).resolve().parents[2]          # .../deadcoach
DEFAULT_DOCS = REPO / "docs"
DEFAULT_REPORTS = Path(os.environ.get("DL_OUT_ROOT", Path.home() / "deadlock-reports"))
DEFAULT_ACCOUNT = int(os.environ.get("DL_ACCOUNT", "79761855"))

ROBOTS = "User-agent: *\nDisallow: /\n"


def _me(digest):
    return next((p for p in digest["players"] if p.get("is_me")), {})


def manifest_entry(digest, start_time):
    """Tile metadata for the homepage. Deliberately excludes the numeric account id."""
    me = _me(digest)
    mid = digest.get("match_id")
    date = datetime.date.fromtimestamp(start_time).isoformat() if start_time else ""
    return {
        "match_id": mid,
        "hero": digest.get("my_hero"),
        "hero_image": digest.get("my_hero_image"),
        "won": digest.get("i_won"),
        "kda": me.get("kda"),
        "net_worth": me.get("net_worth"),
        "souls_per_min": me.get("souls_per_min"),
        "duration": digest.get("duration"),
        "duration_s": digest.get("duration_s"),
        "start_time": start_time,
        "date": date,
        "focus_enemies": digest.get("focus_enemies"),
        "url": f"{mid}/",
    }


def discover_ids(reports_root):
    ids = []
    for d in sorted(Path(reports_root).glob("*")):
        if d.is_dir() and (d / f"{d.name}_report.html").exists():
            ids.append(d.name)
    return ids


def publish(ids, reports_root, docs, account, title="Deadcoach"):
    docs = Path(docs)
    docs.mkdir(parents=True, exist_ok=True)
    # dates from match history (best effort; tolerate API/offline failure)
    starts = {}
    try:
        starts = {str(h["match_id"]): h.get("start_time") for h in L.match_history(account)}
    except Exception as e:
        print("warning: could not fetch match history for dates:", e)

    manifest = []
    for mid in ids:
        mid = str(mid)
        src_dir = Path(reports_root) / mid
        report = src_dir / f"{mid}_report.html"
        digest_f = src_dir / f"{mid}_digest.json"
        if not report.exists() or not digest_f.exists():
            print(f"skip {mid}: missing report or digest")
            continue
        out_dir = docs / mid
        out_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(report, out_dir / "index.html")
        digest = json.loads(digest_f.read_text())
        manifest.append(manifest_entry(digest, starts.get(mid)))
        print(f"published {mid} -> docs/{mid}/index.html")

    manifest.sort(key=lambda m: m.get("start_time") or m.get("match_id") or 0, reverse=True)
    (docs / "matches.json").write_text(json.dumps(manifest, indent=1))
    (docs / "index.html").write_text(H.build_homepage(manifest, title=title))
    (docs / "robots.txt").write_text(ROBOTS)
    print(f"homepage built with {len(manifest)} matches -> docs/index.html")
    return manifest


def git_push(docs, n):
    subprocess.run(["git", "-C", str(REPO), "add", str(Path(docs))], check=True)
    msg = f"Publish site: {n} match report(s) to docs/"
    r = subprocess.run(["git", "-C", str(REPO), "commit", "-m", msg])
    if r.returncode != 0:
        print("nothing to commit (site unchanged)")
        return
    subprocess.run(["git", "-C", str(REPO), "push", "origin", "main"], check=True)
    print("pushed docs/ to origin/main")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", help="comma-separated match ids to publish")
    ap.add_argument("--all", action="store_true", help="publish every report under the reports root")
    ap.add_argument("--reports-root", default=str(DEFAULT_REPORTS))
    ap.add_argument("--docs", default=str(DEFAULT_DOCS))
    ap.add_argument("--account", type=int, default=DEFAULT_ACCOUNT)
    ap.add_argument("--title", default="Deadcoach")
    ap.add_argument("--push", action="store_true")
    a = ap.parse_args()
    if a.all or not a.ids:
        ids = discover_ids(a.reports_root)
    else:
        ids = [s.strip() for s in a.ids.split(",") if s.strip()]
    if not ids:
        ap.error("no matches to publish (use --ids or --all with existing reports)")
    manifest = publish(ids, a.reports_root, a.docs, a.account, title=a.title)
    if a.push:
        git_push(a.docs, len(manifest))
