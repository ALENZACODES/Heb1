"""Confidence-gated word correction against a word list.

Lessons from building a camera translator: a word missing from the list is far
more often a real word the list does not hold than a misreading, so the default
is to change nothing. A word is only replaced when the engine was unsure AND
exactly one listed word is close by the engine's typical mistakes.
"""
from __future__ import annotations

from dataclasses import dataclass

from .text import NAME_LETTERS, has_marks, is_hebrew_letter, letters_only

# letters Tesseract confuses on Hebrew print and signs
LOOK_ALIKE = ("בכ", "דרך", "החת", "וזין", "סםט", "גנ", "עצ", "מט", "כפ", "ךן", "ףק")
NARROW = "יון"
PREFIXES = "הובלמשכ"
PUNCT = ".,:;!?()[]\"'\u201C\u201D"
_PAIRS = {a + b for g in LOOK_ALIKE for a in g for b in g if a != b}
COST_LOOK, COST_NARROW, COST_OTHER = 0.4, 0.6, 1.0


def looks_alike(a: str, b: str) -> bool:
    return a + b in _PAIRS


def distance(a: str, b: str, limit: float = float("inf")) -> float:
    """Weighted edit distance: look-alike swap 0.4, narrow letter in/out 0.6, else 1."""
    n, m = len(a), len(b)
    prev = [0.0] * (m + 1)
    for j in range(1, m + 1):
        prev[j] = prev[j - 1] + (COST_NARROW if b[j - 1] in NARROW else COST_OTHER)
    for i in range(1, n + 1):
        ca = a[i - 1]
        dele = COST_NARROW if ca in NARROW else COST_OTHER
        cur = [prev[0] + dele] + [0.0] * m
        for j in range(1, m + 1):
            cb = b[j - 1]
            sub = 0.0 if ca == cb else COST_LOOK if looks_alike(ca, cb) else COST_OTHER
            ins = COST_NARROW if cb in NARROW else COST_OTHER
            cur[j] = min(prev[j - 1] + sub, prev[j] + dele, cur[j - 1] + ins)
        if min(cur) > limit:
            return float("inf")
        prev = cur
    return prev[m]


def budget(length: int) -> float:
    """Short words are barely touched: too many real words sit one letter apart."""
    return 0.0 if length <= 1 else 0.4 if length == 2 else 0.8 if length == 3 else 1.0 if length == 4 else 1.4


@dataclass
class Corrector:
    words: list
    keep_conf: float = 88.0      # at or above: never change
    low_conf: float = 70.0       # below: allow a bit more
    margin: float = 0.3          # best must beat runner-up by this much

    def __post_init__(self):
        self.rank = {}
        for i, w in enumerate(self.words):
            w = letters_only(w)
            if w and w not in self.rank:
                self.rank[w] = i
        self.by_len = {}
        for w in self.rank:
            self.by_len.setdefault(len(w), []).append(w)

    @classmethod
    def from_file(cls, path: str, **kw) -> "Corrector":
        with open(path, encoding="utf-8") as f:
            return cls([ln.strip() for ln in f if ln.strip() and not ln.startswith("#")], **kw)

    def known(self, w: str) -> bool:
        if w in self.rank:
            return True
        for k in range(1, min(3, len(w) - 2) + 1):
            if all(c in PREFIXES for c in w[:k]) and w[k:] in self.rank:
                return True
        return False

    def suggest(self, token: str, conf: float = -1) -> str:
        """Return the corrected token, or the token unchanged."""
        if conf < 0 or conf >= self.keep_conf:
            return token
        if has_marks(token):                       # pointed prayer/Torah text: match stored texts instead
            return token
        lead = token[: len(token) - len(token.lstrip(PUNCT))]
        tail = token[len(token.rstrip(PUNCT)):]
        core = token[len(lead): len(token) - len(tail)]
        if not core or not all(is_hebrew_letter(c) for c in core):
            return token                           # numbers, Latin, abbreviations (צה״ל), mixed tokens
        w = core
        if NAME_LETTERS in w or self.known(w):
            return token
        lim = budget(len(w)) * (1.0 if conf < self.low_conf else 0.5)
        if lim <= 0:
            return token
        cands = []
        for L in range(len(w) - 2, len(w) + 3):
            for c in self.by_len.get(L, ()):
                d = distance(w, c, lim)
                if d <= lim:
                    cands.append((d, self.rank[c], c))
        if not cands:
            return token
        cands.sort()
        if len(cands) > 1 and cands[1][0] - cands[0][0] < self.margin:
            return token                           # two equally close words: leave it
        return lead + cands[0][2] + tail

    def fix_words(self, words) -> list:
        """words: iterable of ocr.Word; returns new texts in order."""
        return [self.suggest(w.text, w.conf) for w in words]
