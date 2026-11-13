import json
import subprocess
import sys

import pytest

from heb1.ocr import parse_tsv, run_tesseract
from heb1.text import clean
from tests.conftest import needs_tesseract
from tests.helpers import char_accuracy, render

TSV = (
    "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
    "1\t1\t0\t0\t0\t0\t0\t0\t500\t200\t-1\t\n"
    "5\t1\t1\t1\t1\t1\t300\t10\t80\t30\t96.1\tשלום\n"
    "5\t1\t1\t1\t1\t2\t200\t10\t80\t30\t71.5\tעולמ\n"
    "5\t1\t1\t1\t2\t1\t300\t60\t80\t30\t90.0\tבוקר\n"
)


def test_parse_tsv_groups_lines():
    words = parse_tsv(TSV)
    assert [w.text for w in words] == ["שלום", "עולמ", "בוקר"]
    assert words[1].conf == 71.5
    from heb1.ocr import Result
    r = Result(words)
    assert r.text() == "שלום עולמ\nבוקר"
    assert clean(r.text()) == "שלום עולם\nבוקר"


LINES = ["שלום עולם", "בוקר טוב לכולם", "ספר תורה וסידור תפילה בבית הכנסת"]
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


@needs_tesseract
@pytest.mark.parametrize("model", ["heb", "heb-fast", "heocr-r8b"])
def test_ocr_reads_rendered_hebrew(font_path, model):
    img = render(LINES, font_path, size=56)
    from heb1.preprocess import prepare
    res = run_tesseract(prepare(img), model=model)
    got = clean(res.text())
    acc = char_accuracy(got, "\n".join(LINES))
    print(model, repr(got), acc)
    assert acc >= 0.9, got


@needs_tesseract
@pytest.mark.skipif(not __import__("os").path.exists(SANS), reason="DejaVu Sans not installed")
def test_stock_model_reads_sans_sign_text():
    from heb1.preprocess import prepare
    img = render(["יציאה", "כניסה לחניון"], SANS, size=30, fg=255, bg=40)   # light text on a dark sign
    got = clean(run_tesseract(prepare(img), model="heb").text())
    assert char_accuracy(got, "יציאה\nכניסה לחניון") >= 0.85, got


@needs_tesseract
def test_cli_end_to_end(font_path, tmp_path):
    p = tmp_path / "page.png"
    render(LINES, font_path, size=56).save(p)
    out = subprocess.run([sys.executable, "-m", "heb1", "read", str(p), "--format", "json"],
                         capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr
    data = json.loads(out.stdout)
    assert char_accuracy(data["text"], "\n".join(LINES)) >= 0.9
    assert data["mean_conf"] is not None


def test_cli_clean_stdin():
    out = subprocess.run([sys.executable, "-m", "heb1", "clean", "--nikud", "strip"], input="שָׁלוֹמ עוֹלָמ\n",
                         capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "שלום עולם"
