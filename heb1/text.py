"""Hebrew text clean-up after OCR. Pure Python, no dependencies.

Everything here works on logical-order Unicode text (the order you type and
store Hebrew in), not on the visual order a screen draws it in.
"""
from __future__ import annotations

import re
import unicodedata

# ---- character classes -------------------------------------------------------
LETTERS = "".join(chr(c) for c in range(0x05D0, 0x05EB))          # א..ת incl. finals
CANTILLATION = "".join(chr(c) for c in range(0x0591, 0x05B0))     # teamim U+0591..U+05AF
VOWELS = "".join(chr(c) for c in list(range(0x05B0, 0x05BE)) + [0x05BF, 0x05C1, 0x05C2, 0x05C4, 0x05C5, 0x05C7])
MAQAF = "\u05BE"
PASEQ = "\u05C0"
SOF_PASUQ = "\u05C3"
GERESH = "\u05F3"
GERSHAYIM = "\u05F4"
BIDI_CONTROLS = "\u200E\u200F\u202A\u202B\u202C\u202D\u202E\u2066\u2067\u2068\u2069\u061C"
RLM = "\u200F"

FINAL_OF = {"כ": "ך", "מ": "ם", "נ": "ן", "פ": "ף", "צ": "ץ"}
REGULAR_OF = {v: k for k, v in FINAL_OF.items()}

_HEB = re.compile(f"[{LETTERS}]")
_MARKS = re.compile(f"[{CANTILLATION}{VOWELS}]")
_TEAMIM = re.compile(f"[{CANTILLATION}]")
_VOWELS = re.compile(f"[{VOWELS}]")

# The four-letter divine Name, built from code points so it is never written out.
NAME_LETTERS = "\u05D9\u05D4\u05D5\u05D4"
NAME_SHOWN = "\u05D4\u05F3"      # ה׳
_NAME_PREFIXES = "ובלמכשה"


def is_hebrew_letter(ch: str) -> bool:
    return bool(_HEB.fullmatch(ch))


def has_hebrew(s: str) -> bool:
    return bool(_HEB.search(s))


def has_marks(s: str) -> bool:
    """True when the text carries vowel points or cantillation."""
    return bool(_MARKS.search(s))


def strip_bidi(s: str) -> str:
    """Remove invisible direction marks (LRM, RLM, embeddings, isolates)."""
    return s.translate({ord(c): None for c in BIDI_CONTROLS})


def strip_cantillation(s: str) -> str:
    """Remove teamim (Torah reading marks) and keep the vowel points."""
    return _TEAMIM.sub("", s)


def strip_nikud(s: str, keep_maqaf: bool = True) -> str:
    """Remove vowel points and cantillation. Letters, maqaf and punctuation stay."""
    out = _MARKS.sub("", s)
    if not keep_maqaf:
        out = out.replace(MAQAF, "-")
    return out


def letters_only(s: str) -> str:
    return "".join(ch for ch in strip_nikud(s) if is_hebrew_letter(ch))


def normalize(s: str) -> str:
    """Unicode NFC, with Hebrew presentation forms (U+FB1D..U+FB4F) unfolded.

    NFC alone keeps pointed text stable for comparison; NFKD is only used to
    unfold the presentation forms some PDFs and OCR engines emit (e.g. U+FB2A).
    """
    out = []
    for ch in s:
        if 0xFB1D <= ord(ch) <= 0xFB4F:
            out.append(unicodedata.normalize("NFKD", ch))
        else:
            out.append(ch)
    return unicodedata.normalize("NFC", "".join(out))


def fix_geresh(s: str) -> str:
    """ASCII quotes used as Hebrew marks become the real ones.

    צה"ל -> צה״ל (gershayim between letters); ג'ירפה / ש' -> geresh after a letter.
    """
    s = re.sub(rf'(?<=[{LETTERS}])["\u201C\u201D\u05F2](?=[{LETTERS}])', GERSHAYIM, s)
    s = re.sub(rf"(?<=[{LETTERS}])['\u2018\u2019]", GERESH, s)
    return s


_TOKEN = re.compile(rf"[{LETTERS}{CANTILLATION}{VOWELS}{GERESH}{GERSHAYIM}]+")


def fix_final_letters(s: str) -> str:
    """Use the final form at the end of a word and the regular form inside it.

    OCR engines often confuse כ/ך, מ/ם, נ/ן, פ/ף, צ/ץ. A token with geresh or
    gershayim (an abbreviation or a foreign sound like צ׳) is left alone.
    """
    def fix(m: re.Match) -> str:
        tok = m.group(0)
        if GERESH in tok or GERSHAYIM in tok:
            return tok
        chars = list(tok)
        idx = [i for i, c in enumerate(chars) if is_hebrew_letter(c)]
        if len(idx) < 2:
            return tok
        for i in idx[:-1]:
            if chars[i] in REGULAR_OF:
                chars[i] = REGULAR_OF[chars[i]]
        last = idx[-1]
        if chars[last] in FINAL_OF:
            chars[last] = FINAL_OF[chars[last]]
        return "".join(chars)

    return _TOKEN.sub(fix, s)


def show_name(s: str) -> str:
    """Write the four-letter divine Name as ה׳ (bare or pointed, after prefix letters too)."""
    out, i = [], 0
    toks = re.split(rf"([{LETTERS}{CANTILLATION}{VOWELS}]+)", s)
    for tok in toks:
        if tok and has_hebrew(tok):
            bare = letters_only(tok)
            for k in range(0, min(3, len(bare)) + 1):
                pre, rest = bare[:k], bare[k:]
                if rest == NAME_LETTERS and all(c in _NAME_PREFIXES for c in pre):
                    tok = pre + NAME_SHOWN
                    break
        out.append(tok)
    return "".join(out)


def has_name(s: str) -> bool:
    return show_name(s) != s


# ---- reading order -----------------------------------------------------------

def looks_reversed(line: str) -> bool:
    """Guess whether a Hebrew line came back in visual (reversed) order.

    In logical order final letters (ך ם ן ף ץ) sit at the END of words. If most
    of them sit at the START of words instead, the line was reversed.
    """
    words = [letters_only(w) for w in line.split()]
    words = [w for w in words if len(w) >= 2]
    at_end = sum(1 for w in words if w[-1] in REGULAR_OF)
    at_start = sum(1 for w in words if w[0] in REGULAR_OF)
    return at_start >= 2 and at_start > at_end * 2


def to_logical(line: str) -> str:
    """Reverse a visual-order Hebrew line (characters and word order), keeping
    runs of digits/Latin in their own left-to-right order."""
    rev = line[::-1]
    return re.sub(r"[0-9A-Za-z][0-9A-Za-z.,:/%-]*", lambda m: m.group(0)[::-1], rev)


def for_display(text: str, mark: bool = True) -> str:
    """Prefix each Hebrew line with RLM so plain-text viewers start it right-to-left."""
    if not mark:
        return text
    return "\n".join((RLM + ln) if has_hebrew(ln) else ln for ln in text.split("\n"))


def clean(text: str, *, finals: bool = True, geresh: bool = True, nikud: str = "keep",
          name: bool = True, fix_order: bool = True) -> str:
    """The standard post-OCR clean-up chain.

    nikud: "keep" | "strip" (remove vowels and teamim) | "teamim" (remove teamim only)
    """
    lines = []
    for ln in strip_bidi(normalize(text)).split("\n"):
        ln = re.sub(r"[ \t\u00A0]+", " ", ln).strip()
        if fix_order and looks_reversed(ln):
            ln = to_logical(ln)
        if geresh:
            ln = fix_geresh(ln)
        if nikud == "strip":
            ln = strip_nikud(ln)
        elif nikud == "teamim":
            ln = strip_cantillation(ln)
        if finals:
            ln = fix_final_letters(ln)
        if name:
            ln = show_name(ln)
        lines.append(ln)
    # drop runs of blank lines
    out = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip("\n")
    return out
