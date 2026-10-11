# Match formula and season: draft v0.1 (Stage 3)

Status: **approved 2026-10-11** (all five decisions as proposed) and built in `game/template.html`. A summary is in `esports-club-game-spec.md` ("Match simulation"). The calibration ranges below were first estimated before the build; the 500-season check on the built engine gave the numbers in the spec (strongest club wins 65 to 80% of matches, weakest 21 to 35%, strongest club takes the title 22 to 67%).

Decided by the user on 2026-10-11: single round robin (one table, no playoffs in version 1); every club in every league can be chosen; after a season the game starts a new season with the same teams.

## Goals

1. Match results come only from the formula (GM-09). Language reaches the result only through the modifiers (chemistry, morale), never directly.
2. Every league feels competitive, even the second leagues where the ratings are close together.
3. Results are repeatable: the same save and the same seed give the same results.
4. The user's club and the AI clubs use the same formula. AI clubs keep their ratings (spec: "their ratings stay as they are").

## Facts from the data (snapshot 2026-10-11)

| League | Teams | Weeks (single round robin) | Strength spread (best to worst) |
| --- | --- | --- | --- |
| LCK / LCK CL | 10 / 10 | 9 / 9 | 13.4 / 2.4 |
| LPL / LDL | 14 / 10 | 13 / 9 | 14.7 / 5.2 |
| LEC / LFL | 10 / 10 | 9 / 9 | 12.4 / 2.9 |
| LCS / NACL | 8 / 10 | 7 / 9 | 10.3 / 3.7 |
| LCP / LJL | 8 / 7 | 7 / 7 | 6.4 / 2.8 |

Second leagues have a spread of 2 to 5 points, so raw rating differences would make them coin flips. The formula therefore compares teams **inside their own league**, in units of that league's spread (standard deviations).

## Team strength

```
lineup     = best player per role (starters first, then higher overall); the 5 roles top, jungle, mid, bot, support
strength   = 0.18 top + 0.22 jungle + 0.22 mid + 0.22 bot + 0.16 support     (weights of the five overalls)
z          = (strength - league average) / league standard deviation          (computed once per league from the snapshot)
```

Stand-ins: 8 clubs have fewer than 5 players in the snapshot (or a role without a player). A missing role gets a **stand-in** with overall = league base - 3 (league bases from the rating rules). Stand-ins are marked "Stand-in" on screen, have no name of their own and are not real players. This makes all 97 clubs playable.

## One match

```
zA' = zA + modifier(A)          zB' = zB + modifier(B)
modifier(club) = 0.35 * (chemistry - 50) / 50 + 0.35 * (morale - 50) / 50 + preparation       (max +0.7, min -0.7)
p(game won by A) = 1 / (1 + 10 ^ ( -(zA' - zB') / 6 ))
```

- A match is **best of 3** games, so the result reads 2-0 or 2-1 (or 0-2, 1-2). Each game is a draw with probability `p`.
- `chemistry` and `morale` are the club values of the user's club (start 50, set by the language scenes). AI clubs stay at 50, so their modifier is 0.
- `reputation` does not touch the match in version 1.
- `preparation` is 0 in version 1 (the spec lists it; nothing feeds it yet).
- **Randomness:** one seed per season, stored in the save. The draws of a match come from a hash of (seed, week, club ids), so reloading never changes a played result.
- The modifiers are read when the match is played, at the start of the match day. What you write in the scenes of that day affects the next matches, never the match already played.

Calibration with the real strengths (3,000 simulated seasons, scale 6): the strongest team wins about 50 to 60% of its matches in a league with a clear favourite and 70 to 75% in the others; the weakest wins 25 to 33%; the strongest team wins the title 25 to 50% of the time. A mid-table team with modifier 0 wins 47% of its matches; with the best language results (+0.7) it wins about 55%. So language helps, it never decides.

## Season and table

- **Schedule:** round robin by the circle method, one match per club per week. With an odd number of teams (LJL, 7) each club has one **bye week**. The user's club has no match that week: the match day plays the contract scene instead of the press conference, then shotcalling.
- **Table:** match wins, then game difference, then (rare) a fixed order by club id. Only the user's league is simulated each week (the other leagues are not shown in version 1). **Changed on 2026-10-11 after the build:** every league is now played at the same time and the Explore tab shows them; see the spec ("Match simulation", item 4) and save schema 4.
- **End of season:** final table, champion, the user's finish, season summary. Then the game starts the next season (year + 1) with the same teams and ratings. The table resets, club values stay, a short history of past seasons is kept. No promotion or relegation in version 1.

## Screens (Stage 3)

1. **Match result** at the start of each match day: score by game, short summary, updated table with the user's club highlighted (GM-03). Then the press conference uses this real result instead of the sample result.
2. New tab **League**: table, your fixtures, results so far.
3. Club hub: the next opponent is the real fixture; opponent strength is shown as z-based "stronger / similar / weaker".
4. **Season summary** screen at the end of the season.

## Save changes (needs your approval: a new data shape)

Save `schema` goes from 1 to 2. New fields:

```json
{
  "schema": 2,
  "season": { "year": 2026, "seed": 123456789, "results": [ { "w": 0, "a": "t1", "b": "dplus", "ga": 2, "gb": 1 } ] },
  "seasons": [ { "year": 2026, "champion": "gen-g-esports", "finish": 3, "wins": 5, "losses": 4 } ]
}
```

- The schedule is not stored; it is calculated from the team list and the seed.
- `results` holds only the user's league.
- An old save (schema 1) is upgraded when the game opens: the club, values and history are kept, the week goes back to 1 and a new season 2026 starts (the old weeks had only sample results).
- The snapshot and the check-response shape do not change.

## Checks before the rules are accepted

1. All 97 clubs have a full lineup (with stand-ins) and a z-score.
2. Every league's schedule has each pair exactly once and each club at most one match per week.
3. The same seed and the same club values always give the same results; a reload mid-season changes nothing.
4. A season simulated 500 times per league: title shares and win rates inside the ranges above.
5. Modifier at +0.7 versus 0 lifts a mid-table club's win rate by 6 to 10 points.

## Decisions needed

1. **Strength formula and role weights** (0.18 / 0.22 / 0.22 / 0.22 / 0.16), relative-to-league scale 6, modifier cap 0.35 each for chemistry and morale. Or other numbers.
2. **Best of 3 games** per match (result 2-0 or 2-1), table by match wins then game difference.
3. **Stand-ins** for missing roles (overall = league base - 3) so all 97 clubs can be chosen.
4. **Bye week** for odd leagues: contract scene instead of the press conference.
5. **Save schema 2** and the upgrade of old saves as described.
