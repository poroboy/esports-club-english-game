# Esports Club Manager for English Practice: Game Spec (draft v0.2.2)

Draft spec for a personal free-time game. It comes from a brainstorm. Stage 0 decisions were made on 2026-10-11 (see "Changes in v0.2").

Tags used in this file:

- **[OPEN]** still needs a decision. The stage that will decide it is given.
- **[TRIAL]** decided for version 1 and to be reviewed after the first play test (about two weeks of play).
- **[PROPOSED]** a suggestion the user has not confirmed yet.
- No tag: decided by the user.

## Changes in v0.2

- The 8 open points of v0.1 are settled as **[TRIAL]** decisions: feedback language, second-tier league approach, player attributes, snapshot storage, scoring weights and the harder-structure rule, shotcalling timing, session length, chunk display.
- Shotcalling is now a round of 3 situations with one check request per round. The timer counts typing time only.
- The match formula and the version 1 scope (accepted earlier by the user) are no longer **[PROPOSED]**.
- New requirements GM-16 to GM-18. The open questions list is rewritten.
- v0.2.1: Liquipedia's API Terms of Use were re-read on 2026-10-11. Automated access to generated HTML pages is not permitted, so data is collected only through an API (see "Real data"). The Hint button costs no score in version 1 (confirmed).
- v0.2.2: Snapshot format v0.1 approved on 2026-10-11 (see "Snapshot format"), with results and honors going back 5 years. Work moves to Claude Code on the user's own computer.

## Overview

A single-player browser game in which the player manages a professional League of Legends esports club. Every important decision is made by typing English. Claude checks each typed answer and the game shows the correct version, its meaning and the reasons. The game is a separate project from the TOEIC mock-test app: it is played in free time, it does not count as practice time, and it shares no data with the TOEIC app.

The player is a Thai native speaker with intermediate English. The long-term goal is IELTS band 7, so the game trains output (writing now, speaking later), where the player is weakest. Reading and listening are already stronger and are not the target of this game.

Design principles

1. The player always types their own English. No multiple choice.
2. Language affects the club only indirectly. Match results come from the match formula, never from how well the player typed.
3. A short, safe answer must never be the best strategy in a long-form scene.
4. The world moves only while the player plays. Days off are never punished.
5. Money, stocks and rankings exist only inside the game.
6. The game is fun first: a long-term goal (ranking, club value, rivals) keeps the player coming back, and new situations keep the language varied.
7. One self-contained HTML file, no server, same approach as the TOEIC app.

## Language goals

| Goal | How the game trains it |
| --- | --- |
| Link ideas (because, although, so, however) | Long-form scenes reward correct linking |
| Write longer than a few short sentences | Long-form scenes need developed answers |
| Tenses (past, present perfect, future, conditionals) | Scenes are chosen so each needs a different tense: past in press conferences, conditionals in negotiations |
| Chunks (sentence starters the player can continue freely) | Hint button before typing and a suited chunk after the feedback (see "Chunks") |
| Fast, short, clear speech | Shotcalling rounds |

## Game loop

1. The player advances the world by one turn (one match week). Nothing moves without this action.
2. The game plays the match with the match formula and shows the result.
3. One long scene follows: a press conference about the result, or a negotiation when a contract is near its end.
4. One shotcalling round follows (3 short situations).
5. Claude checks the typed answers. The feedback screen shows the result.
6. Scene results change club values (see Effects).
7. At the end of a season: table, results, season summary.

Target session length: 5 to 10 minutes, which is one turn as described above. **[TRIAL]**

## Scenes

### Version 1

| Scene | Length | What the player does | Effect (indirect) |
| --- | --- | --- | --- |
| Press conference | Long | After a match, a journalist asks 2 to 3 questions about the result; the player answers in writing | Club reputation **[PROPOSED]** |
| Negotiation | Long | Contract renewal with a player or an agent: salary, length, conditions | Deal terms and the player's morale |
| Shotcalling | Short, timed | A round of 3 match moments; for each the player types one short call (for example "Group mid, drake in 30") | Team chemistry |

Shotcalling timing **[TRIAL]**: the game times only the typing of each call, on the player's own device. The time Claude needs for the check is not counted. The 3 calls of a round are sent to Claude in one request when the round ends, which saves waiting time and usage.

### Later

Scouting interview and academy deals, sponsor negotiation, investor letter and funding pitch (stocks), crisis scenes (losing streak, conflict between players), social media posts and fan replies.

## Scoring

Claude scores every typed answer on these dimensions, 0 to 100 each.

| Dimension | Meaning |
| --- | --- |
| Accuracy | Grammar, tense, word choice |
| Linking | Correct use of connecting words and clause structure |
| Development | Length and quality of ideas, reasons and examples |
| Relevance | Answers what was asked |
| Naturalness | Sounds like a real person in this situation |

Weights **[TRIAL]**:

| Scene | Accuracy | Linking | Development | Relevance | Naturalness |
| --- | --- | --- | --- | --- | --- |
| Press conference, negotiation | 30 | 20 | 20 | 20 | 10 |
| Shotcalling | 40 | not scored | not scored | 40 | 20 |

Shotcalling also scores speed. The game measures speed itself, and a faster correct call scores higher.

Rules

1. Long-form scenes have a minimum development level. A shorter answer caps the Linking and Development scores, so "Yes, I like it" cannot win. **[OPEN: exact minimum per scene, decided in Stage 4]**
2. Harder structures **[TRIAL]**: the player is never punished for trying a harder structure and getting it partly wrong. When a harder structure is partly wrong, Accuracy falls by the amount of the errors, but Linking and Development are scored on what the player attempted. The total must stay above that of a fully correct one-clause answer. This rule goes into Claude's scoring instructions and is tested with sample answers in Stage 2.
3. A fully correct answer gives the largest effect. A partly correct answer gives a smaller one, and the effect falls step by step.

## Chunks

Chunks are sentence starters the player can continue freely. **[TRIAL]**

- In long scenes a **Hint** button before typing shows 1 or 2 starter chunks. Using it does not reduce the score in version 1.
- After the feedback, the game shows one chunk that suits the situation.
- Shotcalling shows no hint, because the calls are short and timed.

## Feedback screen

After every answer the player sees:

1. The player's sentence, with the mistakes marked.
2. The corrected sentence.
3. The meaning of the corrected sentence.
4. A short reason for each mistake.
5. The dimension scores and the effect on the club.
6. One suited chunk (see Chunks).

Language **[TRIAL]**: the meaning and the reasons are in English at about CEFR B1. A Thai help button shows the Thai version only when the player presses it, as in the TOEIC app. The Thai text is requested on demand (a separate request), so the normal feedback stays fast and uses less of the player's Claude usage.

A shotcalling round shows the feedback for its 3 calls together after the check.

## Claude check

Claude checks every typed answer through the artifact runtime capability `sample`. Check which capabilities exist (Artifact tool, action "capabilities") before building. It needs a claude.ai login and an internet connection, uses the viewer's own Claude usage, and asks for consent on the first request.

Proposed response shape (final shape **[OPEN]**, decided in Stage 2; Claude returns only JSON). For a shotcalling round the response holds the 3 results in one JSON.

```json
{
  "scene": "press-conference",
  "scores": { "accuracy": 70, "linking": 55, "development": 60, "relevance": 90, "naturalness": 65 },
  "corrected": "We lost because we made too many mistakes in the early game.",
  "meaning": "The reason for the loss was many errors at the start of the game.",
  "issues": [
    { "span": "we lose", "fix": "we lost", "reason": "The match is finished, so use the past simple." }
  ]
}
```

Failure handling: a check that fails or is refused shows a short message, is not retried automatically, and costs the player nothing.

## World and data

### Real data

- Source: Liquipedia (League of Legends wiki).
- Scope: the 5 regions LCK, LPL, LEC, LCS and LCP, with the top league and the second-tier league of each region, and every team in them.
  - **[TRIAL]** In Stage 1a, look at Liquipedia and pick the main second-tier league of each region. If a region has several, take the main one first and keep the data size under control.
  - **[OPEN]** The exact list is confirmed in Stage 1a.
- One detailed snapshot of today's data (teams, players, roles, nationalities, ages, results, placings, transfer history). After the start, the game world runs by itself and does not follow the real world.
- Credit page for Liquipedia in the game. Liquipedia content is licensed CC-BY-SA 3.0 and requires attribution.
- Follow Liquipedia's API Terms of Use (current version read on 2026-10-11; read it again before collecting):
  - Automated access to generated HTML pages is not permitted. Use only an API.
  - Send a custom User-Agent that identifies the project and gives contact information. Support gzip, reuse the HTTP client, cache results and never request the same data twice.
  - MediaWiki API (free): no more than 1 request per 2 seconds, and `action=parse` no more than 1 request per 30 seconds.
  - LiquipediaDB API: access needs an approved request, no more than 60 requests per hour, and the API key is not shared.
  - If the game is ever shared or sold, check the terms for commercial use again.
- Storage **[TRIAL]**: published pages cannot fetch other sites while running, so the snapshot is made in a separate data stage and embedded in the game page. To refresh the data, publish the game again. **[OPEN: confirm the real size in Stage 1a and check that it fits the page size limit]**
- A new game copies the snapshot into the save, so a later snapshot refresh never changes an existing save. **[PROPOSED]**

### Snapshot format (v0.1, approved 2026-10-11)

Stage 1a collects facts only. The rating numbers are made in Stage 1b from these facts, so the rating rules can change without collecting data again.

```json
{
  "meta": { "schemaVersion": "0.1", "snapshotDate": "YYYY-MM-DD", "source": "Liquipedia", "license": "CC-BY-SA 3.0" },
  "leagues": [
    { "id": "example-league", "name": "Example League", "region": "LCK", "tier": 1, "page": "Liquipedia page name" }
  ],
  "teams": [
    { "id": "example-team", "name": "Example Team", "tag": "EXT", "leagueId": "example-league",
      "country": "KR", "parentTeamId": null,
      "lastSeasons": [ { "season": "2026 Summer", "placement": 2 } ], "page": "..." }
  ],
  "players": [
    { "id": "example-player", "handle": "ExamplePlayer", "nationality": "KR", "birthDate": "YYYY-MM-DD or null",
      "role": "mid", "teamId": "example-team", "status": "starter", "joinedTeam": "YYYY-MM-DD", "debutYear": 2019,
      "teamHistory": [ { "team": "Other Team", "from": "YYYY-MM", "to": "YYYY-MM" } ],
      "honors": [ { "event": "Example Event", "year": 2025, "placement": 1, "eventTier": "international" } ],
      "page": "..." }
  ]
}
```

Rules:

- Players are stored by in-game handle only. No real names.
- Every item keeps its Liquipedia page name, for credit and as the cache key.
- Results, honors and team history go back at most 5 years.
- `birthDate` may be partial or null; keep what Liquipedia shows.
- The shape changes only after asking the user first.

### Player ratings

Liquipedia gives facts but no skill ratings. The game estimates each player's level from context: role, age, league tier, team results, playoff and international placings, years as a professional, roster stability, transfer history. A player with little data gets a default by league tier. Ratings are the game's estimate, not a fact about the real player.

- Scale 1 to 99.
- Attributes **[TRIAL]**: mechanics, laning, teamfighting, game knowledge, consistency; plus age and a hidden potential for young players.
- Rules v0.1 (Stage 1b, approved 2026-10-11) **[TRIAL]**. Full text: `docs/rating-rules-draft.md`. Code: `build_ratings.py`; output: `data/ratings.json` (new file, separate from the snapshot, which stays facts only). The same snapshot always gives the same ratings.
  - overall = league base (LCK and LPL 72, LEC 67, LCS and LCP 62, LCK CL 57, LDL 55, LFL 51, NACL 47, LJL 45) + experience (+1 per year in the data, max +4) + international play (round(4.5 x sqrt(appearances at Worlds, MSI, First Stand 2022 to 2026))) - 5 for a sub - age adjustment (1 per year over 29; 2 under 19) + results (0 for now).
  - Attributes = overall + role tilt + age and experience tilt + a fixed per-player spread of -3 to +3 (a hash of the player id), shifted so their average equals overall.
  - Hidden potential for players aged 22 or less: overall + growth by age (+18 at 17 down to +3 at 22) + a spread of 0 to 4, max 95. Unknown age: overall + 3.
  - Every rating has a `why` breakdown so the game can explain it.
- Known limits: without placements the best players tie (9 players at 90); LDL has no birth dates; the experience term only sees the years since 2022. The **results** term and the real `debutYear` wait for LiquipediaDB data (needs the user's API key).

### Invented parts

- Player personalities and backgrounds are invented. Private use.
- Academy prospects are generated by the game with fictional names (later stage).

## Match simulation (version 1)

Formula **[TRIAL]**:

Rules v0.1 (Stage 3, approved 2026-10-11). Full text: `docs/match-rules-draft.md`. Code: `game/template.html` (match engine section).

1. Team strength = role-weighted average of the five starters' overall ratings (top 0.18, jungle 0.22, mid 0.22, bot 0.22, support 0.16), then measured in standard deviations of the team's own league (z), because the second leagues are close together. A role with no player in the data gets a stand-in (league base rating minus 3), shown as "Stand-in"; so all 97 clubs can be chosen.
2. Modifiers: chemistry and morale of the user's club, each up to +/-0.35 z (0.35 x (value - 50) / 50); preparation is 0 in version 1; reputation does not touch the match. AI clubs stay at 0.
3. Win probability of one game = 1 / (1 + 10^(-(zA - zB) / 6)). A match is best of 3 games (2-0 or 2-1). The draws come from a seed stored in the save, so a played result never changes on reload.
4. Season: single round robin per league (one match per club per week; a league with an odd number of teams gives each club one bye week, on which the match day plays the contract scene instead of the press conference). One table, no playoffs in version 1: match wins, then game difference, then club id. Only the user's league is simulated. At the end the game shows the final table and starts the next season (year + 1) with the same teams and ratings; the table resets and club values stay.
5. Other clubs are AI rivals with simple behaviour in version 1: they play matches and their ratings stay as they are.

Checked on 2026-10-11 (500 simulated seasons per league): the strongest club wins 65 to 80% of its matches, the weakest 21 to 35%, the strongest club takes the title 22 to 67% of the time (more in leagues with one clear favourite, such as NACL, LEC, LCS, LCP). A mid-table club gains about 9 points of match win rate between chemistry/morale 50 and 100.

Language affects the modifiers (chemistry, morale), not the result directly.

## Effects (how language reaches the club)

| Language result | Club value |
| --- | --- |
| Press conference | Club reputation |
| Negotiation | Contract terms, player morale |
| Shotcalling | Team chemistry |
| Scouting interview (later) | Quality of information about a prospect |
| Investor letter, funding pitch (later) | Investor confidence, share price |

## Later stages (in order of value)

1. **Academy.** Scout, sign, develop and sell young players.
   - A player sold to a club in the game's leagues keeps a data record. Their stats update once per season from age, the new club's quality and randomness, with no match-by-match simulation.
   - A player sold to a club outside the game's leagues needs no record.
   - Languages trained: questions (scouting), negotiation, advice and feedback.
2. **Stocks.** The club is a company with an in-game share price that moves with results, income, reputation and investor confidence. Funding rounds need a pitch to AI investors. End-of-quarter results statement.
3. **Rivals and careers.** AI rival personalities by region and tier (rich clubs that buy stars, clubs that develop youth, clubs that love drama). Player aging and retirement. End-of-season ranking and comparison with the player's own past seasons.
4. **Random events.** Injury, burnout, a rival's offer for a starter, a rookie challenging a starter.
5. **Speaking.** Voice input, if it is ever added, as a separate stage.

## Functional requirements (version 1)

| ID | Requirement |
| --- | --- |
| GM-01 | At the start the player picks one club from the real data; all other clubs are AI rivals |
| GM-02 | The world advances one turn only when the player chooses to, and never advances by itself |
| GM-03 | After each turn the game shows the match result and the updated league table |
| GM-04 | Three scenes in version 1: press conference, negotiation, shotcalling |
| GM-05 | Every typed answer is checked by Claude and scored on the five dimensions |
| GM-06 | Feedback screen after every answer, as described above |
| GM-07 | Long-form scenes have a minimum development level; shotcalling is timed (typing time only, measured by the game) |
| GM-08 | Effects on club values come from the scores, and a fully correct answer gives the largest effect |
| GM-09 | Match results come only from the match formula |
| GM-10 | The game saves automatically in the user's private claude.ai artifact database and syncs across the user's devices **[PROPOSED]** |
| GM-11 | The save can be exported and imported as a JSON file for backup **[PROPOSED]**. Deleting the app or publishing it as a new artifact starts with an empty database |
| GM-12 | A history of past answers with their feedback can be reviewed later **[PROPOSED]** |
| GM-13 | A credit page for Liquipedia |
| GM-14 | A check that fails or is refused shows a short message, is not retried automatically, and costs the player nothing |
| GM-15 | Works on a wide screen and on a phone from one responsive implementation |
| GM-16 | Long scenes have a Hint button with 1 or 2 starter chunks (no score cost in version 1); the feedback shows one suited chunk |
| GM-17 | Feedback is in English at about B1; a Thai help button shows the Thai version on demand |
| GM-18 | A shotcalling round has 3 situations and one check request per round |

## Stages and models

Build in stages. Finish and test one stage before starting the next. Before every stage, state which model and effort the task should use. Model names change, so check the current Claude lineup before choosing.

| Stage | Task | Model | Effort |
| --- | --- | --- | --- |
| 0 | Finish this spec (settle the open points). Done in v0.2 except the items in "Open questions" | Sonnet 5.5 | Medium |
| 1a | Collect and clean Liquipedia data (API only, slow, cached, within its terms; the collection script runs on the user's own computer **[PROPOSED]**) | Sonnet 5.5 | Medium |
| 1b | Player rating rules | Opus 5.5 | High |
| 2 | Core screens, save, Claude check, feedback screen | Sonnet 5.5 | High |
| 3 | Match formula and season | Sonnet 5.5 | High |
| 4 | The three scenes of version 1 | Sonnet 5.5 | High |
| 5+ | Academy, stocks, rivals, events (decide in the spec) | to be decided | |
| Small fixes: text, colours, spacing, one clear bug | Sonnet 5.5 | Low or Medium |
| Hard bug, or a fix that failed twice | Opus 5.5 | High |
| Anything Opus 5.5 at High cannot solve | Fable 5.1 | High |

Review point: after about two weeks of play, review every **[TRIAL]** decision in this file and update the spec.

## Constraints and risks

- The game needs a claude.ai login and an internet connection because Claude checks every answer. It uses the player's own Claude usage.
- Claude's checks are not perfect. The score is a guide, not a grade.
- Ratings are estimates made by the game, not facts about real players.
- Real names are used for private use. If the game is ever shared or sold, check Liquipedia's terms, the fan-content policy of the game's publisher and the rules about real people's names again.
- Keep scenes varied and the first version small. The player is afraid the game will get boring, so the first test is whether it is still fun after about two weeks.
- Do not let building the game take time from the daily TOEIC practice, which is the main plan.

## Not in version 1

Academy, stocks, aging and retirement, rival personalities, end-of-season rankings, random events, voice input, multiple clubs controlled by the player, multiplayer or online ranking with other people.

## Open questions

1. Exact second-tier league of each region, and the real size of the data snapshot (Stage 1a).
2. ~~Player rating rules (Stage 1b).~~ Done as v0.1 on 2026-10-11 (see "Player ratings"); the results term waits for LiquipediaDB data and the rules are reviewed with the **[TRIAL]** items.
3. Final check-response shape, including the shotcalling round, and how the harder-structure rule is tested (Stage 2).
4. ~~Season format of each league (Stage 3).~~ Done as v0.1 on 2026-10-11 (see "Match simulation"): single round robin, one table, no playoffs.
5. Exact minimum length of an answer in each long scene (Stage 4).
6. Whether the Hint button should cost score after version 1 (decide at the two-week review).

## Suggested project instructions

Paste these into the new project.

```text
You are building and maintaining a personal English-practice game. The project file esports-club-game-spec.md is the source of truth. Follow it exactly.

Rules:
1. Build the game as a single self-contained HTML file (HTML, CSS, JS inline). No server.
2. Never change data schemas or the check-response shape without asking me first and explaining why.
3. Build in stages. Finish and test one stage before starting the next.
4. When you change existing code, change only what the task needs and tell me what changed.
5. This game is separate from the TOEIC mock-test app. Do not share data or add game features to it.
6. Talk to me in Thai. Keep code, comments, game text and feedback text in English.
7. Before every task, tell me which Claude model and effort level to use, following "Stages and models" in the spec.
8. Follow Liquipedia's API Terms of Use when collecting data: use only its APIs (never automated access to HTML pages), send a User-Agent that identifies the project with contact information, stay within the rate limits, cache results, and credit Liquipedia.
```
