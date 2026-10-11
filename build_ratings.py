#!/usr/bin/env python3
"""Build player ratings (rules v0.1, docs/rating-rules-draft.md) from data/snapshot.json.

Reads the snapshot only and writes data/ratings.json. The same snapshot always gives the same file:
the "spread" values look random but come from a hash of the player id.
Ratings are the game's estimate, not facts about real players.
"""
import hashlib
import json
import math
import statistics
import sys
from datetime import date
from pathlib import Path

SNAPSHOT = Path("data/snapshot.json")
OUT = Path("data/ratings.json")
RULES_VERSION = "0.1"

LEAGUE_BASE = {"lck": 72, "lpl": 72, "lec": 67, "lcs": 62, "lcp": 62,
               "lck-cl": 57, "ldl": 55, "lfl": 51, "nacl": 47, "ljl": 45}
EXPERIENCE_MAX = 4          # +1 per year in data
INTERNATIONAL_FACTOR = 4.5  # round(4.5 * sqrt(appearances))
SUB_PENALTY = 5
ATTRIBUTES = ["mechanics", "laning", "teamfighting", "gameKnowledge", "consistency"]
ROLE_TILT = {  # laning, teamfighting, gameKnowledge, mechanics
    "top": {"laning": 3, "teamfighting": -1, "gameKnowledge": -1, "mechanics": 0},
    "jungle": {"laning": -3, "teamfighting": 1, "gameKnowledge": 3, "mechanics": 0},
    "mid": {"laning": 1, "teamfighting": 1, "gameKnowledge": 1, "mechanics": 1},
    "bot": {"laning": 3, "teamfighting": 1, "gameKnowledge": -2, "mechanics": 2},
    "support": {"laning": -2, "teamfighting": 2, "gameKnowledge": 3, "mechanics": -2},
}
GROWTH = {17: 18, 18: 15, 19: 12, 20: 9, 21: 6, 22: 3}  # potential bonus by age (17 or younger: 18)
UNKNOWN_AGE_GROWTH = 3
POTENTIAL_MAX = 95


def clamp(x, lo=1, hi=99):
    return max(lo, min(hi, x))


def spread(player_id, name, low, high):
    """Fixed pseudo-random integer in [low, high] for this player and name."""
    h = int(hashlib.sha256(f"{player_id}:{name}".encode()).hexdigest(), 16)
    return low + h % (high - low + 1)


def parse_date(text):
    """'YYYY-MM-DD' with possibly unknown parts ('??'); unknown month/day -> July 1st. None if no year."""
    if not text or not text[:4].isdigit():
        return None
    parts = (text.split("-") + ["", ""])[:3]
    month = int(parts[1]) if parts[1].isdigit() and 1 <= int(parts[1]) <= 12 else 7
    day = int(parts[2]) if parts[2].isdigit() and 1 <= int(parts[2]) <= 31 else 1
    try:
        return date(int(parts[0]), month, day if parts[1].isdigit() else 1)
    except ValueError:
        return date(int(parts[0]), month, 1)


def whole_years(start, end):
    return end.year - start.year - ((end.month, end.day) < (start.month, start.day))


def rate(player, league_id, today):
    born = parse_date(player["birthDate"])
    age = whole_years(born, today) if born else None
    first_year = min(int(h["from"][:4]) for h in player["teamHistory"]) if player["teamHistory"] else today.year
    years = min(EXPERIENCE_MAX, today.year - first_year)
    joined = parse_date(player["joinedTeam"])
    stint = min(3, whole_years(joined, today)) if joined else 0
    intl = sum(1 for h in player["honors"] if h.get("eventTier") == "international")
    sub = player["status"] == "sub"

    why = {
        "league": LEAGUE_BASE[league_id],
        "experience": years,
        "international": round(INTERNATIONAL_FACTOR * math.sqrt(intl)),
        "sub": -SUB_PENALTY if sub else 0,
        "age": (-(age - 29) if age is not None and age >= 30 else 0) + (-2 if age is not None and age < 19 else 0),
        "results": 0,  # filled when placements arrive (LiquipediaDB)
    }
    overall = clamp(sum(why.values()))

    raw = {}
    tilt = ROLE_TILT.get(player["role"], {})
    for a in ATTRIBUTES:
        v = overall + tilt.get(a, 0) + spread(player["id"], a, -3, 3)
        if a == "mechanics" and age is not None:
            v += 2 if age <= 21 else -min(6, 2 * max(0, age - 27))
        if a == "gameKnowledge":
            v += (-3 if age is not None and age <= 20 else 0) + years
        if a == "consistency":
            v += (-4 if age is not None and age < 19 else 0) + stint - (2 if sub else 0)
        raw[a] = v
    shift = overall - statistics.mean(raw.values())  # keep the average of the five equal to overall
    attrs = {a: clamp(round(v + shift)) for a, v in raw.items()}

    if age is None:
        growth = UNKNOWN_AGE_GROWTH
    elif age <= 22:
        growth = GROWTH.get(age, GROWTH[17]) + spread(player["id"], "potential", 0, 4)
    else:
        growth = 0
    potential = max(overall, min(POTENTIAL_MAX, overall + growth)) if growth else overall

    return {"overall": overall, **attrs, "potential": potential, "age": age, "why": why}


def main():
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    today = date.fromisoformat(snap["meta"]["snapshotDate"])
    league_of_team = {t["id"]: t["leagueId"] for t in snap["teams"]}
    region_tier = {l["id"]: (l["region"], 1 if l["tier"] == 1 else 2) for l in snap["leagues"]}

    ratings = {p["id"]: rate(p, league_of_team[p["teamId"]], today) for p in snap["players"]}
    out = {"meta": {"rulesVersion": RULES_VERSION, "snapshotDate": snap["meta"]["snapshotDate"]}, "players": ratings}
    text = json.dumps(out, ensure_ascii=False, separators=(",", ":"))

    # ---- checks (docs/rating-rules-draft.md, "Checks before the rules are accepted")
    failures = []
    for pid, r in ratings.items():
        values = [r["overall"], r["potential"]] + [r[a] for a in ATTRIBUTES]
        if not all(1 <= v <= 99 for v in values):
            failures.append(f"out of range: {pid}")
        if r["potential"] < r["overall"]:
            failures.append(f"potential below overall: {pid}")
        if abs(statistics.mean(r[a] for a in ATTRIBUTES) - r["overall"]) > 1:
            failures.append(f"attribute average differs from overall by more than 1: {pid}")
    again = {p["id"]: rate(p, league_of_team[p["teamId"]], today) for p in snap["players"]}
    if again != ratings:
        failures.append("second run gave different ratings")
    by_league = {}
    for p in snap["players"]:
        by_league.setdefault(league_of_team[p["teamId"]], []).append((ratings[p["id"]]["overall"], p["handle"]))
    medians = {lid: statistics.median(v for v, _ in rows) for lid, rows in by_league.items()}
    for region in {r for r, _ in region_tier.values()}:
        top = [lid for lid, (r, t) in region_tier.items() if r == region and t == 1]
        second = [lid for lid, (r, t) in region_tier.items() if r == region and t == 2]
        if top and second and medians[top[0]] <= medians[second[0]]:
            failures.append(f"{region}: top league median not above second league median")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"Wrote {OUT}: {len(text) / 1024:.0f} KB | players {len(ratings)}")
    print("Checks:", "all passed" if not failures else f"{len(failures)} FAILED")
    for f in failures[:20]:
        print("  FAIL:", f)

    # ---- report for a human check
    handle = {p["id"]: p["handle"] for p in snap["players"]}
    team = {p["id"]: p["teamId"] for p in snap["players"]}
    print("\nMedian overall by league:", {k: medians[k] for k in LEAGUE_BASE})
    print("\nTop 30 overall:")
    top = sorted(ratings.items(), key=lambda kv: (-kv[1]["overall"], -kv[1]["potential"], handle[kv[0]].lower()))[:30]
    for pid, r in top:
        print(f"  {r['overall']:3} {handle[pid]:14} {team[pid]:22} age {r['age']}  "
              + " ".join(f"{a[:4]} {r[a]}" for a in ATTRIBUTES) + f"  pot {r['potential']}")
    print("\nTop 10 potential (age 22 or less):")
    young = sorted(((r["potential"], r["overall"], handle[pid], team[pid], r["age"]) for pid, r in ratings.items()
                    if r["age"] is not None and r["age"] <= 22), reverse=True)[:10]
    for row in young:
        print(f"  pot {row[0]} overall {row[1]} {row[2]} ({row[3]}, age {row[4]})")
    print("\nBottom 3 of each league:")
    for lid in LEAGUE_BASE:
        rows = sorted(by_league[lid])[:3]
        print(f"  {lid:7} " + ", ".join(f"{h} {v}" for v, h in rows))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
