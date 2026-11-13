from PIL import Image, ImageDraw, ImageFont


def render(lines, font_path, size=48, fg=0, bg=255, pad=40):
    """Render Hebrew lines right-aligned. Pillow lays out RTL itself when libraqm is
    present; otherwise we reverse the string for display (pure-letter lines only)."""
    font = ImageFont.truetype(font_path, size)
    try:
        from PIL import features
        raqm = features.check("raqm")
    except Exception:
        raqm = False
    w = int(size * 0.75 * max(len(l) for l in lines)) + 2 * pad
    h = int(size * 1.6 * len(lines)) + 2 * pad
    img = Image.new("L", (w, h), bg)
    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        y = pad + int(i * size * 1.6)
        if raqm:
            d.text((w - pad, y), line, font=font, fill=fg, anchor="ra", direction="rtl")
        else:
            d.text((w - pad, y), line[::-1], font=font, fill=fg, anchor="ra")
    return img


def char_accuracy(got: str, want: str) -> float:
    """1 - normalized Levenshtein distance on letters (spaces ignored)."""
    a, b = got.replace(" ", "").replace("\n", ""), want.replace(" ", "").replace("\n", "")
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return 1 - prev[-1] / max(len(b), 1)
