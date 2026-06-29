# Item catalog: roles, timing, and the items people skip

Item names, costs, and exact effects change between patches, and the live win rates in meta.json are
authoritative for what is strong right now. This file is the durable map: what categories of item
exist, when in the match they matter, and the high-value items amateurs most often skip. Use it to
reason about suggestions, and prefer naming a specific current item from meta.json or the name cache.

## The three slots and four tiers

Items are Weapon, Spirit, or Vitality, each in tiers 1 to 4 (cost rises with tier, roughly: T1 ~500,
T2 ~1,250 to 1,600, T3 ~3,000 to 3,500, T4 ~6,000+). You buy cheap components early and upgrade into
the expensive items as your souls grow. Higher tier is not automatically better; the right item for
the situation beats a pricier irrelevant one.

## By role and when it matters

**Early lane (T1, first 10 min):**
- Weapon: a velocity/accuracy item if your gun is slow (e.g. High-Velocity Rounds), Monster Rounds
  for farming and diving NPCs, Headshot Booster.
- Vitality: Extra Regen, Extra Stamina, Extra Health, early lifesteal to stay in a tough lane.
- Spirit: a cheap spirit/cooldown item if you are ability-based.
Goal: win or stabilise the lane and farm. Buy sustain if you are losing trades.

**Mid game (T2 to T3, ~10 to 25 min) — the make-or-break window:**
- **Armour (the most-skipped, highest-impact category):** Improved Bullet Armour (cuts weapon
  damage) and Improved Spirit Armour (cuts ability damage). Most heroes want both. Skipping armour is
  the number-one reason squishy builds die. If a build has none by ~15 to 20 minutes, that is a
  finding.
- Mobility: Fleetfoot, Enduring Speed, a movement/escape item. Lets you pick fights and leave bad
  ones.
- Weapon spikes: your hero's core damage upgrades (e.g. Headhunter), fire rate, ammo.
- Spirit spikes: cooldown, spirit power, range, an imbue item on a key ability.
- Sustain: Healing items, lifesteal, but watch self-damage items.

**Late game (T3 to T4, 25 min+):**
- Big defensive actives: Metal Skin (brief bullet-damage immunity), spirit equivalents, Unstoppable
  (CC immunity, vital for channelled ultimates and against CC-heavy teams).
- Damage payoff: T4 weapon or spirit capstones that fit your build.
- Whatever the fight needs: see counters below.

## Counter / situational items (buy in response to the enemy, not on autopilot)

- **Knockdown:** knocks airborne heroes (snipers like Venator, Grey Talon, Vindicta) out of the sky
  and interrupts; shuts off their damage in a fight.
- **Healbane / anti-heal:** against high-sustain enemies (Abrams, Infernus, supports). Reduces enemy
  healing so you can actually close kills.
- **Curse / silence:** locks a key target out of abilities and items briefly.
- **Debuff Remover / cleanse:** removes CC and debuffs from you; counters lockdown comps.
- **Unstoppable:** immune to CC for a window; lets you channel a windup ultimate or engage through a
  stun-heavy team.
- **Return Fire / reflect:** punishes gun-heavy attackers.
- **Slow / root items (e.g. a slowing hex):** stick to targets, set up your own CC.

## Self-damage and risk items

Some aggression/sustain items cost you health (e.g. health-draining or "tribute" items). Many of
these are **passives** whose benefit (bonus weapon/spirit power, lifesteal, regen) is baked into your
other damage and sustain — so their HP cost is **not wasted output**, it is the price of the buff.

**Read the digest's self-damage breakdown, not a raw total.** The digest now gives
`me.self_damage` (already **excludes regen/healing**), a per-source `me.self_damage_breakdown`, and
`me.self_heal` (your regen/sustain). Judge a self-damage item by:
- its share of the breakdown (don't blame one item for the whole figure — e.g. Blood Tribute is often
  a small slice), and
- whether it actually cost you fights: deaths where you were already low, self-damage large **relative
  to** your health pool and regen.
Only call self-damage a "cost you" point when the breakdown + deaths show it genuinely outweighed its
benefit on a squishy build — and say which item, with its real number. Do **not** treat self-damage as
pure waste, and account for `self_heal` before concluding.

## How to choose a suggestion

1. What gap did this phase reveal? (no armour, no mobility, wrong damage type, no anti-heal, no
   CC-immunity for a windup ult.)
2. Does the hero's kit and role want it? (see hero-profiles.md.)
3. Is it actually good right now? (meta.json win rate; surface an `underrated` pick if it fits.)
Name a specific current item, say why in one line, and set `instead_of` to what they should drop.
