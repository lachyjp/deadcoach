#!/usr/bin/env python3
"""
watch.py - watch your account for new matches and build a report for each one automatically.

How it works: poll the player match-history endpoint, remember which match ids you've already
processed, and for every new one invoke Claude Code headless (`claude -p ...`) pointing at the
deadlock-match-report skill. Claude then runs the full pipeline (fetch -> meta -> analysis ->
dashboard) and writes an interactive HTML report into that match's folder.

Run as a loop, or with --once from cron / a launchd timer (see references/automation.md).

  python3 watch.py --account 79761855 --out-root ~/deadlock-reports --once
  python3 watch.py --account 79761855 --out-root ~/deadlock-reports --interval 180   # daemon

Flags:
  --no-llm   skip Claude and build a data-only dashboard directly with python (no written
             analysis). Useful for testing the watcher without spending tokens.
  --open     open each finished report in the default browser.
  --claude   path to the claude binary (default: "claude"). Claude Code must be installed and
             authenticated, and the deadlock-match-report skill installed, for the default mode.
"""
import argparse, json, os, subprocess, sys, time, webbrowser
import functools, threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# lazily-started local HTTP server so the Deadlock UI item cards load (they are ESM
# modules + cross-origin asset fetches, which browsers block on file://).
_httpd = None
def ensure_server(root):
    global _httpd
    if _httpd is None:
        handler = functools.partial(SimpleHTTPRequestHandler, directory=str(root))
        _httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=_httpd.serve_forever, daemon=True).start()
    return _httpd.server_address[1]
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dl_lib as L

def seen_path(out_root, acc):
    return Path(out_root) / f".seen_{acc}.json"

def load_seen(out_root, acc):
    p = seen_path(out_root, acc)
    return set(json.loads(p.read_text())) if p.exists() else set()

def save_seen(out_root, acc, seen):
    seen_path(out_root, acc).write_text(json.dumps(sorted(seen)))

BRAWL_GAME_MODE = 4  # Street Brawl (short ~5-15 min mode with inflated souls); 1 = standard Deadlock

def new_matches(acc, seen, ranked_only, include_brawl=False):
    hist = L.match_history(acc)
    ids = []
    skipped_brawl = 0
    for h in hist:
        if h["match_id"] in seen:
            continue
        if not include_brawl and h.get("game_mode") == BRAWL_GAME_MODE:
            skipped_brawl += 1
            continue
        if ranked_only and h.get("match_mode") not in (1, 4):  # 1 unranked? 4 ranked - keep both by default
            pass
        ids.append(h["match_id"])
    if skipped_brawl:
        print(f"skipping {skipped_brawl} Street Brawl match(es) (use --include-brawl to report them)")
    return sorted(ids)   # oldest first

CLAUDE_PROMPT = (
    "Use the deadlock-match-report skill to produce the interactive HTML match report for "
    "Deadlock match {mid}. My account id is {acc}. Save all outputs into the current working "
    "directory and finish by writing {mid}_report.html. Do the full analysis: fetch the match, "
    "pull current item meta for me and the enemies who beat me, write analysis.json, then build "
    "the dashboard."
)

def run_with_claude(claude, skill_dir, mid, acc, out_dir):
    prompt = CLAUDE_PROMPT.format(mid=mid, acc=acc)
    env = dict(os.environ, DL_SKILL_DIR=str(skill_dir))
    # --dangerously-skip-permissions keeps it non-interactive for unattended runs
    cmd = [claude, "-p", prompt, "--dangerously-skip-permissions"]
    print(f"  -> invoking claude for match {mid} in {out_dir}")
    return subprocess.run(cmd, cwd=out_dir, env=env).returncode == 0

def run_data_only(skill_dir, mid, acc, out_dir):
    import dashboard as D
    item_by_id, hero_by_id = L.load_names()
    match = L.load_match(str(mid), None, str(out_dir))
    digest = L.build_digest(match, item_by_id, hero_by_id, acc)
    dpath = Path(out_dir) / f"{mid}_digest.json"
    dpath.write_text(json.dumps(digest, indent=1))
    out = Path(out_dir) / f"{mid}_report.html"
    out.write_text(D.build(digest, None))
    print(f"  -> data-only report written: {out}")
    return True

def process(mid, acc, out_root, args, skill_dir):
    out_dir = Path(out_root) / str(mid)
    out_dir.mkdir(parents=True, exist_ok=True)
    ok = (run_data_only(skill_dir, mid, acc, out_dir) if args.no_llm
          else run_with_claude(args.claude, skill_dir, mid, acc, out_dir))
    report = out_dir / f"{mid}_report.html"
    if ok and args.open and report.exists():
        port = ensure_server(out_root)
        webbrowser.open(f"http://127.0.0.1:{port}/{mid}/{mid}_report.html")
    if ok and getattr(args, "publish", False) and report.exists():
        try:
            import publish as P
            ids = P.discover_ids(out_root)
            P.publish(ids, out_root, P.DEFAULT_DOCS, acc)
            P.git_push(P.DEFAULT_DOCS, len(ids))
        except Exception as e:
            print(f"  -> publish failed: {e}")
    return ok

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", type=int, default=int(os.environ.get("DL_ACCOUNT", "79761855")))
    ap.add_argument("--out-root", default=os.environ.get("DL_OUT_ROOT", str(Path.home() / "deadlock-reports")))
    ap.add_argument("--skill-dir", default=os.environ.get("DL_SKILL_DIR", str(Path(__file__).resolve().parent.parent)))
    ap.add_argument("--claude", default=os.environ.get("DL_CLAUDE", "claude"))
    ap.add_argument("--interval", type=int, default=180)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--open", action="store_true")
    ap.add_argument("--serve-seconds", type=int, default=25,
                    help="with --once --open, keep the local server up this long so the browser can "
                         "load the item cards, then exit (0 = stay up until Ctrl-C)")
    ap.add_argument("--ranked-only", action="store_true")
    ap.add_argument("--include-brawl", action="store_true",
                    help="also build reports for Street Brawl games (skipped by default)")
    ap.add_argument("--publish", action="store_true",
                    help="after building a new report, publish the whole site to docs/ and push (GitHub Pages)")
    ap.add_argument("--backfill", type=int, default=0,
                    help="on first run, process the N most recent matches (default 0: just mark them seen)")
    args = ap.parse_args()
    Path(args.out_root).mkdir(parents=True, exist_ok=True)
    first_run = not seen_path(args.out_root, args.account).exists()

    def tick():
        seen = load_seen(args.out_root, args.account)
        nonlocal first_run
        fresh = new_matches(args.account, seen, args.ranked_only, args.include_brawl)
        if first_run and args.backfill >= 0:
            # don't reprocess full history on first run; optionally backfill the newest N
            to_do = fresh[-args.backfill:] if args.backfill else []
            seen |= set(fresh) - set(to_do)
            save_seen(args.out_root, args.account, seen)
            fresh = to_do
            first_run = False
        for mid in fresh:
            print(f"new match: {mid}")
            process(mid, args.account, args.out_root, args, args.skill_dir)
            seen.add(mid)
            save_seen(args.out_root, args.account, seen)
        if not fresh:
            print("no new matches")

    if args.once:
        tick()
        if args.open and _httpd is not None:
            port = _httpd.server_address[1]
            if args.serve_seconds and args.serve_seconds > 0:
                print(f"serving reports at http://127.0.0.1:{port}/ for {args.serve_seconds}s.")
                time.sleep(args.serve_seconds)
            else:
                print(f"serving reports at http://127.0.0.1:{port}/ — Ctrl-C to stop.")
                try:
                    threading.Event().wait()
                except KeyboardInterrupt:
                    print("\nstopped.")
    else:
        print(f"watching account {args.account} every {args.interval}s. Ctrl-C to stop.")
        while True:
            try:
                tick(); time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\nstopped."); break
            except Exception as e:
                print(f"poll error: {e}; retrying next interval"); time.sleep(args.interval)

if __name__ == "__main__":
    main()
