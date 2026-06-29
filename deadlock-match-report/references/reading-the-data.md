# Reading the data: what the digest fields mean and what they cannot tell you

This is the backbone of honest analysis and of the "blind spots" buckets. Know exactly what each
number is, and where it misleads.

## Top level

- `i_won`, `winning_team`, `my_team`, `duration` — outcome and length.
- `avg_badge` — the rough rank of each team's lobby. Use it only to set expectations (a lower lobby
  forgives mistakes a higher one punishes). Do not over-interpret the exact number.
- `focus_enemies` — the enemies who beat the user, chosen as those who killed them at least twice,
  else the top two enemies by net worth. These get the deep treatment.
- `soul_lead_series` — `[time, your_team_souls minus enemy_souls]`. Positive means ahead. The single
  best macro signal. Swings mark fights and objectives.
- `networth_all` — net worth over time for all 12 players (for the chart).
- `objectives` — `[time, team, objective_id]` of structures destroyed. Tells you the map-pressure
  story but not why each fell.
- `mid_boss` — when the Rejuvenator/mid-boss was claimed and by which team. Uncontested enemy
  mid-bosses while behind are a macro red flag.

## Per-player block

- `kda`, `net_worth`, `souls_per_min`, `last_hits`, `denies`, `level`, `lane` — standard stats.
- `split` — count of Weapon/Spirit/Vitality items in the final build. The build's identity. See
  hero-profiles.md for reading it.
- `final_build` — the items kept at game end, with tier and slot.
- `kills_on_me` — how many times this enemy killed the user.

Deep players (the user + focus enemies) also have:
- `phases` — per-phase deltas from the sampled stat time series:
  - `net_worth`, `souls_per_min` — economy in that window.
  - `kills`/`deaths`/`assists` — from the stat samples (coarse). Prefer `deaths_actual` (computed
    from the exact death log) when counting deaths in a phase.
  - `player_damage` / `player_damage_taken` — hero damage dealt and taken in the window. If taken far
    exceeds dealt, the player was losing trades or had no mitigation.
  - `accuracy_pct` — shots hit / (hit + missed). **Caveat:** this counts every shot, including spray
    on creeps and at long range, so a low number is a flag, not proof of bad aim. Put the caveat in
    blind spots.
  - soul source fields (`gold_lane_creep`, `gold_neutral_creep`, `gold_boss`, `gold_denied`,
    `gold_death_loss`) — where souls came from and how many were lost on death.
  - `window` — the actual clock range the deltas cover.
- `purchase_timeline` — every upgrade bought, when, in which phase, and when sold. Lets you judge
  timing (e.g. armour bought too late, or never).
- `networth_series`, `dmg_series_dealt`, `dmg_series_taken` — time series for the charts.
- `damage_dealt_to` — total hero damage the user dealt to each **enemy** (self-damage and teammate
  damage are excluded). The core of targeting analysis.
- `self_damage` — damage the user dealt to themselves, **already excluding regen/healing**. Paired
  with `self_damage_breakdown` (per-source list, e.g. `[{name, amount}]`) and `self_heal` (total
  regen/sustain). Do not blame a single item for the whole figure — read the breakdown. Passive items
  (e.g. Blood Tribute) appear as their HP cost only; their power/regen benefit is in your other
  numbers, so the cost is not "wasted". Only a "cost you" point when the breakdown + deaths show it
  outweighed its benefit on a squishy build (name the item and its real number, and account for
  `self_heal`).
- `damage_taken_from` — total damage each **enemy** dealt to the user. The enemy at the top is the
  biggest threat to itemise and position against.
- `deaths` (user only) — each death with:
  - `t`, `phase` — when.
  - `killer` — who got the kill (the last hitter, not necessarily who did most of the work).
  - `focused_s` (time_to_kill) — how long the lethal sequence took. **Caveat:** a short value can
    mean a clean burst or simply that you were already low; a long value can be an extended losing
    fight you should have left. It is fight duration, not a pure burst metric.
  - `down_s` (death_duration) — seconds spent dead. This grows through the game, so late deaths cost
    far more uptime than early ones. Several late deaths is often the real reason a comeback failed.
  - `pos` — `[x, y, z]` world coordinates of the death. Plotted on the minimap in the report's
    Deaths section. Strongly negative coordinates are roughly the enemy side of the map; clusters of
    deaths deep on the enemy side while behind suggest overextension.
  - `killer_pos` — `[x, y]` where the killer stood at the moment of the kill (drawn as a line to the
    death spot — useful for spotting ganks from off-angle).
  - `dmg_window` — `{hero: damage}` taken from each enemy in the cumulative damage-matrix sample
    interval bracketing the death (~3-min samples). **Approximate**, not a precise last-few-seconds
    log; the `killer` is exact, this is the surrounding context.
- `kills` (user only) — each enemy kill you got, with `t`, `phase`, `victim`, and `pos` (where they
  died). Plotted as gold markers on the deaths map.
- `map` (digest top level) — `{image, radius}`: the minimap background image URL and the world
  radius used to project `(x, y)` coordinates onto it.

## What the data cannot tell you (always keep these in mind)

- **Communication and intent:** you cannot see voice comms, pings, or whether a death was a planned
  sacrifice (e.g. body-blocking, buying time for an objective).
- **What the team was doing off-screen:** a solo death might be a bad overextension or might be the
  player covering while the team took an objective elsewhere.
- **Cooldown and resource state:** you cannot see whether an ability or ultimate was available at the
  moment of a fight, which heavily affects what the right play was.
- **Inputs and mechanics:** missed skill-shots, dodged abilities, and movement quality are not in the
  data beyond coarse accuracy.
- **Why an item was bought or sold:** the timeline shows what and when, not the reasoning.

Whenever a judgement depends on one of these, put it in "hard to say" or name it in blind spots
rather than asserting it as fact.
