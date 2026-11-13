"""Run an OCR engine on an image and return words with confidences.

Engines:
  tesseract  - the Tesseract CLI (must be on PATH). Models:
               "heb"          the stock model installed with Tesseract (or tessdata_fast, vendored)
               "heocr-r8b"    HeOCR R8b, a printed-Hebrew fine-tune of tessdata_best heb (vendored, Apache-2.0)
               any other name is passed to -l as is (use --tessdata-dir for your own .traineddata)
"""
from __future__ import annotations

import csv
import io
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
VENDOR = Path(os.environ.get("HEB1_VENDOR", ROOT / "vendor"))

# model alias -> (tesseract language name, folder inside vendor/ holding its .traineddata)
MODELS = {
    "heb": ("heb", None),
    "heb-fast": ("heb", "tessdata-fast-heb"),
    "heocr-r8b": ("heocr_r8b", "heocr-r8b"),
}


class OCRError(RuntimeError):
    pass


@dataclass
class Word:
    text: str
    conf: float              # 0-100, -1 when the engine gives none
    line: tuple              # (block, paragraph, line) key from Tesseract
    box: tuple = (0, 0, 0, 0)


@dataclass
class Result:
    words: list = field(default_factory=list)
    engine: str = "tesseract"
    model: str = "heb"

    def lines(self) -> list[list[Word]]:
        out, cur, key = [], [], None
        for w in self.words:
            if key is not None and w.line != key:
                out.append(cur)
                cur = []
            cur.append(w)
            key = w.line
        if cur:
            out.append(cur)
        return out

    def text(self) -> str:
        return "\n".join(" ".join(w.text for w in ln) for ln in self.lines())


def tesseract_available() -> bool:
    return shutil.which(os.environ.get("TESSERACT", "tesseract")) is not None


def resolve_model(model: str, tessdata_dir: str | None = None) -> tuple[str, str | None]:
    """Return (language name for -l, tessdata dir or None)."""
    if model in MODELS:
        lang, folder = MODELS[model]
        if folder:
            d = VENDOR / folder
            if not (d / f"{lang}.traineddata").exists():
                raise OCRError(f"model {model!r} not found in {d}; run: python fetch/fetch.py {model}")
            return lang, str(d)
        return lang, tessdata_dir
    return model, tessdata_dir


def parse_tsv(tsv: str) -> list[Word]:
    """Parse `tesseract ... tsv` output into words (level 5 rows with text)."""
    words = []
    reader = csv.DictReader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE)
    for row in reader:
        if row.get("level") != "5":
            continue
        txt = (row.get("text") or "").strip()
        if not txt:
            continue
        try:
            conf = float(row.get("conf", "-1"))
        except ValueError:
            conf = -1.0
        key = (int(row["page_num"]), int(row["block_num"]), int(row["par_num"]), int(row["line_num"]))
        box = tuple(int(row[k]) for k in ("left", "top", "width", "height"))
        words.append(Word(txt, conf, key, box))
    return words


def run_tesseract(img: Image.Image, model: str = "heb", psm: int = 6,
                  tessdata_dir: str | None = None, timeout: int = 120) -> Result:
    if not tesseract_available():
        raise OCRError("tesseract is not installed (Debian/Ubuntu: apt install tesseract-ocr tesseract-ocr-heb)")
    lang, tdir = resolve_model(model, tessdata_dir)
    exe = os.environ.get("TESSERACT", "tesseract")
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "in.png")
        img.save(path)
        cmd = [exe, path, "stdout", "-l", lang, "--psm", str(psm), "--oem", "1"]
        if tdir:
            cmd += ["--tessdata-dir", tdir]
        # tsv via a variable, not the "tsv" config file: a custom --tessdata-dir has no configs/ folder
        cmd += ["-c", "tessedit_create_tsv=1"]
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    if p.returncode != 0:
        raise OCRError(p.stderr.strip() or f"tesseract exited with {p.returncode}")
    return Result(parse_tsv(p.stdout), "tesseract", model)
