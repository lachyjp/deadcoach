# Deadlock meta: phases, economy, objectives, macro

Durable reasoning for reading a match. Specific numbers (item costs, exact objective timers, hero
balance) drift every patch, so treat the values here as ballparks and let the live data in
meta.json carry the current specifics. The current game has three lanes.

## The shape of a match

- **Laning (0 to ~10 min):** each player is assigned a lane and farms troopers (creeps). The core
  skills are last-hitting (shoot the trooper for the soul orb) and denying (shoot your own dying
  trooper so the enemy cannot get the orb, and secure your own orbs). Winning lane is mostly about
  out-farming and not dying, not about kills. Guardians (the first towers) protect each lane.
- **Early-mid (~10 to ~18 min):** lanes start to break, players begin roaming and jungling (neutral
  camps), and the first objectives fall. The Rejuvenator / mid-boss becomes contestable around the
  10-minute mark and grants a powerful team buff, so it is a major snowball point.
- **Mid (~18 to ~28 min):** teams group for objectives and fights. Walkers (second-tier defences)
  and shrines come down. Soul leads compound here.
- **Late (28 min onward):** death timers are long (often 60 to 90+ seconds), so a single death can
  mean your team fights a man down for over a minute. Throws happen here: a team that is ahead loses
  by taking a greedy fight, and a team that is behind loses by not grouping. The patron (the final
  objective) ends the game.

## Economy benchmarks (rough)

- Souls per minute is the cleanest economy signal. Roughly: under ~500/min in lane is slow,
  ~600 to 900/min mid is healthy, 1,000+/min late is strong. These scale with rank and hero.
- A farming hero that is behind in net worth but high in souls/min is recovering; one that is low
  in both is being starved or is dying too much (deaths lose souls directly via the death penalty).
- Soul sources matter: a healthy economy mixes lane creeps, neutral camps, and orbs. Leaning only on
  lane creeps means missed jungle; lots of lost-on-death souls means dying too much.
- Last hits and denies in lane: more denies means you starved your opponent. Low last hits with low
  souls/min usually means poor farming mechanics or getting zoned off the wave.

## Objectives and macro

- **Guardians, Walkers, Shrines, Patron:** the tower line. Taking them opens the map and pressures
  the enemy base; losing them cedes space. The objectives list in the digest shows what fell and
  when, by which team.
- **Mid-boss (Rejuvenator):** a neutral boss that grants a strong team-wide buff (and historically a
  revive). Taking it uncontested is a big swing. If the digest shows the enemy claimed mid-boss
  once or twice while you were behind or farming elsewhere, that is a macro failure worth naming.
- **Urn / idol mechanics:** a deliverable objective that grants souls for getting it to a drop
  point. Mobile, durable heroes make good carriers. (Urn was reworked in the June 2026 patch, so
  check current behaviour; the principle of contesting it stands.)
- **Reading the soul lead chart:** the single best macro signal. A lead that grows steadily means
  snowballing; a lead that swings hard at a timestamp usually marks a won or lost fight or objective.
  Cross-reference the death markers and mid-boss markers on the chart.
- **When behind:** the correct play is usually to group, defend, take safe farm, and wait for a
  pick or a mistake, not to seek solo fights deep in enemy territory. Deaths far on the enemy side
  of the map (strongly negative world coordinates) while behind are a classic "throwing while behind"
  pattern. Name it, but flag the blind spot that you cannot see whether the team forced the fight.

## Comeback factors

Deadlock has comeback mechanics (bounty on the leading team, objectives that reward the trailing
team). Being 20k behind is not unlosable. The levers are: stop dying (especially the long late
deaths), contest or deny the next mid-boss, and group for one good fight rather than feeding picks.
