#!/usr/bin/env python3
"""Download a catalog resource from its ORIGINAL source and show its licence first.

  python fetch/fetch.py --list                  list fetchable ids
  python fetch/fetch.py ID [--dest DIR] [--yes] [--dry-run]

Nothing is mirrored by Heb1: files come straight from Hugging Face, Zenodo,
GitHub or the publisher. Resources whose licence is non-commercial or unclear
need --yes (or typing "yes") after the licence is shown, so you choose knowingly.
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog" / "catalog.json"
UA = {"User-Agent": "heb1-fetch (+https://github.com/ALENZACODES/Heb1)"}


def load():
    return {e["id"]: e for e in json.loads(CATALOG.read_text(encoding="utf-8"))["entries"]}


def _get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def plan(entry) -> list[tuple[str, str]]:
    """Return [(url, filename)] for an entry, without downloading anything big."""
    f = entry.get("fetch") or {}
    kind = f.get("kind")
    if kind == "url":
        return [(u, u.rsplit("/", 1)[-1]) for u in f["files"]]
    if kind in ("hf", "hf-dataset"):
        base = "https://huggingface.co/" + ("datasets/" if kind == "hf-dataset" else "") + f["repo"]
        return [(f"{base}/resolve/main/{urllib.parse.quote(p)}", p) for p in f["files"]]
    if kind == "zenodo":
        rec = _get_json(f"https://zenodo.org/api/records/{f['record']}")
        return [(x["links"]["self"], x["key"]) for x in rec.get("files", [])]
    if kind == "github":
        return [(f"https://github.com/{f['repo']}/archive/HEAD.zip", f["repo"].replace("/", "_") + ".zip")]
    return []


def needs_consent(entry) -> bool:
    return entry["commercial"] in ("no", "unclear", "conditional")


def show(entry):
    print(f"{entry['name']}  [{entry['id']}]")
    print(f"  source:     {entry['url']}")
    print(f"  licence:    {entry['license']}  (from: {entry['license_source']})")
    print(f"  commercial: {entry['commercial']}")
    if entry.get("notes"):
        print(f"  notes:      {entry['notes']}")


def download(url, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r, open(tmp, "wb") as out:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = r.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r  {dest.name}: {done * 100 // total}%", end="", file=sys.stderr)
    os.replace(tmp, dest)
    print(f"\r  {dest.name}: done ({done:,} bytes)", file=sys.stderr)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("id", nargs="?")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dest", default=str(ROOT / "downloads"))
    ap.add_argument("--yes", action="store_true", help="accept the shown licence without a prompt")
    ap.add_argument("--dry-run", action="store_true", help="show the licence and the files, download nothing")
    a = ap.parse_args(argv)
    cat = load()
    if a.list or not a.id:
        for e in cat.values():
            if e.get("fetch"):
                print(f"{e['id']:28} {e['commercial']:12} {e['license']}")
        return 0
    if a.id not in cat:
        print(f"unknown id {a.id!r}; see --list", file=sys.stderr)
        return 2
    e = cat[a.id]
    show(e)
    if e["how"] == "vendored":
        print("  This one is already in vendor/ in this repository.")
    items = plan(e)
    if not items:
        print("  No automatic download: open the source link above.")
        return 0
    for u, name in items:
        print(f"  file: {name}  <- {u}")
    if a.dry_run:
        return 0
    if needs_consent(e) and not a.yes:
        ans = input(f"Licence is '{e['license']}' (commercial use: {e['commercial']}). Download for your own use? [yes/N] ")
        if ans.strip().lower() != "yes":
            print("Not downloaded.")
            return 1
    target = Path(a.dest) / a.id
    for u, name in items:
        download(u, target / name)
    (target / "SOURCE.txt").write_text(
        f"{e['name']}\nsource: {e['url']}\nlicence: {e['license']} ({e['license_source']})\ncommercial use: {e['commercial']}\n",
        encoding="utf-8")
    print(f"Saved in {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
