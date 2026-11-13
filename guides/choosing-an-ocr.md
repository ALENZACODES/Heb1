# Choosing a Hebrew OCR

No single open model reads everything well. Decide by what is on the page.

## 1. Modern printed Hebrew (books, newspapers, letters, forms)

- **Tesseract + HeOCR R8b** (`heb1 read --model heocr-r8b --psm 3`) for scanned serif book print. R8b is a fine-tune of Tesseract's `tessdata_best` Hebrew model, trained on real scanned lines from public-domain books and government booklets. Its card reports a character error rate under 1% on held-out books, which is optimistic because those books also picked the checkpoint. It adds ׳ ״ —. It has **no Latin letters and no nikud**.
- **Stock `heb`** (tessdata or tessdata_best) when a page mixes Hebrew with Latin words or digits in running text, and for sans-serif type.
- Our own quick check (clean renders, not scans, 2026-11-12) found two things:
  - Stock `heb` read sans-serif sign text (DejaVu Sans, IBM Plex Sans Hebrew) correctly, but R8b misread it badly.
  - On serif book type (Frank Ruhl Libre), both read almost perfectly, but R8b sometimes dropped a word-final letter at the end of a line (לכולם → לכול).

  So try both on a few of your own pages and keep the better one.
- For PDFs, **OCRmyPDF** (`ocrmypdf -l heb in.pdf out.pdf`) keeps the page images and adds a searchable text layer.
- Page mode: `--psm 3` for whole pages with columns, `--psm 6` for a single block, and `--psm 7` for one line.

## 2. Signs, menus, labels and phone photos

- Crop to the text, then use `heb1 read` (psm 6). Preparation matters more than the model: see [preprocessing.md](preprocessing.md).
- Add `--lexicon` with a word list for your domain (menu words, street names). The corrector is confidence-gated, so it stays out of the way when Tesseract is sure.
- In the browser, **tesseract.js** runs the same `heb` model offline as WebAssembly.

## 3. Pointed text: siddur, chumash, children's books

- Tesseract's models were trained mostly on unpointed text. Vowel points become noise, broken letters or stray marks. Use `--nikud strip`, or better, **do not trust OCR'd points at all**:
  - for a known text (a prayer or a pasuk), OCR the letters, then *match* them against a stored edition such as the Sefaria export and show that edition's pointing;
  - for new text, OCR the letters, then restore nikud with a model (DictaBERT-large char menaked, Nakdimon, UNIKUD, Phonikud), and label the result as machine-pointed.
- Teamim (cantillation) are the hardest. No open OCR in the catalog reads them reliably.

## 4. Manuscripts and scribal hands

- Use **kraken** with the **BiblIA** models (general, Ashkenazi, Italian, Sephardi bookhand; CC-BY-SA-4.0) inside **eScriptorium**. Segment with baselines, recognise, then correct a few pages and fine-tune. The BiblIA paper reports more than 97% character accuracy on its validation set.
- **Sofer Mahir** has segmentation models for big rabbinic manuscripts, but only for non-commercial use.
- Torah scrolls (STaM): no open model trained specifically on STaM was found. BiblIA's square-script models are the closest starting point. Expect to fine-tune.
- Add `--reorder` (and a base direction of R) to kraken so the output is in logical order.

## 5. Modern handwriting

- **Lines:** the on-device TrOCR-CTC models (cyttic/hebrew-ocr-android, MIT) are the most practical open option found. HeOCR R3h is a kraken baseline trained only on synthetic pages.
- **Single letters** (tracing and teaching apps): train a small classifier on **HHD_v0** (CC-BY-4.0, ~5,000 letters from forms) plus letters rendered from OFL Hebrew fonts with pen-style augmentation. Score it on HHD's own TEST split and report look-alike pairs (ב/כ, ד/ר, ה/ח, ו/ז/ן, ס/ם) separately.
- **Benchmark** on the ivrit.ai handwriting benchmark (gated, accept its terms) rather than on your training fonts.

## 6. After OCR

- **Clean-up:** `heb1 clean` (finals, geresh, direction marks, the Name as ה׳).
- **Word fixes:** `--lexicon`. For a stronger, slower option, rank candidates with a masked language model: DictaBERT for modern text, BEREL for rabbinic text, MsBERT for manuscripts.
- **Names:** tag them with DictaBERT-NER first, and never auto-correct a tagged name.
- **Morphology:** DictaBERT-joint, YAP or Hspell (AGPL).
