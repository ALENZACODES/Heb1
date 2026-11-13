"""heb1 command line.

  heb1 read IMAGE [options]      OCR an image and print clean right-to-left Hebrew text
  heb1 clean [FILE]              clean OCR text from a file or stdin
  heb1 strip-metadata IN OUT     re-save an image with pixels only
  heb1 doctor                    show which engines and models are available
"""
from __future__ import annotations

import argparse
import html
import json
import subprocess
import sys

from . import __version__
from .text import clean, for_display


def _read(args) -> int:
    from PIL import Image

    from .correct import Corrector
    from .ocr import OCRError, run_tesseract
    from .preprocess import Prep, prepare

    try:
        with Image.open(args.image) as im:
            prep = prepare(im, Prep(binarize=not args.no_binarize, deskew=args.deskew,
                                    line_height=args.line_height, upscale_to=args.upscale_to))
    except (OSError, ValueError) as e:
        print(f"heb1: cannot open image: {e}", file=sys.stderr)
        return 2
    if args.save_prep:
        prep.save(args.save_prep)
    try:
        res = run_tesseract(prep, model=args.model, psm=args.psm, tessdata_dir=args.tessdata_dir)
    except OCRError as e:
        print(f"heb1: {e}", file=sys.stderr)
        return 3
    fixer = Corrector.from_file(args.lexicon) if args.lexicon else None
    lines = []
    for ln in res.lines():
        toks = fixer.fix_words(ln) if fixer else [w.text for w in ln]
        lines.append(" ".join(toks))
    text = clean("\n".join(lines), finals=not args.no_finals, nikud=args.nikud)
    if args.format == "json":
        confs = [w.conf for w in res.words if w.conf >= 0]
        out = {"text": text, "lines": text.split("\n"), "engine": res.engine, "model": res.model,
               "words": len(res.words), "mean_conf": round(sum(confs) / len(confs), 1) if confs else None}
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif args.format == "html":
        body = "\n".join(f"  <p>{html.escape(l)}</p>" for l in text.split("\n"))
        print(f'<!doctype html>\n<html lang="he" dir="rtl"><meta charset="utf-8">\n<body>\n{body}\n</body></html>')
    else:
        print(for_display(text, mark=args.rtl_mark))
    return 0


def _clean(args) -> int:
    data = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    print(for_display(clean(data, finals=not args.no_finals, nikud=args.nikud), mark=args.rtl_mark))
    return 0


def _strip(args) -> int:
    from .preprocess import strip_metadata
    strip_metadata(args.src, args.dst)
    return 0


def _doctor(args) -> int:
    from .ocr import MODELS, VENDOR, tesseract_available
    print(f"heb1 {__version__}")
    if tesseract_available():
        v = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
        print("tesseract:", (v.stdout or v.stderr).splitlines()[0])
        langs = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True).stdout.split()
        print("installed heb:", "heb" in langs)
    else:
        print("tesseract: not found (apt install tesseract-ocr tesseract-ocr-heb, or brew install tesseract tesseract-lang)")
    for alias, (lang, folder) in MODELS.items():
        if folder:
            print(f"model {alias}: {'present' if (VENDOR / folder / (lang + '.traineddata')).exists() else 'missing'}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="heb1", description="Free Hebrew OCR: image in, clean RTL text out.")
    ap.add_argument("--version", action="version", version=f"heb1 {__version__}")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def text_opts(p):
        p.add_argument("--nikud", choices=["keep", "strip", "teamim"], default="keep",
                       help="keep vowel points, strip them, or strip only cantillation (teamim)")
        p.add_argument("--no-finals", action="store_true", help="do not fix final-letter forms")
        p.add_argument("--rtl-mark", action="store_true", help="start each Hebrew line with RLM for plain-text viewers")

    r = sub.add_parser("read", help="OCR an image")
    r.add_argument("image")
    r.add_argument("--model", default="heb", help="heb (default) | heb-fast | heocr-r8b | any tesseract language")
    r.add_argument("--psm", type=int, default=6, help="tesseract page mode: 6 block (default), 3 full page, 7 one line")
    r.add_argument("--tessdata-dir")
    r.add_argument("--lexicon", help="word list (one per line, most common first) for confidence-gated fixes")
    r.add_argument("--format", choices=["text", "json", "html"], default="text")
    r.add_argument("--no-binarize", action="store_true")
    r.add_argument("--deskew", action="store_true")
    r.add_argument("--line-height", type=int, default=48, help="rescale so text lines are about this many px tall (0 = off)")
    r.add_argument("--upscale-to", type=int, default=1000, help="fallback when no lines are found")
    r.add_argument("--save-prep", help="save the prepared image (no metadata) to this path")
    text_opts(r)
    r.set_defaults(fn=_read)

    c = sub.add_parser("clean", help="clean OCR text")
    c.add_argument("file", nargs="?")
    text_opts(c)
    c.set_defaults(fn=_clean)

    s = sub.add_parser("strip-metadata", help="re-save an image with pixels only")
    s.add_argument("src")
    s.add_argument("dst")
    s.set_defaults(fn=_strip)

    d = sub.add_parser("doctor", help="check engines and models")
    d.set_defaults(fn=_doctor)

    args = ap.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
