# Lessons from building ALEF's Hebrew camera, handwriting and nikud tools

ALEF is a Hebrew-learning web app that runs fully offline in the browser. Its camera translator, letter-tracing checker and vowel-mark packs live in [alef-tools](https://github.com/ALENZACODES/alef-tools), which is MIT-licensed by the same author. These are the generic lessons. App data is not included.

## Camera OCR (Tesseract `heb` in WebAssembly)

- **Measure on your own images before tuning.** These numbers come from a bench of 145 synthetic images, with printed text degraded in software, read by Tesseract 5.3 `heb` at page mode 6:
  - 79.7% word recall on sign-style images;
  - ~65% on pointed prayer lines and pages.

  The same model compiled for the browser scored 88.3% on the signs, so measure in the runtime you ship.
- **Most sign errors are**:
  - look-alike swaps (ב/כ, ד/ר, ה/ח, ו/ז/י/ן, ס/ם);
  - a narrow letter (י ו ן) dropped or added;
  - a missed space between two words;
  - a stray mark glued to a word.
- **Correct conservatively.** A word missing from your list is usually a real word the list lacks, not a misreading. ALEF's rules (ported here as `heb1.correct`):
  - leave words with confidence 88 or more alone;
  - allow one look-alike swap at 70–88;
  - allow a little more below 70;
  - change a word only when exactly one listed word is close;
  - never touch short words, numbers, Latin, abbreviations, names or the Name.

  This lifted sign accuracy by ~4 points (79.7% → 83.6%) with no image made worse. With the test phrases removed from the word list, it lost about 1 point. Word-list overlap with your test set inflates results.
- **Never "correct" pointed text.** For prayers and pesukim, match the OCR'd letters to a stored edition instead.
- **Show the Name as ה׳,** including when it is misread one letter off, and never replace it with another word.

## Handwritten letter checking

- Train a tiny CNN (27 classes: 22 letters + 5 finals, plus "not a letter"; ≤ 2 MiB ONNX) rather than shipping a large TrOCR. Use letters rendered from OFL Hebrew fonts (print and script styles) with stroke and pen augmentation, plus HHD_v0 (CC-BY-4.0) for real hands.
- Keep some fonts as **held-out fonts** that are never trained on, and use HHD's TEST split as the real-handwriting score. Report look-alike pairs separately.
- Leave out fonts whose licence file cannot be fetched, and decorative or historical cursives (Solitreo) that learners are not taught.
- Combine the classifier with simple stroke-order and shape checks, and give one kind tip at a time.
- Unlicensed "testing" Hebrew TrOCR checkpoints are for benchmarking only, never for shipping.

## Nikud restoration packs

- **Size and speed:**
  - DictaBERT-large char menaked (CC-BY-4.0) quantized to 8-bit is ~303 MiB and agrees with the full model on 98.5% of words;
  - 4-bit is ~194 MiB (98.0%) but was ~3× slower in WebAssembly;
  - on a 2-core machine, 8-bit ran at ~0.5 s per sentence.
- **Keep the letters.** The model's default output can drop vowel letters, giving short spelling. Keep the input letters and add the matching points instead.
- **Leave alone:** already-pointed words, text with teamim, and anything containing the Name.
- **Rule-based shva rules need review.** Shva na vs shva nach and kamatz katan (חָכְמָה, תָּכְנִית) are where hand-written rules and models disagree most, and the right answer depends on reading tradition.
- Machine-pointed lines nobody has read should be shown with a "not checked" note.

## General

- Record the licence and revision of every model you ship, and drop anything non-commercial or unlicensed from the shipped app.
- Download big weights on demand, in parts with checksums, and only when the user asks. Never ship them in the first install.
- Strip metadata from every image you publish.
