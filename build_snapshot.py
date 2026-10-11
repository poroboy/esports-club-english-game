#!/usr/bin/env python3
"""Build the game snapshot (format v0.1, see esports-club-game-spec.md) from cached Liquipedia pages.

Reads cache/pages only and sends no requests. Writes data/snapshot.json.
Decisions agreed for Stage 1a (2026-10-11):
  - placements are not in the wikitext; they stay null until LiquipediaDB is used
  - honors: one entry per Worlds / MSI / First Stand roster appearance, placement null (Stage 1b decision)
  - tag: Liquipedia abbreviation or null; parentTeamId: null; debutYear: null
  - joinedTeam: start date of the first season of the player's current, unbroken stint in our data
    (2022 onwards, so a player who joined before 2022 gets a date that is too late)
  - Royal Never Give Up (LDL) has no roster on Liquipedia and is left out
  - league tier is the Liquipedia tier (LFL is tier 3 there)
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from liquipedia_fetch import normalize_title
from liquipedia_parse import parse_infobox, parse_participants, parse_placements

SNAPSHOT_DATE = "2026-10-11"
CACHE = Path("cache/pages")
OUT = Path("data/snapshot.json")

# short id, region, page of the league, latest season page(s); later pages are fallbacks for empty rosters
LEAGUES = [
    ("lck", "LCK", "LCK", ["LCK/2026"]),
    ("lck-cl", "LCK", "LCK Challengers League", ["LCK CL/2026"]),
    ("lpl", "LPL", "LPL", ["LPL/2026/Split 3", "LPL/2026/Split 2"]),
    ("ldl", "LPL", "LDL", ["LDL/2025/Split 3", "LDL/2025/Split 2/Stage 2", "LDL/2025/Split 2/Stage 1", "LDL/2025/Split 1"]),
    ("lec", "LEC", "LEC", ["LEC/2026/Summer"]),
    ("lfl", "LEC", "LFL", ["LFL/2026/Summer"]),
    ("lcs", "LCS", "LCS", ["LCS/2026/Summer"]),
    ("nacl", "LCS", "North American Challengers League", ["North American Challengers League/2026/Summer"]),
    ("lcp", "LCP", "LCP", ["LCP/2026/Split 3"]),
    ("ljl", "LCP", "LJL", ["LJL/2026/Summer Championship"]),
]
# LPL/2026/Split 3 lists 12 of the 14 LPL teams; the other two are taken from LPL/2026/Split 2.
# Oh My God is also listed in LDL/2025/Split 3, but its latest league is the LPL.
EXTRA_TEAMS = {"lpl": ["Ultra Prime", "Oh My God"]}
EXCLUDED_TEAMS = {"ldl": {"Royal Never Give Up", "Oh My God"}}  # RNG: no roster on Liquipedia
# season-page team names whose page title differs (found in phase D)
TEAM_PAGE_FIX = {
    "Nongshim Redforce": "Nongshim RedForce", "bro challengers": "BRION Challengers",
    "DRX challengers": "DRX Challengers", "fearx youth": "FEARX Youth",
    "Freecs challengers": "Freecs Challengers", "KT Rolster challengers": "KT Rolster Challengers",
    "ns challengers": "Nongshim RedForce Challengers", "blue otter": "Blue Otter", "Ground Zero": "Ground Zero Gaming",
}
INTERNATIONAL = ("World Championship/", "Mid-Season Invitational/", "First Stand Tournament/")

COUNTRY = {
    "south korea": "KR", "korea": "KR", "china": "CN", "taiwan": "TW", "hong kong": "HK", "japan": "JP",
    "vietnam": "VN", "thailand": "TH", "cambodia": "KH", "mongolia": "MN", "australia": "AU",
    "united states": "US", "canada": "CA", "mexico": "MX", "brazil": "BR", "argentina": "AR",
    "france": "FR", "germany": "DE", "spain": "ES", "united kingdom": "GB", "sweden": "SE", "denmark": "DK",
    "poland": "PL", "czech republic": "CZ", "bulgaria": "BG", "greece": "GR", "portugal": "PT", "belgium": "BE",
    "netherlands": "NL", "switzerland": "CH", "austria": "AT", "italy": "IT", "croatia": "HR", "slovenia": "SI",
    "serbia": "RS", "montenegro": "ME", "north macedonia": "MK", "romania": "RO", "lithuania": "LT",
    "ukraine": "UA", "turkey": "TR", "israel": "IL", "jordan": "JO", "algeria": "DZ", "dz": "DZ",
    "mauritius": "MU",
}


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def norm(name):
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


def country_code(value, unknown):
    if not value:
        return None
    code = COUNTRY.get(value.strip().lower())
    if code is None:
        unknown[value] += 1
    return code


def load_cache():
    by_requested = {}
    for f in CACHE.glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        by_requested[d["requested_title"]] = d
        if not d["missing"]:
            by_requested.setdefault(d["title"], d)  # also findable by the title after redirects
    return by_requested


def entry(cache, title):
    d = cache.get(normalize_title(title))
    return None if d is None or d["missing"] else d


def main():
    cache = load_cache()
    unknown_country = Counter()
    warnings = []

    # ---- season pages (deduplicated by resolved title), with dates
    season_titles = json.loads(Path("seeds_phase_c.json").read_text(encoding="utf-8"))["titles"]
    seasons, seen = [], set()
    for t in season_titles:
        d = entry(cache, t)
        if d is None or d["title"] in seen:
            continue
        seen.add(d["title"])
        info = parse_infobox(d["content"], "Infobox league") or {}
        seasons.append({"page": d["title"], "sdate": info.get("sdate"), "edate": info.get("edate") or info.get("sdate"),
                        "rosters": parse_participants(d) or [], "placements": parse_placements(d) or [],
                        "international": d["title"].startswith(INTERNATIONAL)})
    seasons.sort(key=lambda s: s["sdate"] or "")

    # ---- leagues and current teams
    leagues, teams, team_alias = [], [], {}
    current_rosters = []  # (team_id, league_tier, [players])
    for lid, region, page, latest in LEAGUES:
        d = entry(cache, page)
        info = (parse_infobox(d["content"], "Infobox league") or parse_infobox(d["content"], "Infobox series") or {})
        tier = int(info["liquipediatier"]) if str(info.get("liquipediatier", "")).isdigit() else None
        leagues.append({"id": lid, "name": info.get("name") or d["title"], "region": region, "tier": tier,
                        "page": d["title"]})
        first = parse_participants(entry(cache, latest[0])) or []
        names = [((x.get("teamPage") or x["team"]).strip(), x["team"].strip()) for x in first]
        names += [(n, n) for n in EXTRA_TEAMS.get(lid, [])]
        for page_name, roster_name in names:
            if roster_name in EXCLUDED_TEAMS.get(lid, ()):
                continue
            td = entry(cache, TEAM_PAGE_FIX.get(page_name, page_name))
            if td is None:
                warnings.append(f"team page not found: {page_name}")
                continue
            tinfo = parse_infobox(td["content"], "Infobox team") or {}
            tid = slug(td["title"])
            teams.append({"id": tid, "name": tinfo.get("name") or td["title"], "tag": tinfo.get("abbreviation") or None,
                          "leagueId": lid, "country": country_code(tinfo.get("location"), unknown_country),
                          "parentTeamId": None, "lastSeasons": [], "page": td["title"]})
            for alias in (td["title"], td["requested_title"], page_name, roster_name, tinfo.get("name")):
                if alias:
                    team_alias[norm(alias)] = tid
            # current roster: latest season page that has players for this team
            for src in latest:
                rows = {x["team"].strip(): x for x in (parse_participants(entry(cache, src)) or [])}
                row = rows.get(roster_name)
                if row and row["players"]:
                    src_start = (parse_infobox(entry(cache, src)["content"], "Infobox league") or {}).get("sdate") or ""
                    current_rosters.append((tid, tier or 9, row["players"], src_start))
                    break
            else:
                warnings.append(f"no roster for {roster_name}")
    team_by_id = {t["id"]: t for t in teams}

    def resolve(name):
        return team_alias.get(norm(name))

    # ---- lastSeasons (league seasons only; placements are null unless written in the wikitext)
    for s in seasons:
        if s["international"]:
            continue
        place = {resolve(p["team"]): p["placement"] for p in s["placements"] if resolve(p["team"])}
        label = s["page"].replace("/", " ")
        for row in s["rosters"]:
            tid = resolve(row.get("teamPage") or row["team"]) or resolve(row["team"])
            if tid:
                team_by_id[tid]["lastSeasons"].append({"season": label, "placement": place.get(tid)})
    for t in teams:
        t["lastSeasons"].reverse()  # newest first

    # ---- player appearances over all seasons (for teamHistory and joinedTeam)
    # sort key: season start, then "former" before current (a player traded mid-season left that team first)
    appearances = defaultdict(list)  # player page -> [(sdate, edate, order, team name, team id)]
    honors = defaultdict(list)  # player page -> international events played (Worlds, MSI, First Stand)
    for s in seasons:
        edate = min(s["edate"] or s["sdate"], SNAPSHOT_DATE)  # a running season ends "now"
        for row in s["rosters"]:
            tid = resolve(row.get("teamPage") or row["team"]) or resolve(row["team"])
            tname = team_by_id[tid]["name"] if tid else (row.get("teamPage") or row["team"]).strip()
            for p in row["players"]:
                order = 0 if p["status"] == "former" else 1
                appearances[normalize_title(p["page"])].append((s["sdate"], edate, order, tname, tid))
                if s["international"] and p["status"] != "former":
                    event, year = s["page"].rsplit("/", 1)
                    honors[normalize_title(p["page"])].append(
                        {"event": f"{event} {year}", "year": int(year), "placement": None,
                         "eventTier": "international"})  # appearance only; placement waits for LiquipediaDB

    # ---- current players: one team each (newest roster first, then starter before sub, then higher league)
    chosen = {}
    for tid, tier, players, src_start in current_rosters:
        for p in players:
            if p["status"] == "former":
                continue
            key = normalize_title(p["page"])
            newest_first = "".join(chr(0x10FFFF - ord(c)) for c in src_start)  # sorts later dates first
            rank = (newest_first, 0 if p["status"] == "starter" else 1, tier)
            if key not in chosen or rank < chosen[key][0]:
                if key in chosen:
                    warnings.append(f"player on two teams: {p['handle']} ({chosen[key][1]} / {tid}); kept {tid}")
                chosen[key] = (rank, tid, p)

    players, used_ids = [], set()
    for key, (_, tid, p) in chosen.items():
        pd = entry(cache, key)
        pinfo = (parse_infobox(pd["content"], "Infobox player") or {}) if pd else {}
        # team history: consecutive appearances with the same team form one stint
        stints = []
        for sdate, edate, _, tname, atid in sorted(appearances.get(key, []), key=lambda a: (a[0] or "", a[2])):
            if stints and stints[-1]["team"] == tname:
                stints[-1]["to"] = max(stints[-1]["to"], (edate or sdate)[:7])
                continue
            stints.append({"team": tname, "from": sdate[:7], "to": (edate or sdate)[:7], "_start": sdate, "_tid": atid})
        joined = stints[-1]["_start"] if stints and stints[-1]["_tid"] == tid else None
        pid = slug(pd["title"] if pd else p["page"])
        while pid in used_ids:
            pid += "-2"
        used_ids.add(pid)
        role = p["role"] or {"jgl": "jungle", "sup": "support"}.get((pinfo.get("role") or pinfo.get("roles") or "").lower(),
                                                                   (pinfo.get("role") or pinfo.get("roles") or "").lower() or None)
        players.append({
            "id": pid, "handle": p["handle"],
            "nationality": country_code(pinfo.get("country"), unknown_country),
            "birthDate": pinfo.get("birth_date") or None,
            "role": role, "teamId": tid, "status": p["status"],
            "joinedTeam": joined, "debutYear": None,
            "teamHistory": [{k: v for k, v in s.items() if not k.startswith("_")} for s in stints],
            "honors": sorted(honors.get(key, []), key=lambda h: (-h["year"], h["event"])),
            "page": pd["title"] if pd else p["page"],
        })

    snapshot = {
        "meta": {"schemaVersion": "0.1", "snapshotDate": SNAPSHOT_DATE, "source": "Liquipedia", "license": "CC-BY-SA 3.0"},
        "leagues": leagues, "teams": teams, "players": players,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    size = OUT.stat().st_size
    print(f"Wrote {OUT}: {size / 1024:.0f} KB | leagues {len(leagues)} | teams {len(teams)} | players {len(players)}")
    filled = lambda k: sum(1 for p in players if p[k])
    print(f"players with nationality {filled('nationality')}, birthDate {filled('birthDate')}, role {filled('role')}, "
          f"joinedTeam {filled('joinedTeam')}, teamHistory {filled('teamHistory')}")
    print(f"teams with tag {sum(1 for t in teams if t['tag'])}, with any placement "
          f"{sum(1 for t in teams if any(s['placement'] for s in t['lastSeasons']))}")
    if unknown_country:
        print("country values not converted:", dict(unknown_country))
    for w in warnings:
        print("WARNING:", w)


if __name__ == "__main__":
    sys.exit(main())
