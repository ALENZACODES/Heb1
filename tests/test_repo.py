"""Repository rules: catalog is valid and in sync, vendored folders carry licences, no big files."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRIES = json.loads((ROOT / "catalog" / "catalog.json").read_text(encoding="utf-8"))["entries"]
NONCOMMERCIAL = ("-NC", "NC-", "non-commercial")


def test_catalog_fields():
    ids = set()
    for e in ENTRIES:
        for k in ("id", "name", "type", "task", "license", "license_source", "commercial", "how", "url"):
            assert e.get(k), (e.get("id"), k)
        assert e["id"] not in ids
        ids.add(e["id"])
        assert e["commercial"] in ("yes", "no", "unclear", "conditional")
        assert e["how"] in ("vendored", "linked")
        assert e["url"].startswith(("https://", "http://"))
        if any(x in e["license"] for x in NONCOMMERCIAL):
            assert e["commercial"] in ("no", "conditional"), e["id"]


def test_noncommercial_and_unclear_never_vendored():
    for e in ENTRIES:
        if e["commercial"] in ("no", "unclear", "conditional"):
            assert e["how"] == "linked", e["id"]


def test_vendored_folders_have_licence_and_attribution():
    vend = [e for e in ENTRIES if e["how"] == "vendored"]
    assert vend
    for e in vend:
        d = ROOT / "vendor" / e["id"]
        assert (d / "LICENSE").exists(), d
        att = (d / "ATTRIBUTION.md").read_text(encoding="utf-8")
        for f in d.glob("*.traineddata"):
            assert hashlib.sha256(f.read_bytes()).hexdigest() in att, f


def test_catalog_and_readme_in_sync():
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "build_catalog.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


def test_no_file_over_50mb_and_no_tetragrammaton_in_text():
    name = "\u05D9\u05D4\u05D5\u05D4"
    for p in ROOT.rglob("*"):
        if ".git" in p.parts or not p.is_file() or "downloads" in p.parts or ".pytest_cache" in p.parts:
            continue
        assert p.stat().st_size < 50 * 1024 * 1024, p
        if p.suffix in (".md", ".py", ".json", ".txt", ".yml", ".toml"):
            assert name not in p.read_text(encoding="utf-8", errors="ignore"), p


def test_fetch_plans_point_to_original_sources():
    sys.path.insert(0, str(ROOT / "fetch"))
    import fetch
    for e in ENTRIES:
        f = e.get("fetch")
        if not f or f["kind"] == "zenodo":
            continue
        for url, _ in fetch.plan(e):
            assert url.startswith(("https://huggingface.co/", "https://github.com/")), url
    assert fetch.needs_consent(next(e for e in ENTRIES if e["id"] == "sofer-mahir"))
