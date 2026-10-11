#!/usr/bin/env python3
"""Fetch raw wikitext from Liquipedia's MediaWiki API, politely, and cache it on disk.

This script follows Liquipedia's API Terms of Use (read on 2026-10-11).
Read the current terms again before every big run: https://liquipedia.net/api-terms-of-use

What it does:
  - Uses the MediaWiki API only (action=query). It never opens normal HTML pages and
    never uses action=parse.
  - Sends a custom User-Agent with the project name and your contact email (config.json).
  - Waits at least 2 seconds between requests (default 2.5 s).
  - Asks for gzip and re-uses one HTTP session.
  - Caches every page on disk. A cached page (even a missing one) is never requested again.
  - Stops at the first HTTP or API error. It never retries in a loop.
  - Has a request cap per run (--max-requests) so a bug cannot flood the server.

What it does not do: parse the wikitext. Parsing is a separate step.
"""
import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

API_URL = "https://liquipedia.net/leagueoflegends/api.php"
MIN_DELAY = 2.0  # seconds; Liquipedia asks for no more than 1 request per 2 seconds


class StopRun(Exception):
    """The run must stop (HTTP error, API error, network error)."""


def load_config(path):
    p = Path(path)
    if not p.exists():
        raise SystemExit(
            f"Config file not found: {path}\n"
            "Copy config.example.json to config.json and put your contact email in it."
        )
    cfg = json.loads(p.read_text(encoding="utf-8"))
    email = str(cfg.get("contact_email", "")).strip()
    if "@" not in email or "PUT-YOUR" in email.upper():
        raise SystemExit("config.json: set contact_email to a real email address (Liquipedia asks for contact information).")
    name = str(cfg.get("project_name", "EsportsClubEnglishGame")).strip()
    version = str(cfg.get("project_version", "0.1")).strip()
    url = str(cfg.get("project_url", "")).strip()
    cfg["user_agent"] = f"{name}/{version} ({url}; {email})"
    cfg["delay_seconds"] = max(float(cfg.get("delay_seconds", 2.5)), MIN_DELAY)
    cfg["batch_size"] = max(1, min(int(cfg.get("batch_size", 10)), 50))
    cfg.setdefault("cache_dir", "cache")
    return cfg


def normalize_title(title):
    t = title.strip().replace("_", " ")
    return t[:1].upper() + t[1:] if t else t


def cache_file(cache_dir, title):
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", title).strip("_") or "page"
    digest = hashlib.sha1(title.encode("utf-8")).hexdigest()[:8]
    return Path(cache_dir) / "pages" / f"{safe}_{digest}.json"


def make_session(cfg):
    s = requests.Session()
    s.headers.update({"User-Agent": cfg["user_agent"], "Accept-Encoding": "gzip"})
    return s


def _resolve(title, normalized, redirects):
    t = normalized.get(title, title)
    for _ in range(5):
        if t in redirects:
            t = redirects[t]
        else:
            break
    return t


def fetch_batch(session, titles):
    """One API request for several titles. Returns a list of cache entries."""
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "revisions",
        "rvprop": "ids|timestamp|content",
        "rvslots": "main",
        "redirects": "1",
        "titles": "|".join(titles),
    }
    try:
        resp = session.get(API_URL, params=params, timeout=60)
    except requests.RequestException as exc:
        raise StopRun(f"Network error: {exc}")
    if resp.status_code != 200:
        retry = resp.headers.get("Retry-After")
        extra = f" (Retry-After: {retry})" if retry else ""
        raise StopRun(
            f"HTTP {resp.status_code} from Liquipedia{extra}. Stopping. "
            "Wait a good while before trying again; do not hammer the server."
        )
    try:
        data = resp.json()
    except ValueError:
        raise StopRun("The response was not JSON. Stopping.")
    if "error" in data:
        raise StopRun(f"API error: {data['error']}")

    query = data.get("query", {})
    normalized = {n["from"]: n["to"] for n in query.get("normalized", [])}
    redirects = {r["from"]: r["to"] for r in query.get("redirects", [])}
    pages = {p.get("title"): p for p in query.get("pages", [])}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    entries = []
    for requested in titles:
        final = _resolve(requested, normalized, redirects)
        page = pages.get(final)
        entry = {
            "requested_title": requested,
            "title": final,
            "missing": True,
            "revid": None,
            "revision_timestamp": None,
            "fetched_at": now,
            "api": API_URL,
            "content": None,
        }
        if page and not page.get("missing") and not page.get("invalid") and page.get("revisions"):
            rev = page["revisions"][0]
            entry["missing"] = False
            entry["revid"] = rev.get("revid")
            entry["revision_timestamp"] = rev.get("timestamp")
            entry["content"] = rev.get("slots", {}).get("main", {}).get("content")
        entries.append(entry)
    return entries


def run(titles, cfg, session=None, max_requests=5, dry_run=False, sleep=time.sleep, clock=time.monotonic):
    cache_dir = cfg["cache_dir"]
    already = [t for t in titles if cache_file(cache_dir, t).exists()]
    already_set = set(already)
    todo = [t for t in titles if t not in already_set]
    size = cfg["batch_size"]
    batches = [todo[i:i + size] for i in range(0, len(todo), size)]

    print(f"Titles asked: {len(titles)} | already cached: {len(already)} | to fetch: {len(todo)} "
          f"| requests needed: {len(batches)}")
    if dry_run:
        for i, b in enumerate(batches, 1):
            print(f"  request {i}: {b}")
        return {"fetched": 0, "missing": 0}
    if not batches:
        print("Nothing to do.")
        return {"fetched": 0, "missing": 0}
    if len(batches) > max_requests:
        print(f"Request cap is {max_requests}. Only the first {max_requests} request(s) will run; "
              "run the script again to continue (cached pages are not requested again).")
        batches = batches[:max_requests]

    session = session or make_session(cfg)
    log_path = Path(cache_dir) / "requests.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    fetched = missing = 0
    last = None
    for n, batch in enumerate(batches, 1):
        if last is not None:
            wait = cfg["delay_seconds"] - (clock() - last)
            if wait > 0:
                sleep(wait)
        last = clock()
        entries = fetch_batch(session, batch)
        for e in entries:
            path = cache_file(cache_dir, e["requested_title"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(e, ensure_ascii=False, indent=1), encoding="utf-8")
            if e["missing"]:
                missing += 1
            else:
                fetched += 1
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                "titles": batch}, ensure_ascii=False) + "\n")
        print(f"request {n}/{len(batches)} done: {len(entries)} title(s)")
    print(f"Finished. Fetched: {fetched} | not found: {missing}")
    return {"fetched": fetched, "missing": missing}


def collect_titles(args):
    titles = list(args.titles or [])
    if args.seeds:
        data = json.loads(Path(args.seeds).read_text(encoding="utf-8"))
        titles += data.get("titles", [])
    seen, out = set(), []
    for t in titles:
        n = normalize_title(t)
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Fetch and cache raw wikitext from Liquipedia (API only).")
    ap.add_argument("--config", default="config.json")
    ap.add_argument("--seeds", help="JSON file with a list called titles")
    ap.add_argument("--titles", nargs="*", help="page titles given directly")
    ap.add_argument("--max-requests", type=int, default=5, help="cap on API requests in this run (default 5)")
    ap.add_argument("--dry-run", action="store_true", help="show what would be requested, send nothing")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    titles = collect_titles(args)
    if not titles:
        raise SystemExit("No titles. Use --seeds seeds_pilot.json or --titles ...")
    print(f"User-Agent: {cfg['user_agent']}")
    try:
        run(titles, cfg, max_requests=args.max_requests, dry_run=args.dry_run)
    except StopRun as exc:
        print(f"STOPPED: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
