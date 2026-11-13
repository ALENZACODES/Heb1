# Preparing images for Hebrew OCR

`heb1.preprocess.prepare()` does all of this by default. You can also do it yourself.

1. **Rotate by EXIF, then drop the metadata.** Phone photos are often stored sideways with a rotation tag. Apply it, then save pixels only, so location and device data never travel with the image (`heb1 strip-metadata`).
2. **Resolution: scale by line height, not by image size.** Tesseract reads best when letters are about 25–40 px tall, which is roughly 300 dpi for book print. `prepare()` measures the text lines and rescales so each line band is about 48 px (`--line-height`). Blowing a short sign crop up to a fixed width made letters 150+ px tall, and the fine-tuned model then dropped letters. Shrink anything over ~5,000 px.
3. **Dark text on a light background.** Signs are often white on blue or green. Invert when the mean level is dark. Tesseract 4+ copes with some inverted text, but not reliably.
4. **Contrast and noise.** Autocontrast with a 1% cutoff, then a 3×3 median filter, removes JPEG speckle without eating the thin strokes of ו, י and ן.
5. **Binarize.** A global Otsu threshold suits scans. For uneven light on photos, crop tighter or use an adaptive threshold (OpenCV `adaptiveThreshold`, or kraken's `binarize`). Skip binarization (`--no-binarize`) for very small or faint print, where it can break letters apart.
6. **Deskew.** A tilt of even 2–3° hurts line finding. `--deskew` tries small angles and keeps the one with the sharpest row profile.
7. **White margin.** Leave about 20 px of white around the text. Text touching the image edge is often dropped.
8. **Page mode.** Choose `--psm` for the layout (3 page, 6 block, 7 line, 11 sparse text for scattered signs).

Nikud-specific: with pointed text, do **not** use aggressive morphology such as erosion or opening. It deletes dots (chirik, dagesh, shin dot) and merges the kamatz with the letter beneath. Prefer `--no-binarize` and strip the marks afterwards.
