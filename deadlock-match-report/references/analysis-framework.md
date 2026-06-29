# Analysis framework

This is how to turn a digest into the written analysis. The goal is many small, honest, specific
judgements rather than one vague summary. You are coaching an amateur, so every claim must be
grounded in a number from the digest or a named meta fact, and you must be clear about what the
data cannot tell you.

## The grid

Analyse every phase against every category. That naturally produces dozens of focused notes.

Phases (the digest segments the data this way; windows are clock-based and approximate because
real phases also depend on game-state):
- **Laning** 0 to 10 min
- **Early-mid** 10 to 18 min
- **Mid** 18 to 28 min
- **Late** 28 min onward

Categories, in each phase:
- **Economy** souls per minute, last hits, denies, soul sources, lost-on-death
- **Combat** hero damage dealt vs taken, accuracy, kills and assists, fight participation
- **Survivability** deaths, how fast you were bursted (focused_s), time spent dead (down_s)
- **Itemisation** what you bought and when, versus what the hero and matchup wanted
- **Targeting** who you damaged versus who you should have (use the damage matrix)
- **Macro** objectives, mid-boss, map position of deaths, grouping versus splitting

## The trichotomy (use exactly these three buckets, plus blind spots)

For every category in every phase, sort observations into:
- **Did well** clearly good, supported by the numbers. Praise it specifically.
- **Hard to say** genuinely ambiguous, context-dependent, or where the metric is noisy. This bucket
  is not a hedge to avoid judgement; it is for things the data raises but cannot settle (e.g.
  accuracy includes spray on creeps, farming while behind can be right or wrong). Use it honestly.
- **Cost you** clearly suboptimal and supported by the numbers. Be direct but constructive, and say
  what to do instead.
- **Blind spots** one short line naming what the data cannot reveal for this category (comms,
  intent, whether a death was a planned sacrifice, what the team was doing off-screen). Never
  pretend the data is the whole story.

Each bucket can be a single string or a list of short strings. Omit a bucket if you have nothing
honest to put in it. Omit a whole category in a phase only if there is genuinely nothing to say
(e.g. targeting in laning is mostly creep last-hits, which the per-target matrix does not isolate).

Keep each point to one or two sentences. Concrete and kind. Avoid generic advice that would apply
to any match ("play better", "farm more") unless you tie it to a specific number.

## Item suggestions per phase

For each phase, give a short list of item suggestions: `{item, why, instead_of}`. Ground them in:
1. The hero's role and kit (see hero-profiles.md) and the matchup (the enemies in this match).
2. The live meta in meta.json: prefer items with a strong current win rate for this hero, and
   surface one or two from the `underrated` list when they fit, since the user wants obscure picks.
3. The actual gap this phase revealed (no armour, no mobility, wrong damage type, no anti-heal).
Set `instead_of` to a specific item they bought when you are proposing a swap, else null.

Do not invent items. Only name items that exist in the name cache / meta.json. If meta.json is
empty (API was unreachable), fall back to the durable picks in item-catalog.md and say the
suggestion is based on general principles rather than current win rates.

## Targeting (overall) and focus enemies

- `targeting_overall`: compare `damage_dealt_to` against `damage_taken_from` and the enemies' net
  worth. The classic mistake is pouring damage into a tank while the fed carry is the real threat.
  Tie the advice to the hero's kit (e.g. Warden's Flask plus Binding Word is built to lock one
  squishy, so it should be aimed at the carry).
- `focus_enemy_notes`: one note per enemy in `focus_enemies` (the ones who beat them). Say why they
  were a problem (kills on you, net worth, damage to you) and the concrete answer (an item counter,
  a positioning change). Use named counters from item-catalog.md and hero-profiles.md.

## Overall verdict and priorities

- `verdict`: one tight paragraph. Lead with the real story of the game (often it is not "you
  farmed badly"; it is survivability, itemisation, or targeting). Use the headline numbers.
- `priorities`: exactly three, ordered by impact, each actionable next game. These should be the
  three things that, if changed, most change the result. Make them specific to this match.

## Output

Write the analysis to `analysis.json` following `assets/analysis_schema.md` exactly. The dashboard
renders only the fields that are present, so partial sections are fine, but aim to fill the grid.
