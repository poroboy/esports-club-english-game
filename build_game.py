#!/usr/bin/env python3
"""Build the game page (Stage 2) from game/template.html, data/snapshot.json and data/ratings.json.

Writes two files in game/:
  esports-club-english-game.html  the page content for the Artifact tool (it adds the document skeleton)
  preview.html                    the same page with a document skeleton and a FAKE Claude stub, for
                                  looking at the screens in a local browser. Never publish this one.
Sends no requests.
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
TEMPLATE = ROOT / "game" / "template.html"
OUT = ROOT / "game" / "esports-club-english-game.html"
PREVIEW = ROOT / "game" / "preview.html"

STUB_FILE = ROOT / "game" / "preview_stub.html"


def main():
    snap = json.loads((ROOT / "data" / "snapshot.json").read_text(encoding="utf-8"))
    ratings = json.loads((ROOT / "data" / "ratings.json").read_text(encoding="utf-8"))
    data = json.dumps({"snapshot": snap, "ratings": ratings}, ensure_ascii=False, separators=(",", ":"))
    data = data.replace("</", "<\\/")  # keep the JSON from closing its script tag
    page = TEMPLATE.read_text(encoding="utf-8").replace("__GAME_DATA__", data)
    assert "__GAME_DATA__" not in page
    OUT.write_text(page, encoding="utf-8")
    wrapped = ('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
               "<style>body{margin:0}</style></head><body>" + STUB_FILE.read_text(encoding="utf-8") + page + "</body></html>")
    PREVIEW.write_text(wrapped, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)}: {OUT.stat().st_size / 1024:.0f} KB")
    print(f"Wrote {PREVIEW.relative_to(ROOT)} (local preview with a fake Claude, do not publish)")


if __name__ == "__main__":
    main()
