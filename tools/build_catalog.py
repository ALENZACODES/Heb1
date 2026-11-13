#!/usr/bin/env python3
"""Write catalog/catalog.json from tools/catalog_src.py and refresh the tables in README.md.

  python tools/build_catalog.py           write both
  python tools/build_catalog.py --check   exit 1 if either is out of date (used by CI)
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from catalog_src import CATALOG  # noqa: E402

START, END = "<!-- catalog:start -->", "<!-- catalog:end -->"
SECTIONS = [("engine", "Engines"), ("model", "Models"), ("dataset", "Datasets"), ("tool", "Tools"),
            ("font", "Fonts for synthetic training data"), ("service", "Web services (not open licences)"),
            ("list", "Other lists")]
COMMERCIAL = {"yes": "yes", "no": "**no**", "unclear": "unclear", "conditional": "conditional"}


def catalog_json() -> str:
    return json.dumps({"checked": "2026-11-12", "entries": CATALOG}, ensure_ascii=False, indent=1) + "\n"


def tables() -> str:
    c = Counter(e["how"] for e in CATALOG)
    out = [f"{len(CATALOG)} resources: {c['vendored']} vendored in this repo, {c['linked']} linked "
           "(fetched from the original source with `fetch/fetch.py`). Licences as stated by each source, checked 2026-11-12.", ""]
    for key, title in SECTIONS:
        rows = [e for e in CATALOG if e["type"] == key]
        if not rows:
            continue
        out += [f"### {title}", "", "| Name | Use | Licence | Commercial use | In repo |", "|---|---|---|---|---|"]
        for e in rows:
            out.append(f"| [{e['name']}]({e['url']}) | {e['task']} | {e['license']} | {COMMERCIAL[e['commercial']]} | "
                       f"{'vendored' if e['how'] == 'vendored' else 'link'} |")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def readme_with(text: str) -> str:
    a, b = text.index(START) + len(START), text.index(END)
    return text[:a] + "\n" + tables() + text[b:]


def main() -> int:
    cj, rd = ROOT / "catalog" / "catalog.json", ROOT / "README.md"
    new_cj, new_rd = catalog_json(), readme_with(rd.read_text(encoding="utf-8"))
    if "--check" in sys.argv:
        ok = cj.read_text(encoding="utf-8") == new_cj and rd.read_text(encoding="utf-8") == new_rd
        print("catalog up to date" if ok else "catalog out of date: run python tools/build_catalog.py")
        return 0 if ok else 1
    cj.write_text(new_cj, encoding="utf-8")
    rd.write_text(new_rd, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
