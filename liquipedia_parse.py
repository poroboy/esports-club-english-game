#!/usr/bin/env python3
"""Parse cached Liquipedia wikitext (Stage 1a). Reads files in cache/pages only; sends no requests.

Reads: team and player infoboxes, tournament rosters ({{TeamParticipants}} and the older
{{TeamCard}}), and placements from {{TeamPrizePool}}.
"""
import json
import re
import sys
from pathlib import Path


def _template_start(text, name, pos=0):
    """Index of the next '{{name' whose name ends there (so 'TeamParticipants' does not match
    'TeamParticipantsControls'), or -1."""
    pattern = re.compile(r"\{\{\s*" + re.escape(name) + r"\s*(?=[|}\n])", re.IGNORECASE)
    m = pattern.search(text, pos)
    return m.start() if m else -1


def find_template(text, name):
    """Return the inner text of the first {{name ...}} template (nested templates allowed), or None."""
    start = _template_start(text, name)
    if start < 0:
        return None
    depth, i = 0, start
    while i < len(text) - 1:
        pair = text[i:i + 2]
        if pair == "{{":
            depth += 1
            i += 2
        elif pair == "}}":
            depth -= 1
            i += 2
            if depth == 0:
                return text[start + 2:i - 2]
        else:
            i += 1
    return None


def split_top_level(body):
    """Split on '|' that are not inside {{ }} or [[ ]]."""
    parts, buf, depth_t, depth_l, i = [], [], 0, 0, 0
    while i < len(body):
        pair = body[i:i + 2]
        if pair == "{{":
            depth_t += 1
            buf.append(pair)
            i += 2
        elif pair == "}}":
            depth_t -= 1
            buf.append(pair)
            i += 2
        elif pair == "[[":
            depth_l += 1
            buf.append(pair)
            i += 2
        elif pair == "]]":
            depth_l -= 1
            buf.append(pair)
            i += 2
        elif body[i] == "|" and depth_t == 0 and depth_l == 0:
            parts.append("".join(buf))
            buf = []
            i += 1
        else:
            buf.append(body[i])
            i += 1
    parts.append("".join(buf))
    return parts


def parse_infobox(text, name):
    """Return {key: value} for {{name ...}}; None if the template is not on the page."""
    body = find_template(text, name)
    if body is None:
        return None
    fields = {}
    for part in split_top_level(body)[1:]:
        if "=" in part:
            key, value = part.split("=", 1)
            fields[key.strip()] = value.strip()
    return fields


def parse_team_page(entry):
    """entry = one cache file. Returns the facts the snapshot needs from a team page."""
    if entry.get("missing") or not entry.get("content"):
        return None
    info = parse_infobox(entry["content"], "Infobox team") or {}
    return {
        "name": info.get("name"),
        "tag": info.get("abbreviation"),  # not always present; never guessed
        "country": info.get("location"),
        "region": info.get("region"),
        "league": info.get("league"),
        "page": entry["title"],
    }


def parse_player_page(entry):
    """Facts from {{Infobox player}}. Real names are deliberately not read (handle only, see spec)."""
    if entry.get("missing") or not entry.get("content"):
        return None
    info = parse_infobox(entry["content"], "Infobox player") or {}
    role = (info.get("role") or info.get("roles") or "").split(",")[0].strip().lower()
    return {
        "handle": info.get("id"),
        "birthDate": info.get("birth_date") or None,  # may be partial; kept as shown
        "nationality": info.get("country") or None,
        "role": ROLE_MAP.get(role),
        "status": (info.get("status") or "").lower() or None,
        "page": entry["title"],
    }


ROLE_MAP = {"top": "top", "jgl": "jungle", "jg": "jungle", "jungle": "jungle", "mid": "mid",
            "bot": "bot", "adc": "bot", "sup": "support", "supp": "support", "support": "support"}
STAFF_WORDS = ("coach", "analyst", "manager", "staff", "assistant", "strategic")


def _section(text, heading):
    """Text of '==heading==' up to the next level-2 heading."""
    m = re.compile(r"^==[^=\n]*" + heading + r"[^=\n]*==\s*$", re.M).search(text)  # heading text inside
    if not m:
        return None
    nxt = re.compile(r"\n==[^=]").search(text, m.end())  # level-2 only, not ===
    return text[m.start():nxt.start() if nxt else len(text)]


def parse_person(body):
    """body = inner text of {{Person|...}}. Returns a dict, or None for staff / unreadable entries."""
    handle, fields = None, {}
    for part in split_top_level(body)[1:]:
        if "=" in part.split("[[")[0]:
            key, value = part.split("=", 1)
            fields[key.strip()] = value.strip()
        elif part.strip():
            handle = part.strip()
    roles = [r.strip().lower() for r in fields.get("role", "").split(",")]
    role = next((ROLE_MAP[r] for r in roles if r in ROLE_MAP), None)
    is_staff = fields.get("type") == "staff" or (
        role is None and any(w in r for r in roles for w in STAFF_WORDS))  # staff without type=staff
    if is_staff or not handle:
        return None
    return {
        "handle": handle,
        "role": role,  # None when Liquipedia gives no playing role; never guessed
        "status": {"sub": "sub", "former": "former"}.get(fields.get("status"), "starter"),
        "captain": "captain" in roles,
        "page": fields.get("link", handle).replace("_", " "),
    }


def _templates(text, name):
    """Yield the inner text of every top-level {{name ...}} found in text."""
    pos = 0
    while True:
        i = _template_start(text, name, pos)
        if i < 0:
            return
        body = find_template(text[i:], name)
        if body is None:
            return
        yield body
        pos = i + len(body) + 4


def _fields(body):
    """Named fields of a template body as {key: value} (positional parts are skipped)."""
    fields = {}
    for part in split_top_level(body)[1:]:
        if "=" in part.split("{{")[0].split("[[")[0]:
            key, value = part.split("=", 1)
            fields[key.strip()] = value.strip()
    return fields


def _participants_new(section):
    """{{TeamParticipants}} format (2025 onwards). All blocks in the section are read."""
    teams = []
    for outer in _templates(section, "TeamParticipants"):
        for opp in split_top_level(outer)[1:]:
            opp = opp.strip()
            if _template_start(opp, "Opponent") != 0:
                continue
            parts = split_top_level(find_template(opp, "Opponent"))
            players = []
            for part in parts[2:]:
                if part.strip().startswith("players"):
                    for person in _templates(part, "Person"):
                        p = parse_person(person)
                        if p:
                            p["roleSource"] = "liquipedia" if p["role"] else None
                            players.append(p)
            teams.append({"team": parts[1].strip(), "players": players})
    return teams


ORDER_ROLES = ["top", "jungle", "mid", "bot", "support"]  # Liquipedia convention for TeamCard p1-p5


def _teamcard_player(handle, link, role, status, role_source):
    return {"handle": handle, "role": role, "status": status, "captain": False,
            "page": (link or handle).replace("_", " "), "roleSource": role_source}


def _participants_old(section):
    """{{TeamCard}} format (up to 2025). p1-p5 = starters in role order; tN blocks = subs, former or staff."""
    teams = []
    for body in _templates(section, "TeamCard"):
        f = _fields(body)
        if not f.get("team"):
            continue
        players = []
        n = 1
        while f.get(f"p{n}") is not None or f.get(f"p{n + 1}") is not None:
            handle = f.get(f"p{n}")
            if handle:
                pos = ROLE_MAP.get(f.get(f"pos{n}", "").strip().lower())
                if pos:
                    role, src = pos, "liquipedia"
                elif n <= 5:
                    role, src = ORDER_ROLES[n - 1], "order"
                else:
                    role, src = None, None
                if f.get(f"p{n}leave", "").lower() == "true":
                    status = "former"  # left the team during the season
                else:
                    status = "starter" if n <= 5 else "sub"
                players.append(_teamcard_player(handle, f.get(f"p{n}link"), role, status, src))
            n += 1
        for t in range(2, 10):
            title = f.get(f"t{t}title", "").lower()
            if "staff" in title or "coach" in title:
                continue
            status = "former" if "former" in title else "sub"
            n = 1
            while f.get(f"t{t}p{n}") is not None or f.get(f"t{t}p{n + 1}") is not None:
                handle = f.get(f"t{t}p{n}")
                pos = f.get(f"t{t}pos{n}", "").strip().lower()
                if handle and (pos in ROLE_MAP or not pos):  # any other pos is staff (coach, analyst ...)
                    role = ROLE_MAP.get(pos)
                    players.append(_teamcard_player(handle, f.get(f"t{t}p{n}link"), role, status,
                                                    "liquipedia" if role else None))
                n += 1
        teams.append({"team": f["team"], "teamPage": f.get("link") or None, "players": players})
    return teams


def parse_participants(entry):
    """Teams and players from the ==Participating Teams== section of a tournament page.
    Returns [{"team": name as written on the page, "players": [...]}]; staff are left out.
    roleSource: "liquipedia" (written on the page), "order" (TeamCard p1-p5 convention) or None."""
    if entry.get("missing") or not entry.get("content"):
        return None
    section = _section(entry["content"], "Participa")  # "Participants", "Top 12 Participants", "Participating Teams ..."
    if section is None:
        return None
    teams = _participants_new(section)
    if not teams:
        teams = _participants_old(section)
    return teams or None


def parse_placements(entry):
    """Placements from {{TeamPrizePool}}. Slots are in order; a slot with several opponents is a
    shared place. Slots filled automatically from a bracket have no opponent in the wikitext: they
    still take their place number, so those teams are simply missing (never guessed).
    Returns [{"team": opponent as written, "placement": int}] or None."""
    if entry.get("missing") or not entry.get("content"):
        return None
    body = find_template(entry["content"], "TeamPrizePool")
    if body is None:
        return None
    result, place = [], 1
    for part in split_top_level(body)[1:]:
        part = part.strip()
        if _template_start(part, "Slot") != 0:
            continue
        slot = find_template(part, "Slot")
        opponents = []
        for opp in _templates(slot, "Opponent"):
            parts = split_top_level(opp)
            if len(parts) > 1 and "=" not in parts[1]:
                opponents.append(parts[1].strip())
        for name in opponents:
            result.append({"team": name, "placement": place})
        place += max(1, len(opponents))
    return result


if __name__ == "__main__":
    # usage: python liquipedia_parse.py team|player|participants|placements <cache files...>
    mode, files = sys.argv[1], sys.argv[2:]
    for path in files:
        entry = json.loads(Path(path).read_text(encoding="utf-8"))
        if mode == "team":
            print(entry["title"], "->", parse_team_page(entry))
        elif mode == "player":
            print(entry["title"], "->", parse_player_page(entry))
        elif mode == "placements":
            print(json.dumps(parse_placements(entry), ensure_ascii=False))
        else:
            print(json.dumps(parse_participants(entry), ensure_ascii=False, indent=1))
