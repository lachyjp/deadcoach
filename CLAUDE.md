# Deadcoach — project guide for Claude

Deadcoach turns a finished **Deadlock** match into an interactive HTML **coaching report**, and
publishes a set of those reports as a small **website** (homepage + per-match pages) on GitHub Pages.

## Working with this user (read first)
- **The user is a designer, not an engineer.** Explain changes in plain, visual language — lead with
  *what they'll see on screen*, not code internals. Avoid jargon; when you must use it, define it.
- In **plan mode** and proposals, describe the visible/UX outcome first.
- **Always end every chat with a short "What changed in the UI" recap** — a few bullets the user can
  open the report/site and verify themselves (which section, what's new, where to look). This is a
  standing expectation for this project.
- Before anything **public/outward-facing** (pushing, going live, publishing), confirm first.

## What it produces
- A per-match report (Brass HUD skin) with sections: **Overview, Charts, phase breakdowns
  (Laning/Early-mid/Mid/Late), Builds, Targeting, Deaths (map + timeline), Playbook, Scoreboard.**
- A **homepage** (`docs/index.html`) listing matches as tiles with an overall stats strip.
- Live at `https://lachyjp.github.io/deadcoach/` (GitHub Pages, served from `/docs` on `main`).
  Public by link but **noindexed** (robots.txt + meta) so search engines don't list it.

## Architecture / data flow
`deadlock-match-report/` is a Claude **skill** (`SKILL.md`) plus scripts:
- `scripts/dl_lib.py` — fetches match data + assets from deadlock-api, builds the **digest** JSON
  (per-player stats, phases, damage matrix, deaths w/ positions + killer pos + dmg window, kills,
  item builds, `map` image+radius). Also `load_names`, `hero_images`, `load_map`, `match_history`.
- `scripts/meta.py` — current per-hero item win-rate meta → `meta.json`.
- `scripts/dashboard.py` — renders the report HTML from `digest.json` + `analysis.json`.
- `scripts/charts.py` — the seven Plotly charts.
- `scripts/homepage.py` — builds the site homepage from a matches manifest.
- `scripts/publish.py` — assembles `docs/` (copies reports to `docs/<id>/index.html`, writes
  `matches.json`, homepage, `robots.txt`); `--push` commits+pushes.
- `scripts/watch.py` — polls the account for new matches and runs the pipeline per match;
  `--publish` makes new games go live automatically; skips Street Brawl (`game_mode=4`) by default.
- `assets/analysis_schema.md` — the exact shape of `analysis.json` (the written coaching that the
  model produces); `references/` — how to analyse, read the data, hero/item/meta knowledge.

Pipeline per match: **fetch → digest → (write analysis.json) → dashboard → report → publish to docs/.**
Data-only mode (`--no-llm`) skips the written analysis but still renders charts/map/builds/scoreboard.

## Generating / publishing (commands)
- One report: `python3 scripts/dl_lib.py --match <id> --me <acct> --out ~/deadlock-reports/<id>`
  then `python3 scripts/dashboard.py --digest ..._digest.json --analysis analysis.json --out ..._report.html`.
- Publish the site: `python3 scripts/publish.py --all --push` (or `--ids a,b,c`).
- View locally over HTTP (required — see gotchas): `python3 -m http.server --directory docs`.

## Conventions & gotchas
- **Brass HUD** visual identity: 1930s Art Deco brass/gold on teal-black; Big Shoulders Display +
  Barlow fonts; category colours weapon=amber, spirit=violet, vitality=green, souls=cyan.
- **Reports must be served over http(s), not file://** — the `@deadlock-api/ui-core` item cards and
  the minimap fetch cross-origin and are blocked on file://. Pages (https) is fine.
- **Python 3.9** here: no nested same-quote f-strings; build such strings with `.format()` or temps.
- `rich(text, digest)` in dashboard.py **auto-embeds** item icons + hero avatars wherever an item or
  hero name appears in prose. Item names must match the catalog (a normaliser handles spelling/
  "Improved"/"(imbued)" variants).
- Deaths map projects world `(x, y)` onto the minimap using `radius` (10752) from `/v1/map`;
  calibration constants `MAP_FLIP_X/Y` in dashboard.py.
- **Privacy**: the site is public-but-noindexed; never surface the raw numeric **account id** in
  published output (the manifest and tiles deliberately omit it).
- `plotly` is required for charts (`pip install plotly`).
- Automation: scheduled task **deadlock-match-report-watch** runs the watcher; the skill is symlinked
  at `~/.claude/skills/deadlock-match-report`. Reports/output live under `~/deadlock-reports/`.
