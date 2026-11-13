import io

from PIL import Image

from heb1.preprocess import Prep, mean_level, otsu_threshold, prepare, strip_metadata


def test_otsu_splits_two_levels():
    img = Image.new("L", (100, 100), 200)
    img.paste(40, (0, 0, 50, 100))
    t = otsu_threshold(img)
    assert 40 <= t < 200


def test_prepare_inverts_dark_background_and_binarizes():
    img = Image.new("RGB", (300, 100), (10, 30, 120))       # blue sign
    img.paste((255, 255, 255), (100, 40, 200, 60))         # white text bar
    out = prepare(img, Prep(border=10))
    assert out.mode == "L"
    hist = out.histogram()
    assert sum(hist[1:255]) == 0                          # only black and white
    assert mean_level(out) > 128                           # light background after inversion
    assert max(out.size) > 300                             # thin 20 px line scaled up toward 48 px


def test_line_height_estimate(font_path):
    from heb1.preprocess import estimate_line_height
    from tests.helpers import render
    small = render(["שלום עולם", "בוקר טוב"], font_path, size=20)
    big = render(["שלום עולם", "בוקר טוב"], font_path, size=80)
    assert 10 <= estimate_line_height(small) <= 40
    assert 50 <= estimate_line_height(big) <= 140
    out = prepare(big)
    assert 30 <= estimate_line_height(out) <= 70


def test_prepare_drops_metadata(tmp_path):
    img = Image.new("RGB", (50, 50), "white")
    exif = Image.Exif()
    exif[0x010F] = "SomeCamera"                            # Make
    exif[0x0112] = 6                                       # rotate 90
    src = tmp_path / "in.jpg"
    img.save(src, exif=exif.tobytes())
    with Image.open(src) as im:
        assert im.getexif().get(0x010F) == "SomeCamera"
        out = prepare(im, Prep(line_height=0, upscale_to=50, border=0, binarize=False, denoise=False))
    assert not out.info.get("exif") and len(out.getexif()) == 0
    dst = tmp_path / "out.png"
    strip_metadata(str(src), str(dst))
    with Image.open(dst) as im2:
        assert len(im2.getexif()) == 0 and "exif" not in im2.info


def test_deskew_runs(font_path):
    from tests.helpers import render
    img = render(["שלום עולם", "בוקר טוב"], font_path).rotate(3, expand=True, fillcolor=255)
    out = prepare(img, Prep(deskew=True))
    assert out.size[0] > 0
