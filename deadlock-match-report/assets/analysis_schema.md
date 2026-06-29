# analysis.json schema

The analysis step writes this file; `dashboard.py` renders it. The dashboard only renders fields that
are present, so partial output is safe, but aim to fill the grid (see references/analysis-framework.md).

## Shape

```json
{
  "overall": {
    "verdict": "one tight paragraph: the real story of the game, using headline numbers",
    "priorities": ["priority 1", "priority 2", "priority 3"]
  },
  "phases": {
    "Laning":    { "summary": "...", "categories": { ... }, "item_suggestions": [ ... ] },
    "Early-mid": { "summary": "...", "categories": { ... }, "item_suggestions": [ ... ] },
    "Mid":       { "summary": "...", "categories": { ... }, "item_suggestions": [ ... ] },
    "Late":      { "summary": "...", "categories": { ... }, "item_suggestions": [ ... ] }
  },
  "targeting_overall": "one paragraph comparing who you damaged vs who beat you",
  "focus_enemy_notes": { "HeroName": "why they were a problem and the concrete answer" },
  "hero_guide": {
    "overview": "one paragraph on the user's hero identity / win condition, tied to this match",
    "situations": [ { "situation": "short label", "advice": "what to do, referencing a match number" } ]
  },
  "macro_tips": [ "macro recommendation grounded in this match's objectives/timings/deaths" ],
  "resources": [ { "title": "...", "url": "https://...", "kind": "video" | "article", "why": "why it's relevant to this player's gaps" } ]
}
```

- Phase keys must be exactly `Laning`, `Early-mid`, `Mid`, `Late`. Only include phases that exist in
  the digest (a short game may have no Late phase).
- `categories` keys must be exactly: `Economy`, `Combat`, `Survivability`, `Itemisation`,
  `Targeting`, `Macro`. Omit a category in a phase if there is genuinely nothing to say.
- Each category is an object with any of these buckets: `did_well`, `hard_to_say`, `cost_you`,
  `blind_spots`. Each bucket is **either a string or a list of short strings**. Omit empty buckets.
- `item_suggestions` is a list of `{ "item": "...", "why": "...", "instead_of": "..." | null }`.
- `focus_enemy_notes` keys are hero names from the digest's `focus_enemies`.
- `hero_guide`, `macro_tips`, `resources` are all optional and render in a "<Hero> playbook" section.
  Item and hero names anywhere in the prose are auto-embedded as inline icons, so spell them as they
  appear in the catalog. `macro_tips` should be concrete and match-grounded (objective timings,
  mid-boss, where deaths happened), not generic. `resources` must be **real, verified URLs** to
  highly-relevant guides/videos for this hero or the match's lessons — verify each link resolves
  (e.g. YouTube oEmbed) before including it, and the `why` should connect it to the player's actual
  gaps. Omit `resources` rather than guessing a URL.

## Minimal example (one phase, one category)

```json
{
  "overall": { "verdict": "Lost on survivability, not farm.", "priorities": ["Buy armour", "Stop dying late", "Focus the carry"] },
  "phases": {
    "Mid": {
      "summary": "Farm recovered but you got bursted in the enemy jungle.",
      "categories": {
        "Survivability": {
          "cost_you": ["Died at 26:10 in 9.6s deep on the enemy side, with no armour to soak it."],
          "blind_spots": "Can't tell if the team forced that fight."
        }
      },
      "item_suggestions": [
        { "item": "Improved Spirit Armour", "why": "Cuts the burst that was killing you.", "instead_of": "Blood Tribute" }
      ]
    }
  },
  "targeting_overall": "You dealt most damage to the tank while the carry farmed.",
  "focus_enemy_notes": { "Venator": "Killed you 3x from range; buy Knockdown." }
}
```

Validation before handing off: it must be valid JSON, phase and category keys must match exactly, and
every named item must be a real item (present in meta.json or the name cache).
