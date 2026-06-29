# Automation: keeping the watcher running

`scripts/watch.py` detects new matches on the account and builds a report for each. Run it either as
a long-lived daemon (`--interval`) or as a one-shot (`--once`) on a schedule. One-shot on a schedule
is the more robust choice on a laptop that sleeps.

First run is safe: by default it marks your existing match history as already-seen and does nothing,
so it will not reprocess your whole history. Use `--backfill N` on the first run to also build
reports for your N most recent matches.

## Prerequisites

- Python 3 and Plotly (`pip install plotly`).
- For the default (full analysis) mode: Claude Code installed and authenticated, with the
  deadlock-match-report skill installed, and the `claude` binary on PATH (or pass `--claude`).
- For `--no-llm` mode (data dashboard only, no written analysis): just Python and Plotly.

Note that each full report makes an LLM run in Claude Code, which uses tokens. Build a few reports
manually first to confirm you are happy with the output and the cost before leaving it on a timer.

## macOS (launchd, recommended on macOS Tahoe)

Create `~/Library/LaunchAgents/gg.deadlock.watch.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>gg.deadlock.watch</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/ABSOLUTE/PATH/TO/deadlock-match-report/scripts/watch.py</string>
    <string>--account</string><string>79761855</string>
    <string>--out-root</string><string>/Users/YOU/deadlock-reports</string>
    <string>--once</string>
    <string>--open</string>
  </array>
  <key>StartInterval</key><integer>300</integer>
  <key>StandardOutPath</key><string>/tmp/deadlock-watch.log</string>
  <key>StandardErrorPath</key><string>/tmp/deadlock-watch.err</string>
</dict></plist>
```

Then `launchctl load ~/Library/LaunchAgents/gg.deadlock.watch.plist`. It runs every 5 minutes,
builds reports for new matches, and opens them. Unload with `launchctl unload ...`.

## Linux (cron)

```
*/5 * * * * /usr/bin/python3 /path/to/deadlock-match-report/scripts/watch.py --account 79761855 --out-root ~/deadlock-reports --once >> /tmp/deadlock-watch.log 2>&1
```

## Linux (systemd timer)

A `deadlock-watch.service` (Type=oneshot running watch.py with `--once`) plus a
`deadlock-watch.timer` with `OnUnitActiveSec=5min` works well and survives reboots.

## Windows (Task Scheduler)

Create a Basic Task that runs `python.exe C:\path\to\watch.py --account 79761855 --out-root %USERPROFILE%\deadlock-reports --once` on a 5-minute repeat trigger.

## Where reports go

Each match gets `OUT_ROOT/<match_id>/<match_id>_report.html` plus its digest and analysis JSON. Open
the HTML in any browser — but serve it over `http://` (e.g. `python3 -m http.server 8000 --directory
OUT_ROOT/<match_id>`) so the Deadlock UI item cards load; over `file://` the charts and text still
render but the cards do not. The processed-match list lives in `OUT_ROOT/.seen_<account>.json`; delete
it to reprocess from scratch.
