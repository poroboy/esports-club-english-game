#!/usr/bin/env python3
"""Probe: list page titles that start with a prefix (MediaWiki list=allpages).

Sends ONE request per prefix (at most 500 titles each, no auto-continue), waits delay_seconds between requests, then caches the answer in cache/discovery/. If the answer is already
cached, it sends nothing. It reuses the config, User-Agent and error handling of liquipedia_fetch.py.
Example: python liquipedia_probe.py --prefix LCK/2026 LPL/2026 (one request per prefix)
--namespace takes a number or a name (e.g. Match). A name is looked up in the wiki's namespace
list (meta=siteinfo), which costs one extra request the first time and is cached after that.
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

from liquipedia_fetch import API_URL, StopRun, load_config, make_session


class Probe:
    """One HTTP session; at least delay_seconds between two requests."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.session = make_session(cfg)
        self.last = None
        self.dir = Path(cfg["cache_dir"]) / "discovery"

    def _get(self, params):
        if self.last is not None:
            wait = self.cfg["delay_seconds"] - (time.monotonic() - self.last)
            if wait > 0:
                time.sleep(wait)
        self.last = time.monotonic()
        try:
            resp = self.session.get(API_URL, params=params, timeout=60)
        except Exception as exc:
            raise StopRun(f"Network error: {exc}")
        if resp.status_code != 200:
            raise StopRun(f"HTTP {resp.status_code} from Liquipedia. Stopping, no retry.")
        try:
            data = resp.json()
        except ValueError:
            raise StopRun("The response was not JSON. Stopping.")
        if "error" in data:
            raise StopRun(f"API error: {data['error']}")
        return data

    def _cached(self, name, fetch):
        path = self.dir / name
        if path.exists():
            print(f"Already cached: {path} (no request sent)")
            return json.loads(path.read_text(encoding="utf-8"))
        result = fetch()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
        return result

    def namespaces(self):
        """{name: number} for every namespace of the wiki (meta=siteinfo)."""
        def fetch():
            data = self._get({"action": "query", "format": "json", "formatversion": "2",
                              "meta": "siteinfo", "siprop": "namespaces"})
            return {ns.get("name", ""): ns["id"] for ns in data["query"]["namespaces"].values()}
        return self._cached("siteinfo_namespaces.json", fetch)

    def allpages(self, prefix, namespace=0, limit=500):
        suffix = "" if namespace == 0 else f"_ns{namespace}"
        name = re.sub(r"[^A-Za-z0-9._-]+", "_", prefix) + suffix + ".json"

        def fetch():
            data = self._get({"action": "query", "format": "json", "formatversion": "2",
                              "list": "allpages", "apprefix": prefix,
                              "apnamespace": str(namespace), "aplimit": str(limit)})
            titles = [p["title"] for p in data.get("query", {}).get("allpages", [])]
            return {"prefix": prefix, "namespace": namespace, "titles": titles, "more": "continue" in data}
        return self._cached(name, fetch)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prefix", required=True, nargs="+", help="one or more prefixes; one request each")
    ap.add_argument("--namespace", default="0", help="namespace number or name (default 0 = articles)")
    ap.add_argument("--config", default="config.json")
    args = ap.parse_args()
    probe = Probe(load_config(args.config))
    try:
        if args.namespace.isdigit():
            ns = int(args.namespace)
        else:
            table = probe.namespaces()
            if args.namespace not in table:
                print(f"Namespace {args.namespace!r} not found. Known: {sorted(table)}")
                sys.exit(1)
            ns = table[args.namespace]
            print(f"Namespace {args.namespace!r} = {ns}")
        for prefix in args.prefix:
            result = probe.allpages(prefix, ns)
            print(f"[{prefix}] {len(result['titles'])} title(s); more available: {result['more']}")
            for t in result["titles"][:30]:
                print("  ", t)
    except StopRun as exc:
        print(f"STOPPED: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
