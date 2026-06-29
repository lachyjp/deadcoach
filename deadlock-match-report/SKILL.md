---
name: deadlock-match-report
description: >-
  Turn a completed Deadlock match into an in-depth interactive HTML coaching dashboard. Use this
  skill whenever the user mentions a Deadlock match or match id, asks to analyse/review their
  Deadlock game or performance, wants to know what they did well or could have done better, asks
  about their item build or who they should have targeted, or wants to set up automatic match
  reports or watch their account for new matches. It analyses every phase (laning, early-mid, mid,
  late) across economy, combat, survivability, itemisation, target selection and macro, going deep
  on the user and the enemies who beat them, grounds item advice in current win-rate data, and is
  honest about what the data cannot show. Trigger it even if the user just pastes a Deadlock match
  id or says "review my last game".
---

# Deadlock match report

Produce an interactive HTML dashboard that coaches the user on one Deadlock match. The pipeline is:
fetch the match, derive a phase-segmented digest, pull current item meta, write the analysis, and
build the dashboard. The scripts do the deterministic work; you (the model) write the analysis.

Default account id is **79761855** unless the user gives another. All scripts are standard-library
Python except the charts, which need Plotly.

## Setup (once per run)

1. Ensure Plotly is available: `pip install plotly --break-system-packages -q` (or in the user's env).
2. Work from the skill's `scripts/` directory, or call scripts by path (Python puts the script's own
   folder on the import path, so the cross-imports resolve). Write outputs into the current working
   directory.

## Workflow

### 1. Resolve the match id
- If the user gave a match id, use it.
- Otherwise fetch the newest match for the account:
  `python3 scripts/dl_lib.py --latest --account <ACCOUNT> --out .` (this also builds the digest).

### 2. Fetch and build the digest
`python3 scripts/dl_lib.py --match <MATCH_ID> --me <ACCOUNT> --out .`
- Writes `<MATCH_ID>_digest.json` and caches the raw match + name tables.
- If the match is not found, it may not be ingested yet; tell the user to open it on a tracker
  (e.g. tracklock.gg) to trigger ingestion, then retry. Add `--refresh` occasionally to update the
  item/hero name tables after a patch.

### 3. Read the digest
Open `<MATCH_ID>_digest.json`. Note `my_hero`, `i_won`, `duration`, `avg_badge`, and `focus_enemies`
(the enemies who beat the user). Map `my_hero` and each focus-enemy hero name to its numeric id using
the cached heroes table at `~/.cache/deadlock/heroes.json` (or `$DL_CACHE/heroes.json`).

### 4. Pull current item meta
Query live win rates for the user's hero and the focus enemies, filtered to the lobby's rank band and
a recent window:
`python3 scripts/meta.py --heroes <MY_ID,ENEMY_IDS> --min-badge <avg-6> --max-badge <avg+6> --days 30 --out meta.json`
- Use the match's `avg_badge` to set the band (a few points either side). If you are unsure of the
  badge scale, omit `--min-badge`/`--max-badge` to query all ranks.
- If the API is unreachable and `meta.json` comes back empty, proceed using the durable picks in
  `references/item-catalog.md` and say suggestions are based on general principles, not live data.

### 5. Read the references you need
- Always: `references/analysis-framework.md` (how to write the analysis) and
  `references/reading-the-data.md` (what every field means and its caveats).
- `references/hero-profiles.md` for the user's hero and the focus enemies.
- `references/item-catalog.md` for itemisation reasoning, and `references/deadlock-meta.md` for
  economy benchmarks, objectives, and macro.

### 6. Write the analysis
Write `analysis.json` following `assets/analysis_schema.md`. Follow the framework:
- Fill the grid: every phase that exists, every relevant category, using the trichotomy
  (**Did well / Hard to say / Cost you**) plus a one-line **Blind spots** note per category.
- Ground every claim in a digest number or a named meta fact. Be specific and constructive; you are
  coaching an amateur. Keep each point to one or two sentences.
- Per-phase `item_suggestions`: tie them to the gap the phase revealed, the hero's kit/role, and the
  live `meta.json` (prefer strong current win rates; surface one or two `underrated` picks when they
  fit, since the user wants obscure meta). Only name items that exist; set `instead_of` to a real
  item they bought when proposing a swap.
- `targeting_overall`: compare `damage_dealt_to` vs `damage_taken_from` and enemy net worth; name the
  classic "damaged the tank, ignored the carry" error when it applies.
- `focus_enemy_notes`: one note per focus enemy, with a concrete counter (item or positioning).
- `overall.verdict`: one paragraph with the real story and headline numbers.
- `overall.priorities`: exactly three, ordered by impact, actionable next game.
Validate that `analysis.json` is valid JSON with exact phase/category keys before continuing.

### 7. Build the dashboard
`python3 scripts/dashboard.py --digest <MATCH_ID>_digest.json --analysis analysis.json --out <MATCH_ID>_report.html`
- Self-contained HTML with seven interactive charts and all the written sections.
- The report wears Deadlock's "Brass HUD" skin — 1930s noir Art Deco, aged brass/gold on deep
  teal-black, condensed deco display type (Big Shoulders Display) + clean sans body (Barlow), with
  corner-bracket framing and the game's category colour coding (Weapon amber / Vitality green /
  Spirit violet, souls cyan). It uses Google Fonts + the Plotly CDN, so it looks best online.
- **Builds section + Deadlock UI item cards.** The report loads the official `@deadlock-api/ui-core`
  web components (`<dl-provider>` + `<dl-item-card>`, from the unpkg CDN) and uses them everywhere an
  item is shown: a dedicated **Builds** section (your final build + collapsible "the builds that beat
  you" for each enemy who killed you / the focus enemies) and the per-phase item suggestions. Cards
  pull live icons, tier badges and hover tooltips from `assets.deadlock-api.com` by item id. The
  digest carries the ids: `final_build_items[].id` (every player) and `item_index[name].id` (any item
  the analysis names). When an item name has no resolvable id (e.g. an `instead_of` not in the digest)
  the chip degrades to a styled placeholder, so the report never breaks.
- Hero portraits still come from `dl_lib`'s `my_hero_image`/per-player `hero_image` URLs.
- **Serve over HTTP to view.** Because the UI components are ESM modules and fetch assets
  cross-origin, they are blocked on `file://`. Serve the output directory and open it over `http://`,
  e.g. `python3 -m http.server 8000 --directory <DIR>` then open
  `http://localhost:8000/<MATCH_ID>_report.html`. (Charts/scoreboard/text still render from `file://`;
  only the item cards need the server.)
- **Dependency:** charts require `plotly` (`python3 -m pip install plotly`).

### 8. Deliver
Serve the report over HTTP and give the user the link (the item cards need `http://`, see step 7),
e.g. `python3 -m http.server 8000 --directory <DIR>` → `http://localhost:8000/<MATCH_ID>_report.html`.
Opening the file directly (`open` / `xdg-open`) still works for everything except the item cards.
Summarise the three priorities in chat. If `present_files` is available, present the HTML.

## Automatic mode (watch the account)

The user wants new matches analysed automatically. `scripts/watch.py` polls the account and runs this
skill for each new match via Claude Code headless:
- One-shot (for cron / launchd): `python3 scripts/watch.py --account <ACCOUNT> --out-root <DIR> --once --open`
- Daemon: `python3 scripts/watch.py --account <ACCOUNT> --out-root <DIR> --interval 180`
- `--no-llm` builds a data-only dashboard (charts + scoreboard, no written analysis) without an LLM
  call, which is good for testing the watcher cheaply.
First run marks existing history as seen (use `--backfill N` to also do the newest N). See
`references/automation.md` for launchd/cron/systemd setup. Tell the user that full reports use tokens
via Claude Code, so they should build a few manually first to confirm output and cost.

## Files
- `scripts/dl_lib.py` core: API access, name joining, asset image URLs, digest (phases, damage matrix, deaths)
- `scripts/charts.py` seven Plotly charts from the digest (Brass HUD palette)
- `scripts/dashboard.py` assembles the HTML report (Brass HUD skin)
- `scripts/meta.py` current per-hero item win rates
- `scripts/watch.py` the auto-watcher
- `references/` the analysis framework, data field guide, hero profiles, item catalog, meta, automation
- `assets/analysis_schema.md` the exact analysis.json schema
