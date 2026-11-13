# Right-to-left output and nikud

## Logical order vs visual order

Hebrew is stored in **logical order**, the order it is typed and read. The screen's bidi algorithm draws it right to left. Every engine in the catalog should return logical order:

- **Tesseract 4+** returns logical order for `heb`.
- **kraken** needs `--reorder` (and a base direction of R). Without it, lines come back in display order.
- **Vision-language models** and some ONNX ports may return visual order, depending on how their training text was stored.

A quick test: final letters (ך ם ן ף ץ) belong at the **end** of a word. If most of them sit at the start of words, the line is reversed. `heb1.text.looks_reversed()` uses this check, and `clean()` re-reverses such lines while keeping digit and Latin runs left to right.

Displaying the text:
- **HTML:** `<p dir="rtl" lang="he">`. Use `dir="auto"` for mixed content.
- **Plain text files and terminals:** start each line with RLM (U+200F), using `--rtl-mark`, so viewers begin the paragraph right to left. Strip RLM and other direction marks again before you compare or search text (`strip_bidi`).
- Never "fix" display by reversing the string. That breaks copy, search and screen readers.

## Geresh, gershayim and maqaf

OCR and keyboards produce ASCII `'` and `"`. In Hebrew these should be ׳ (U+05F3) and ״ (U+05F4): צה״ל, ג׳ירפה, ש׳. `fix_geresh()` converts them only between or after Hebrew letters, so ordinary quotation marks are left alone. The maqaf ־ (U+05BE) is a Hebrew hyphen; keep it.

## Final letters

Tesseract sometimes mixes up כ/ך, מ/ם, נ/ן, פ/ף and צ/ץ, especially on worn print. `fix_final_letters()` uses the final form at the end of a word and the regular form inside it. It skips tokens with ׳ or ״, because abbreviations and sounds like צ׳ follow other rules.

## Nikud and teamim

- Vowel points are U+05B0–U+05BD, U+05BF, U+05C1, U+05C2, U+05C4, U+05C5 and U+05C7. Teamim are U+0591–U+05AF. `strip_nikud()` removes both, and `strip_cantillation()` removes only the teamim.
- **Normalize before comparing.** The same pointed word can be typed with its marks in different orders. Use NFC on both sides, or compare letters only. Some PDFs and OCR engines emit precomposed presentation forms (U+FB1D–U+FB4F, e.g. שׁ as one code point). `normalize()` unfolds those.
- **Short spelling vs full spelling.** Pointed text uses short spelling (סֻכָּר, בֹּקֶר), but unpointed modern text uses full spelling (סוכר, בוקר). Stripping the points from short spelling leaves a different word (סכר, בקר), which hurts both OCR word lists and nikud models. Store both forms if you need to match them.
- **Machine-restored nikud is not checked nikud.** Restoration models score ~93–95% of words right on everyday sentences. They score far lower on headwords alone, because a single word without context (ברח) can be pointed several ways. They are not made for Biblical or liturgical text. Label machine-pointed text as such.

## The divine Name

Write the four-letter Name as **ה׳** in anything you display, whether bare or pointed, and also after prefix letters (לה׳). `show_name()` does this. Keep the Name out of automatic correction, and out of any text-to-speech or phoneme step.
