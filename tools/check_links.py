#!/usr/bin/env python3
"""Check that every catalog URL and every http(s) link in the Markdown files answers (no 404s).

  python tools/check_links.py
"""
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Sites that refuse automated clients (they answer 403 to scripts but work in a browser).
BOT_BLOCKED = ("www.nli.org.il",)
UA = {"User-Agent": "Mozilla/5.0 (heb1 link check; +https://github.com/ALENZACODES/Heb1)"}


def urls():
    found = {e["url"] for e in json.loads((ROOT / "catalog" / "catalog.json").read_text(encoding="utf-8"))["entries"]}
    for md in ROOT.rglob("*.md"):
        if ".git" in md.parts or "vendor" in md.parts:
            continue
        for u in re.findall(r"https?://[^\s)\]>`\"']+", md.read_text(encoding="utf-8")):
            found.add(u.rstrip(".,;"))
    return sorted(u for u in found if "<" not in u and "{" not in u)


def check(u):
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(u, headers=UA, method=method)
            with urllib.request.urlopen(req, timeout=30) as r:
                return u, r.status
        except urllib.error.HTTPError as e:
            if method == "GET" or e.code not in (403, 405, 429, 400, 501):
                return u, e.code
        except Exception as e:  # noqa: BLE001
            if method == "GET":
                return u, f"error: {e}"
    return u, "?"


def main():
    bad = []
    with ThreadPoolExecutor(8) as ex:
        for u, st in ex.map(check, urls()):
            ok = isinstance(st, int) and st < 400
            if not ok and st == 403 and any(h in u for h in BOT_BLOCKED):
                print(f"ok  403 (blocks scripts; checked in a browser) {u}")
                continue
            print(f"{'ok ' if ok else 'BAD'} {st} {u}")
            if not ok:
                bad.append((u, st))
    print(f"\n{len(bad)} bad link(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
