# Hero profiles and build reading

Hero balance changes every patch, so pull current per-hero and per-item win rates from meta.json for
specifics. This file gives the durable reasoning: how to read a build, how archetypes work, and a
detailed profile for Warden (the user's main). For any hero not covered here, infer from the
archetype framework and lean on meta.json.

## Reading a build from the item split

Every item is Weapon (orange), Spirit (purple), or Vitality (green). The digest reports each
player's split, e.g. `W7 S3 V1`.

- **Weapon-heavy:** a gun build. Scales the basic attack. Wants accuracy, fire rate, ammo, headshots.
  Needs Vitality to survive, because gun heroes must stand and shoot.
- **Spirit-heavy:** an ability build. Scales the kit. Wants spirit power, cooldown, ability range.
- **Vitality:** survivability for everyone: health, regen, and crucially **armour**. Bullet Armour
  reduces weapon damage; Spirit Armour reduces ability damage. Most heroes want both by mid game.
- **The common amateur mistake:** going almost pure Weapon or pure Spirit with one Vitality item and
  no armour. It produces big damage on paper and a hero who dies in two seconds. A frontline hero
  with no armour is the clearest "cost you" itemisation finding there is.

A build should match the hero's job. A frontline initiator who builds like a glass-cannon carry is
mis-itemised even if the damage numbers look fine, because the team needs them to survive and create
space, not to die first.

## Archetypes (job on the team)

- **Frontline / initiator / bruiser:** starts fights, soaks damage, locks enemies down. Needs
  durability (armour, health, sustain) far more than raw damage. Warden, Abrams are examples.
- **Carry / damage dealer:** the win condition's damage. Often gun-based, needs protection and
  positioning. Snowballs with farm.
- **Backline / poke / sniper:** long-range damage from safety. Strong against immobile frontliners,
  weak to dive and to being knocked out of position. Venator, Grey Talon, Vindicta are examples.
- **Burst / assassin:** deletes a single target quickly. Lady Geist, Pocket-style threats. Countered
  by armour, by not being caught alone, and by spacing around their burst windows.
- **Support / utility:** healing, peel, zoning. Countered by anti-heal.

## Warden (the user's main) — detailed

Identity: a durable frontline initiator and peeler with strong single-target DPS once he locks
someone down. One of the tankiest heroes in the game when built correctly. A good urn/idol carrier
thanks to mid-game mobility.

Kit:
- **1 Alchemical Flask:** thrown AoE that damages, slows move speed, drains stamina, and reduces
  enemy weapon damage. Very low cooldown, so spam it to farm waves and camps, to win trades (the
  weapon-damage reduction makes enemies lose direct fights), and to set up Binding Word (the stamina
  drain removes their dash escape). Often the target of a Quicksilver Reload imbue (reload on cast).
- **2 Willpower:** a barrier plus bonus move speed for him and nearby allies. At tier 3 the barrier
  scales with Spirit Power, so spirit items make it much stronger. Pop it when you see enemy burst
  coming, and lead objectives with it up.
- **3 Binding Word:** curses an enemy; if they do not leave their spot in time they are rooted, and
  Warden deals bonus bullet damage to rooted targets. The delay can be dodged by good players, so
  land Flask (stamina drain) first, or use it as a follow-up to team CC. A rooted carry is a dead
  carry if the team follows up.
- **4 Last Stand (ultimate):** after a ~2s windup, pulses damage to enemies and heals Warden based on
  damage done, with greatly increased bullet and spirit resist while channelling. The windup is
  interruptible by CC, which is his biggest teamfight weakness (see Unstoppable). Open fights with
  it from cover, ideally trapping several enemies.

Strengths: durable frontline, layered CC, strong single-target DPS, good mobility mid game, good urn
carrier. Weaknesses: short range (struggles into long-range poke like Venator, Grey Talon, Vindicta),
hard CC during Last Stand windup, and his spirit damage alone is not enough (he wants weapon damage
plus the CC to convert).

Skill order: most builds put an early point in Alchemical Flask (wave clear, harass), then max one
of Binding Word (for 1v1 and lockdown) or Willpower (safer, and strong if building spirit) depending
on the game, with Last Stand taken whenever available. Both max orders are seen at high level.

Itemisation pattern (confirm current win rates in meta.json):
- **Opener:** High-Velocity Rounds first (fixes his slow bullet velocity so he can last-hit and
  deny), then Monster Rounds, plus an early sustain or regen pickup.
- **Weapon spikes:** Headshot Booster then Headhunter (his root guarantees headshots), and weapon
  items that fit (Crippling/Weakening Headshot, Weighted Shots, Berserker when taking damage).
- **Ability/utility:** Quicksilver Reload imbued on Flask, Mystic Burst, Slowing Hex, Duration items.
- **Defence (do not skip):** Improved Bullet Armour and Improved Spirit Armour are core by mid game.
  Metal Skin (brief bullet immunity) is excellent against gun-heavy enemies. Fortitude/health as
  needed.
- **Mobility:** Fleetfoot, Enduring Speed, Majestic Leap for roaming and disengaging.
- **Counters:** Unstoppable (channel Last Stand through CC), Knockdown (knock air snipers like
  Venator and Grey Talon out of the sky), Healbane (against healers and high-sustain enemies like
  Abrams or Infernus), Curse or Debuff Remover as the game demands.

If the user's Warden build is weapon-heavy with little or no armour, that is almost always the
headline itemisation problem, because his entire value proposition is surviving on the frontline.

## Common threats (infer the rest from archetypes + meta.json)

- **Venator, Grey Talon, Vindicta (air / long-range):** poke from safety, often airborne. Counter
  with Knockdown, and do not face-check their sightlines without armour or a gap-closer.
- **Lady Geist (burst):** high spirit and burst damage. Counter with Spirit Armour and by spacing
  around her burst rather than standing in it.
- **Abrams (bruiser, sustains):** durable and self-healing; do not dump your damage into him when a
  squishier carry is the real threat, and consider Healbane.
