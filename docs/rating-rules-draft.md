# Player rating rules: draft v0.1 (Stage 1b)

Status: **approved 2026-10-11** (all five decisions as proposed) and built in `build_ratings.py`. A summary is in `esports-club-game-spec.md` ("Player ratings").

## Goals

1. Every number comes from facts in `data/snapshot.json`, by fixed rules. Same snapshot, same ratings.
2. The rules are a small table of constants, so they can be tuned without collecting data again.
3. Each rating can be explained: the game can show "why" (league, experience, international play).
4. Ratings are the game's estimate, not a fact about the real player (spec, "Constraints and risks").

## Facts available today (snapshot 2026-10-11, 531 players)

| Fact | Coverage | Notes |
| --- | --- | --- |
| League and tier of current team | 531 | 10 leagues |
| Starter or sub | 531 | 469 starters, 62 subs |
| Role | 531 | about 105 per role |
| Years in our data (2022 to 2026) | 531 | from `teamHistory`; capped at 4 because data starts in 2022 |
| Age | 419 | LDL has no birth dates at all; NACL, LJL, LFL partly missing |
| International appearances (Worlds, MSI, First Stand 2022 to 2026) | 173 players with at least 1 | in the cache, **not yet in the snapshot** (see Decision 1) |
| Stint with current team | 523 | `joinedTeam` |
| Team and player placements, titles | almost none | waits for LiquipediaDB |

## Overall rating (1 to 99)

```
overall = leagueBase[league]
        + experience            (+1 per year in data, max +4)
        + international         (round(4.5 * sqrt(appearances)): 1 -> +5, 4 -> +9, 10 -> +14)
        - sub penalty           (-5 for a sub)
        - age adjustment        (age 30+: -1 per year over 29; age under 19: -2)
        + results               (0 for now; filled when placements arrive, see "Later")
clamped to 1..99
```

League base (proposed, tunable):

| Region | Tier 1 | Base | Second league | Base |
| --- | --- | --- | --- | --- |
| LCK | LCK | 72 | LCK CL | 57 |
| LPL | LPL | 72 | LDL | 55 |
| LEC | LEC | 67 | LFL | 51 |
| LCS | LCS | 62 | NACL | 47 |
| LCP | LCP | 62 | LJL | 45 |

Reason for the order: LCK and LPL have won the international events of recent years; LEC is next; LCS and LCP are below. Second leagues sit about 15 points under their top league.

Players with no Liquipedia page (23) get the same formula: their league, status and team history come from the rosters. This is the spec's "default by league tier".

### Preview with today's data

| League | Median | Min | Max |
| --- | --- | --- | --- |
| LCK | 80 | 68 | 90 |
| LPL | 76 | 69 | 90 |
| LEC | 75 | 66 | 86 |
| LCS | 70 | 62 | 80 |
| LCP | 70.5 | 59 | 77 |
| LCK CL | 58 | 50 | 61 |
| LDL | 56 | 51 | 63 |
| LFL | 51 | 46 | 59 |
| NACL | 48 | 42 | 56 |
| LJL | 46 | 43 | 52 |

Top today: knight, Zeus, Oner, ON, Keria, JunJia, Gumayusi, Chovy, Bin (90); Faker, Doran, Canyon (89).

**Known weakness:** 9 players share the top value, because without placements nothing separates a world champion from a quarter-finalist. Attributes (below) separate them a little; placements fix it properly.

## Attributes (1 to 99)

Five attributes from the spec: mechanics, laning, teamfighting, game knowledge, consistency.

```
attribute = overall + roleTilt + ageTilt + spread
then shift all five so their average equals overall (overall stays the main number)
```

Role tilt (laning / teamfighting / game knowledge / mechanics):

| Role | Laning | Teamfighting | Game knowledge | Mechanics |
| --- | --- | --- | --- | --- |
| top | +3 | -1 | -1 | 0 |
| jungle | -3 | +1 | +3 | 0 |
| mid | +1 | +1 | +1 | +1 |
| bot | +3 | +1 | -2 | +2 |
| support | -2 | +2 | +3 | -2 |

Age and experience tilt:

- Mechanics: +2 at age 21 or less; -2 per year over 27 (max -6).
- Game knowledge: -3 at age 20 or less; +1 per year in data (max +4).
- Consistency: -4 under 19; +1 per year with the current team (max +3); -2 for a sub.
- Unknown age: no age tilt.

Spread: a fixed number from -3 to +3 per player and attribute, made from a hash of the player id and the attribute name. It looks random but never changes between runs, so players with the same overall are not identical.

## Age and hidden potential

- Age is shown in the game (whole years on the snapshot date). Unknown age is shown as unknown.
- Potential (hidden) for players aged 22 or less:
  `potential = overall + growth[age] + spread(0..4)`, max 95.
  growth: 17: +18, 18: +15, 19: +12, 20: +9, 21: +6, 22: +3.
- Older players: potential = overall.
- Unknown age: potential = overall + 3 (see Decision 4).

## Output (new file, see Decision 2)

`data/ratings.json`, separate from the snapshot so the snapshot stays facts only:

```json
{
  "meta": { "rulesVersion": "0.1", "snapshotDate": "2026-10-11" },
  "players": {
    "faker": { "overall": 89, "mechanics": 86, "laning": 90, "teamfighting": 89,
               "gameKnowledge": 94, "consistency": 88, "potential": 89, "age": 30,
               "why": { "league": 72, "experience": 4, "international": 14, "sub": 0, "age": -1, "results": 0 } }
  }
}
```

(The attribute numbers above are only an example of the shape.)

## Checks before the rules are accepted

1. All values in 1..99; potential is never below overall.
2. Running twice gives the same file.
3. In every region the top league median is higher than the second league median.
4. The average of the five attributes equals overall (±1 for rounding).
5. A readable list of the top 30 and the bottom 10 of each league for you to judge.

## Later (after LiquipediaDB)

- `results` term: team placements of the last 5 years, weighted by recency (for example 1st in a tier-1 league +3, international title +5, with a cap).
- `debutYear` replaces "years in data", so veterans who started before 2022 get their full experience.
- The top 9 tie should disappear.

## Decisions needed

1. **International appearances into the snapshot:** fill `honors` with `{"event", "year", "placement": null, "eventTier": "international"}` for each Worlds, MSI and First Stand roster appearance. The shape does not change; placement stays null until LiquipediaDB. Alternative: the rating script reads the cache directly (then ratings no longer come only from the snapshot).
2. **New file `data/ratings.json`** with the shape above (a new data schema, so it needs your approval).
3. **League bases** in the table above, or other numbers.
4. **Unknown age:** potential = overall + 3, or no potential bonus.
5. **Accept the top tie for now**, until LiquipediaDB placements arrive.
