"""Image preparation before OCR (Pillow only).

What helps Hebrew OCR most, in order: enough resolution (letter height of
roughly 25-40 px), dark text on a light background, a clean black/white image,
a level line, and a white margin around the text.
"""
from __future__ import annotations

from dataclasses import dataclass

from PIL import Image, ImageFilter, ImageOps


@dataclass
class Prep:
    line_height: int = 48       # rescale so a text line is about this tall (0 = off)
    upscale_to: int = 1000      # fallback when no lines are found: longer side at least this
    max_side: int = 5000
    binarize: bool = True
    denoise: bool = True
    deskew: bool = False
    border: int = 20


def otsu_threshold(gray: Image.Image) -> int:
    """Otsu's threshold from the 256-bin histogram of a greyscale image."""
    hist = gray.histogram()[:256]
    total = sum(hist)
    sum_all = sum(i * h for i, h in enumerate(hist))
    w_b = sum_b = 0
    best_t, best_var = 127, -1.0
    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += t * hist[t]
        m_b = sum_b / w_b
        m_f = (sum_all - sum_b) / w_f
        var = w_b * w_f * (m_b - m_f) ** 2
        if var > best_var:
            best_var, best_t = var, t
    return best_t


def mean_level(gray: Image.Image) -> float:
    hist = gray.histogram()[:256]
    n = sum(hist) or 1
    return sum(i * h for i, h in enumerate(hist)) / n


def _row_profile_score(bw: Image.Image) -> float:
    """Variance of dark pixels per row: highest when text lines are level."""
    w, h = bw.size
    data = bw.tobytes()
    # bw is mode "L" 0/255: count dark pixels (value 0) in each row
    rows = [data[y * w:(y + 1) * w].count(0) for y in range(h)]
    m = sum(rows) / (h or 1)
    return sum((r - m) ** 2 for r in rows) / (h or 1)


def estimate_skew(bw: Image.Image, max_angle: float = 5.0, step: float = 0.5) -> float:
    """Small-angle deskew by projection profile on a reduced copy."""
    small = bw.copy()
    small.thumbnail((600, 600))
    best_a, best_s = 0.0, -1.0
    a = -max_angle
    while a <= max_angle + 1e-9:
        rot = small.rotate(a, expand=True, fillcolor=255, resample=Image.NEAREST)
        s = _row_profile_score(rot)
        if s > best_s:
            best_a, best_s = a, s
        a += step
    return best_a


def estimate_line_height(gray: Image.Image) -> int:
    """Median height of the dark row-bands (text lines) in px, or 0 if none are found."""
    small = gray.copy()
    f = 1.0
    if small.width > 1200:
        f = 1200 / small.width
        small = small.resize((1200, max(1, round(small.height * f))))
    t = otsu_threshold(small)
    bw = small.point(lambda v: 0 if v <= t else 255, mode="L")
    w, h = bw.size
    data = bw.tobytes()
    ink = [data[y * w:(y + 1) * w].count(0) > max(2, w // 200) for y in range(h)]
    runs, n = [], 0
    for on in ink + [False]:
        if on:
            n += 1
        elif n:
            if n >= 3:
                runs.append(n)
            n = 0
    if not runs:
        return 0
    runs.sort()
    return round(runs[len(runs) // 2] / f)


def prepare(img: Image.Image, opts: Prep | None = None) -> Image.Image:
    """Return a clean greyscale/binary image ready for OCR. No metadata is kept."""
    o = opts or Prep()
    img = ImageOps.exif_transpose(img)            # honour camera rotation, then drop EXIF
    if img.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", img.size, "white")
        rgba = img.convert("RGBA")
        bg.paste(rgba, mask=rgba.split()[-1])
        img = bg
    gray = ImageOps.autocontrast(img.convert("L"), cutoff=1)
    if mean_level(gray) < 110:                    # light text on a dark sign
        gray = ImageOps.invert(gray)
    lh = estimate_line_height(gray) if o.line_height else 0
    f = 1.0
    if lh:
        f = max(0.4, min(4.0, o.line_height / lh))
        if abs(f - 1) <= 0.15:
            f = 1.0
    elif max(gray.size) < o.upscale_to:
        f = o.upscale_to / max(gray.size)
    f = min(f, o.max_side / max(gray.size))
    if f != 1.0:
        gray = gray.resize((max(1, round(gray.width * f)), max(1, round(gray.height * f))), Image.LANCZOS)
    if o.denoise:
        gray = gray.filter(ImageFilter.MedianFilter(3))
    out = gray
    if o.binarize:
        t = otsu_threshold(gray)
        out = gray.point(lambda v: 255 if v > t else 0, mode="L")
    if o.deskew:
        a = estimate_skew(out if o.binarize else gray.point(lambda v: 255 if v > 128 else 0))
        if abs(a) >= 0.5:
            out = out.rotate(a, expand=True, fillcolor=255, resample=Image.BICUBIC)
    if o.border:
        out = ImageOps.expand(out, border=o.border, fill=255)
    clean = Image.new(out.mode, out.size)
    clean.paste(out)
    return clean


def strip_metadata(src: str, dst: str) -> None:
    """Re-save an image with pixels only (no EXIF, XMP, ICC or text chunks)."""
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        clean = Image.new(im.mode, im.size)
        clean.paste(im)
        clean.save(dst)
