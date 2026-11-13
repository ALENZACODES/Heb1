import glob
import os
import shutil

import pytest

FONT_GLOBS = [
    "/usr/share/fonts/truetype/culmus/FreeSans*.ttf", "/usr/share/fonts/truetype/culmus/*.ttf",
    "/usr/share/fonts/opentype/culmus/*.otf",
    "/usr/share/fonts/truetype/noto/NotoSansHebrew-Regular.ttf", "/usr/share/fonts/**/NotoSansHebrew*.ttf",
    "/usr/share/fonts/**/FrankRuhlLibre*.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial Unicode.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf", "C:/Windows/Fonts/arial.ttf",
]


def hebrew_font():
    env = os.environ.get("HEB1_TEST_FONT")
    if env and os.path.exists(env):
        return env
    for g in FONT_GLOBS:
        for p in sorted(glob.glob(g, recursive=True)):
            if "Italic" not in p and "Mono" not in p:
                return p
    return None


@pytest.fixture
def font_path():
    p = hebrew_font()
    if not p:
        pytest.skip("no Hebrew font found (set HEB1_TEST_FONT)")
    return p


needs_tesseract = pytest.mark.skipif(shutil.which("tesseract") is None, reason="tesseract not installed")
