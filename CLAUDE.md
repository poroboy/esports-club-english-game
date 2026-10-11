# Esports Club English Game: project rules for Claude Code

This is a personal English-practice game (a League of Legends esports club manager). The file `esports-club-game-spec.md` in this folder is the source of truth. Follow it exactly.

## How to work with me

- Talk to me in Thai. Keep code, comments, game text and feedback text in English.
- Before every task, tell me which Claude model and effort level to use, following "Stages and models" in the spec.
- Build in stages. Finish and test one stage before starting the next. Current stage: **Stages 1a, 1b, 2 and 3 are done (data, rating rules v0.1, game page, match formula and season v0.1); next is Stage 4, the three scenes of version 1** (Sonnet 5.5, High). The LiquipediaDB placements are still open and need the user's API key.
- Never change data schemas (including the snapshot format in the spec) or the check-response shape without asking me first and explaining why.
- When you change existing code, change only what the task needs and tell me what changed.
- The game is one self-contained HTML file with no server. It is separate from my TOEIC app: no shared data.

## Liquipedia rules (Stage 1a)

- Use only Liquipedia's MediaWiki API. Never fetch generated HTML pages, never use `action=parse`.
- Keep the custom User-Agent from `config.json` (project name, repo link, my email).
- At most 1 request per 2 seconds. Cache everything. Never request the same page twice.
- Read https://liquipedia.net/api-terms-of-use again before any run bigger than the pilot.
- The game must credit Liquipedia (CC-BY-SA 3.0).

## Safety rules for this folder

- Work only inside this project folder.
- Always ask me before any command that sends requests to Liquipedia, and before `git push`.
- Run the pilot only (`seeds_pilot.json`, 1 request). Do not start a full collection unless I say so after we agree on the page list.
- `config.json` holds my email. I type it myself. Never print it into documents, never commit it.
- Never commit `config.json` or the `cache/` folder. Make sure `.gitignore` contains: `config.json`, `cache/`, `__pycache__/`.
- Do not ask me for passwords or tokens. If git asks me to sign in, I do it myself.
- If the script stops with an HTTP or API error, show me the message and wait. Do not retry.

## Pilot steps (current task)

1. Make sure these files are in the folder: `esports-club-game-spec.md`, `liquipedia_fetch.py`, `config.example.json`, `seeds_pilot.json`.
2. Create `.gitignore` as above.
3. Tell me to copy `config.example.json` to `config.json` and edit `contact_email` myself.
4. Install `requests` (ask first).
5. Run `python liquipedia_fetch.py --seeds seeds_pilot.json --dry-run` and show me the result.
6. After I say yes, run it for real (1 request, 3 pages). Report which pages were found and which were missing.
7. Look at the files in `cache/pages`. Do not write a parser yet. Show me what the wikitext of a team page looks like (roster, player links, templates) and propose how to parse it. I approve before you write the parser.
8. Then propose the full page list (leagues and teams for LCK, LPL, LEC, LCS, LCP and their second-tier leagues) and the number of requests needed. Wait for my approval.

## Notes

- Second-tier leagues proposed so far: LCK Challengers League, LDL, NACL, LJL (for LCP). For LEC, pick the main ERL league after checking the ERL list through the API. All of these must be confirmed against Liquipedia.
- Ratings are not part of Stage 1a. They are made in Stage 1b from the collected facts.
