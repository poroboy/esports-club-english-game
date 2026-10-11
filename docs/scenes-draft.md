# The three scenes of version 1: draft v0.1 (Stage 4)

Status: **approved 2026-10-11** (all five decisions as proposed) and built in `game/template.html`. A summary is in `esports-club-game-spec.md` ("Version 1 scene rules"). Checked with the real Claude by the user on 2026-10-11 (game version 6, after the Level up change): the scoring self-test passed (B 66 above A 57; B accuracy 55 below A 95; A 57 above C 40) and the minimum-length test passed (short answer: linking 25, development 15; long answer total 84 against 51). The margin of the first test is thin (9 points), so watch for reports where a complex answer scores below a short correct one.

## Where we are

| Scene | Now (test version) | Spec says |
| --- | --- | --- |
| Press conference | 1 question, 4 variants, minimum 15 words | 2 to 3 questions about the result |
| Negotiation | 1 message, 2 variants, minimum 20 words, no contract data | contract renewal: salary, length, conditions; effect on deal terms and morale |
| Shotcalling | 3 calls, 2 rounds (6 situations) | 3 situations per round, timed, no hints |
| Hint button | 2 starters per scene, written by hand | 1 or 2 starter chunks before typing, no score cost |

## 1. Minimum development level (open question 5)

The minimum is measured in words, by the game, and given to Claude, which caps Linking and Development at 40 when the answer is shorter (scoring rule 1, already in the check prompt). The game warns before sending a short answer but never blocks it.

| Scene | Minimum |
| --- | --- |
| Press conference | **25 words per answer**, 2 answers (about 50 words) |
| Negotiation | **45 words**, one reply |
| Shotcalling | none (short is the point); an empty call is not sent |

Reason: a day is 5 to 10 minutes (spec). At about 15 words a minute for a B1 writer, this is 3 to 4 minutes of typing in the long scene plus the timed round. The numbers are **[TRIAL]** and checked at the two-week review.

## 2. Press conference: 2 questions, one check

- The journalist asks **2 questions**: the first about the result, the second a follow-up (pressure, a player, the season so far, the next match).
- Both answers are sent in **one** request (like shotcalling), so the check costs the same as today.
- Language goals: past tenses for what happened, present perfect for the season so far. These are named to Claude as the target structures. A different correct structure is never punished.
- Effect: club reputation, from the average of the two totals.

**Check-response shape (needs your approval).** The long-scene shape stays exactly as approved for one answer. For two answers the response is the same shape as the shotcalling round, with the five long-scene dimensions:

```json
{
  "results": [
    { "n": 1, "scores": { "accuracy": 70, "linking": 55, "development": 60, "relevance": 90, "naturalness": 65 },
      "corrected": "...", "meaning": "...", "issues": [ { "span": "...", "fix": "...", "reason": "..." } ] },
    { "n": 2, "...": "..." }
  ],
  "chunk": "..."
}
```

A negotiation reply (one answer) keeps the approved single-answer shape.

## 3. Negotiation with real contract terms

- Each player on your five starters gets an **invented** contract end year (the snapshot has none; contracts are not facts about the real players). The game stores only `{playerId: endYear}`.
- A negotiation is held with the player or his agent when his contract ends this season (otherwise a rival-offer or conditions topic). It covers salary, length, conditions. Money does not exist in version 1, so "salary" is part of the talk, not a number in the game.
- Language goals: conditionals and modals ("If you ..., we would ...", "We could offer ...").
- **Outcome from the score** (the player never leaves in version 1):

| Total | Contract | Player morale |
| --- | --- | --- |
| 80 or more | 3 more years | morale +4 |
| 60 to 79 | 2 more years | morale +2 |
| below 60 | 1 more year | morale +1 |

  Morale uses the same steps as today (a better answer gives a bigger step, never negative). The contract end year is shown on the player card.

**Save schema 3 (needs your approval):** adds `contracts: { "playerId": 2027 }`. Old saves are upgraded when the game opens (contract end years are made from the save seed). The snapshot and the check-response shape of the single answer do not change.

## 4. Shotcalling: a bank of situations

- **24 situations** in 4 groups of 6: objective (dragon, Baron, towers), fight (engage, retreat, focus), rotation and vision (ward, roam, lane swap), and recovery (behind, low health, no ultimates).
- A round has 3 situations, chosen from the season seed and the week, one group each at least twice a season.
- Same scoring as today (accuracy, relevance, naturalness; speed credit for a correct call). No hints. Typing time only.

## 5. Hint button and chunks (GM-16)

- Every situation has **2 starter chunks written by hand** (not generated, so a hint costs no usage and no time).
- After feedback, Claude gives 1 suited chunk (already in the check response).
- The hint stays free in version 1.

## 6. Content volume

| Scene | Situations |
| --- | --- |
| Press conference | 16 questions in pairs (win, narrow win, loss, heavy loss; streak; rival; a player stands out; the season so far) |
| Negotiation | 8 topics (renewal x3, rival offer, role and playing time, bonus, conditions, new young player) |
| Shotcalling | 24 situations |

All text is English, written at about B1, with the club, rival and player names filled in from the game. No real person is quoted.

## Checks before the rules are accepted

1. The press conference sends one request for 2 answers and shows 2 feedback blocks; a failed check keeps both answers and applies nothing.
2. Answers shorter than the minimum show the warning and are still sent; Claude caps Linking and Development at 40 (tested with the scoring self-test using a short and a long version of the same answer).
3. The harder-structure test (self-test) still passes with the new prompt text.
4. A negotiation sets the contract end year and morale as in the table; an old save is upgraded without losing anything.
5. 30 weeks in a row never show the same situation twice in a row, and every question mentions only things that exist in the game state (no missing names, no wrong score).

## Decisions needed

1. **Minimums:** press 25 words per answer (2 answers), negotiation 45 words, shotcalling none. Or other numbers.
2. **Press conference with 2 questions and one check**, using the two-answer response shape above.
3. **Contracts:** invented end years, saved as `contracts` in save schema 3, with the outcome table above.
4. **Content volume:** 16 / 8 / 24 situations written by hand.
5. **Short-answer warning:** a note in the page before sending, never a block.
