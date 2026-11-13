# Heb1: free Hebrew OCR in one place

Heb1 collects the free and open tools, models and datasets for reading Hebrew from images: printed text, handwriting, and Torah, siddur and manuscript pages. It also includes the Hebrew text tools you need after OCR, such as vowel marks (nikud), morphology and normalization. You also get:

- a **catalog** of every resource, with its licence written down exactly as its source states it;
- **guides** on choosing an engine, preparing images, right-to-left output and nikud;
- a **small Python pipeline** (`heb1`) that runs Tesseract on an image, with an optional fine-tuned Hebrew model for scanned books, and prints clean, logical-order, right-to-left text.

By John K ([ALENZA CODES](https://github.com/ALENZACODES)), Toronto, Ontario.

## Quick start

```sh
# 1. Tesseract with Hebrew
sudo apt install tesseract-ocr tesseract-ocr-heb      # Debian / Ubuntu
brew install tesseract tesseract-lang                  # macOS

# 2. Heb1
git clone https://github.com/ALENZACODES/Heb1 && cd Heb1
pip install -e .

# 3. Read an image
heb1 read sign.jpg                         # stock Tesseract heb model
heb1 read book.png --model heocr-r8b       # alternative model for scanned serif book print (vendored here)
heb1 read page.png --psm 3 --format json   # whole page, JSON with mean confidence
heb1 read siddur.png --nikud strip         # drop vowel points and teamim from the output
heb1 doctor                                # what is installed
```

Example output for a line from the siddur: `ברוך אתה ה׳ אלהינו מלך העולם`. The divine Name is always shown as **ה׳**.

### What `heb1 read` does

1. **Prepares the image** (Pillow only). It applies the camera's rotation, then removes EXIF and other metadata. It rescales the image so each text line is about 48 px tall (letters that are too large hurt as much as letters that are too small), stretches the contrast, and turns light-on-dark signs into dark-on-light. Then it applies a median filter, Otsu black and white and a white margin. `--deskew` straightens a slightly tilted page.
2. **Runs Tesseract** (`--oem 1`, LSTM) with `heb`, `heb-fast` or `heocr-r8b`, and reads word confidences from its TSV output.
3. **Optionally fixes words** (`--lexicon words.txt`). A word changes only when Tesseract was unsure **and** exactly one word in your list is close by Tesseract's usual look-alike mistakes (ב/כ, ד/ר, ה/ח, ו/ז/י/ן, ס/ם).
4. **Cleans the text.** This step:
   - applies Unicode NFC and unfolds Hebrew presentation forms;
   - removes invisible direction marks;
   - re-reverses any line that came back in visual order;
   - converts ASCII `"` and `'` to ״ and ׳;
   - fixes final letters (כ→ך at a word's end, ך→כ inside it);
   - can strip nikud or teamim;
   - writes the Name as ה׳.
5. **Prints** plain text (`--rtl-mark` adds an RLM at the start of each line for plain-text viewers), JSON, or HTML with `dir="rtl"`.

`heb1 clean FILE` runs step 4 on text you already have. `heb1 strip-metadata IN OUT` re-saves an image with pixels only.

## Which OCR should I use?

| Material | Start with | Then try |
|---|---|---|
| Modern print: books, newspapers, documents | stock `heb` and `--model heocr-r8b --psm 3`, then keep the better one for your scans | [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF) for PDFs |
| Signs, menus, phone photos | `heb1 read` (psm 6, default prep) with `--lexicon` | crop to the text first; `--psm 7` for one line |
| Pointed text: siddur, chumash, children's books | stock `heb` with `--nikud strip`, then match against a stored text ([Sefaria export](https://github.com/Sefaria/Sefaria-Export)) | restore nikud with a model rather than trusting OCR'd points |
| Medieval manuscripts and other square-script hands (incl. Torah scrolls, untested) | [kraken](https://github.com/mittagessen/kraken) + [BiblIA models](https://zenodo.org/records/5468286) in [eScriptorium](https://gitlab.com/scripta/escriptorium) | fine-tune on a few pages of your own hand |
| Modern handwriting | [Hebrew handwriting OCR (TrOCR-CTC)](https://huggingface.co/cyttic/hebrew-ocr-android) | [HeOCR R3h](https://huggingface.co/HeOCR/heocr-r3h-recognition) (synthetic-trained baseline) |
| Single handwritten letters (tracing apps) | a small CNN trained on [HHD_v0](https://zenodo.org/records/4287442) + OFL fonts | see [guides/lessons-from-alef.md](guides/lessons-from-alef.md) |

Details: [guides/choosing-an-ocr.md](guides/choosing-an-ocr.md) · [guides/preprocessing.md](guides/preprocessing.md) · [guides/rtl-and-nikud.md](guides/rtl-and-nikud.md) · [guides/lessons-from-alef.md](guides/lessons-from-alef.md)

## Catalog

The machine-readable version is [catalog/catalog.json](catalog/catalog.json). To download any linked item from its original source, after its licence is shown:

```sh
python fetch/fetch.py --list
python fetch/fetch.py hhd                 # HHD_v0 from Zenodo (CC-BY-4.0)
python fetch/fetch.py biblia-model        # kraken model from Zenodo (CC-BY-SA-4.0)
python fetch/fetch.py sofer-mahir         # non-commercial: asks you to confirm first
```

<!-- catalog:start -->
79 resources: 2 vendored in this repo, 77 linked (fetched from the original source with `fetch/fetch.py`). Licences as stated by each source, checked 2026-11-12.

### Engines

| Name | Use | Licence | Commercial use | In repo |
|---|---|---|---|---|
| [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) | printed OCR | Apache-2.0 | yes | link |
| [Tesseract.js](https://github.com/naptha/tesseract.js) | printed OCR (browser) | Apache-2.0 | yes | link |
| [kraken](https://github.com/mittagessen/kraken) | handwriting / manuscripts | Apache-2.0 | yes | link |
| [Surya](https://github.com/datalab-to/surya) | multilingual OCR + layout | Apache-2.0 (code); modified AI Pubs Open Rail-M (weights) | conditional | link |
| [hebOCR (HOCR)](https://github.com/yaacov/hebocr) | printed OCR (classic) | GPL-3.0 | yes | link |

### Models

| Name | Use | Licence | Commercial use | In repo |
|---|---|---|---|---|
| [tessdata_fast heb.traineddata](https://github.com/tesseract-ocr/tessdata_fast) | printed OCR | Apache-2.0 | yes | vendored |
| [tessdata_best heb.traineddata](https://github.com/tesseract-ocr/tessdata_best) | printed OCR | Apache-2.0 | yes | link |
| [tessdata_best script/Hebrew.traineddata](https://github.com/tesseract-ocr/tessdata_best/tree/main/script) | printed OCR (Hebrew script, incl. Yiddish) | Apache-2.0 | yes | link |
| [HeOCR R8b (Tesseract)](https://huggingface.co/HeOCR/heocr-r8b-tesseract-heb) | printed OCR | Apache-2.0 | yes | vendored |
| [HeOCR R7 (Tesseract)](https://huggingface.co/HeOCR/heocr-r7-tesseract-heb) | printed OCR | Apache-2.0 | yes | link |
| [HeOCR R6 (Tesseract)](https://huggingface.co/HeOCR/heocr-r6-tesseract-heb) | printed OCR | Apache-2.0 | yes | link |
| [HeOCR R3h recognition (kraken)](https://huggingface.co/HeOCR/heocr-r3h-recognition) | modern documents, print + handwriting-style | Apache-2.0 | yes | link |
| [HeOCR R4d segmentation (kraken)](https://huggingface.co/HeOCR/heocr-r4d-segmentation) | line segmentation | Apache-2.0 | yes | link |
| [HeOCR A1 reading order](https://huggingface.co/HeOCR/heocr-a1-reading-order) | reading order | Apache-2.0 | yes | link |
| [BiblIA_01 Medieval Hebrew (kraken)](https://zenodo.org/records/5468286) | medieval manuscripts | CC-BY-SA-4.0 | yes | link |
| [Ashkenazi_01 (kraken)](https://zenodo.org/records/5468478) | medieval manuscripts | CC-BY-SA-4.0 | yes | link |
| [Italian_01 (kraken)](https://zenodo.org/records/5468573) | medieval manuscripts | CC-BY-SA-4.0 | yes | link |
| [Sephardi_01 (kraken)](https://zenodo.org/records/5468665) | medieval manuscripts | CC-BY-SA-4.0 | yes | link |
| [Sofer Mahir models](https://github.com/dstoekl/sofer_mahir) | rabbinic manuscripts (segmentation + HTR) | CC-BY-NC-SA-4.0 | **no** | link |
| [Hebrew handwriting OCR (TrOCR-CTC, on-device)](https://huggingface.co/cyttic/hebrew-ocr-android) | handwriting lines | MIT (dictabert-tiny parts CC-BY-4.0) | yes | link |
| [PP-OCRv5 server text detector (ONNX)](https://huggingface.co/PaddlePaddle/PP-OCRv5_server_det_onnx) | text detection | Apache-2.0 | yes | link |
| [PyLaia Hebrew synthetic lines](https://huggingface.co/johnlockejrr/pylaia-heb_synth_lines_pytorch_2) | printed/handwritten lines (PyLaia) | MIT | yes | link |
| [PP-OCRv6 Samaritan/Hebrew](https://huggingface.co/johnlockejrr/ppocrv6-sam-heb) | Samaritan and Hebrew lines | Apache-2.0 | yes | link |
| [Hebrew manuscripts letter classifier](https://huggingface.co/bsesic/HebrewManuscriptsMNIST) | single-letter classification | MIT | yes | link |
| [Paleo-Hebrew post-OCR (mT5)](https://huggingface.co/mr3vial/paleo-hebrew-mt5-post-ocr-processing) | post-OCR correction (paleo-Hebrew) | MIT | yes | link |
| [testing-trOCR-hebrew-handwritten](https://huggingface.co/sivan22/testing-trOCR-hebrew-handwritten) | handwriting (experimental) | none stated | unclear | link |
| [hebrew-htr-trocr](https://huggingface.co/oln-1/hebrew-htr-trocr) | handwriting | none stated | unclear | link |
| [ocr-rec-hebrew-crnn (ONNX)](https://huggingface.co/sentraio/ocr-rec-hebrew-crnn) | printed line recognition | none stated | unclear | link |
| [Qwen3-VL Hebrew HTR adapters](https://huggingface.co/kohelet-splendour/qwen3-vl-hebrew-htr) | handwriting (VLM LoRA) | none stated | unclear | link |
| [DictaBERT-large char menaked](https://huggingface.co/dicta-il/dictabert-large-char-menaked) | nikud restoration | CC-BY-4.0 | yes | link |
| [DictaBERT joint](https://huggingface.co/dicta-il/dictabert-joint) | morphology + syntax + lemmas | CC-BY-4.0 | yes | link |
| [DictaBERT seg](https://huggingface.co/dicta-il/dictabert-seg) | prefix segmentation | CC-BY-4.0 | yes | link |
| [DictaBERT morph](https://huggingface.co/dicta-il/dictabert-morph) | morphological tagging | CC-BY-4.0 | yes | link |
| [DictaBERT lex](https://huggingface.co/dicta-il/dictabert-lex) | lemmatization | CC-BY-4.0 | yes | link |
| [DictaBERT NER](https://huggingface.co/dicta-il/dictabert-ner) | named entities (keep names out of OCR correction) | CC-BY-4.0 | yes | link |
| [BEREL 3.0](https://huggingface.co/dicta-il/BEREL_3.0) | Rabbinic Hebrew language model | Apache-2.0 | yes | link |
| [MsBERT (manuscripts)](https://huggingface.co/dicta-il/MsBERT) | manuscript Hebrew language model | CC-BY-4.0 | yes | link |
| [AlephBertGimmel base](https://huggingface.co/dicta-il/alephbertgimmel-base) | Hebrew language model | CC0-1.0 | yes | link |
| [AlephBERT base](https://huggingface.co/onlplab/alephbert-base) | Hebrew language model | Apache-2.0 | yes | link |
| [Phonikud ONNX](https://huggingface.co/thewh1teagle/phonikud-onnx) | nikud + phonemes + stress | MIT | yes | link |
| [D-Nikud](https://huggingface.co/NadavShaked/D_Nikud) | nikud restoration | none stated | unclear | link |
| [hebrew_punctuation](https://huggingface.co/verbit/hebrew_punctuation) | punctuation restoration | Apache-2.0 | yes | link |

### Datasets

| Name | Use | Licence | Commercial use | In repo |
|---|---|---|---|---|
| [HHD_v0 Hebrew handwritten letters](https://zenodo.org/records/4287442) | handwritten letters | CC-BY-4.0 | yes | link |
| [hebrew-handwritten-characters (HHD mirror)](https://huggingface.co/datasets/sivan22/hebrew-handwritten-characters) | handwritten letters | CC-BY-3.0 | yes | link |
| [hebrew-handwritten-dataset (parquet)](https://huggingface.co/datasets/sivan22/hebrew-handwritten-dataset) | handwritten letters | CC-BY-3.0 | yes | link |
| [BiblIA open annotated dataset](https://zenodo.org/records/5167263) | medieval manuscripts (ALTO) | CC-BY-NC-SA-4.0 | **no** | link |
| [Hebrew handwriting OCR benchmark](https://huggingface.co/datasets/ivrit-ai/hebrew-handwriting-ocr-benchmark) | handwriting lines + pages (test) | other ("ivrit.ai" licence), gated | unclear | link |
| [DiffusionPen Hebrew handwriting (synthetic)](https://huggingface.co/datasets/cyttic/diffusionpen-hebrew-handwriting) | synthetic handwriting lines | MIT (Hub tag); card text says CC-BY-4.0 | unclear | link |
| [matan Hebrew handwriting words](https://huggingface.co/datasets/cyttic/matan-hebrew-handwriting-words) | handwritten words | other (placeholder; see original corpus) | unclear | link |
| [synth-HTR](https://huggingface.co/datasets/sivan22/synth-HTR) | synthetic handwriting lines | none stated | unclear | link |
| [hebrew-ocr-doctags-dataset_v2](https://huggingface.co/datasets/youssefkhalil320/hebrew-ocr-doctags-dataset_v2) | document OCR (DocTags) | none stated | unclear | link |
| [hebrew-ocr-dataset (TSV)](https://huggingface.co/datasets/mbole/hebrew-ocr-dataset) | OCR text pairs | none stated | unclear | link |
| [HebrewManuscripts](https://huggingface.co/datasets/bsesic/HebrewManuscripts) | manuscript letters | MIT | yes | link |
| [YidTakNL corpus (Amsterdam regulations)](https://zenodo.org/records/11179901) | Yiddish/Hebrew-script ground truth | CC-BY-4.0 | yes | link |
| [Project Ben-Yehuda public-domain dump](https://github.com/projectbenyehuda/public_domain_dump) | Hebrew literature text (OCR language models, labels) | Public domain | yes | link |
| [Sefaria export](https://github.com/Sefaria/Sefaria-Export) | Torah, siddur and rabbinic texts | per text: Public Domain / CC0 / CC-BY / CC-BY-SA / CC-BY-NC | conditional | link |
| [National Library of Israel: Ktiv Hebrew manuscripts](https://www.nli.org.il/en/discover/manuscripts/hebrew-manuscripts) | manuscript images (IIIF) | per item: terms set by each holding library | unclear | link |

### Tools

| Name | Use | Licence | Commercial use | In repo |
|---|---|---|---|---|
| [eScriptorium](https://gitlab.com/scripta/escriptorium) | manuscript transcription platform | MIT | yes | link |
| [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF) | searchable PDFs | MPL-2.0 | yes | link |
| [HeOCR engine](https://github.com/HeOCR/heocr-engine) | OCR baselines and training records | MIT | yes | link |
| [HeOCR hocrgen](https://github.com/HeOCR/hocrgen) | synthetic Hebrew page generation | MIT | yes | link |
| [TextRecognitionDataGenerator](https://github.com/Belval/TextRecognitionDataGenerator) | synthetic line images | MIT | yes | link |
| [Nakdimon](https://github.com/elazarg/nakdimon) | nikud restoration | MIT | yes | link |
| [UNIKUD](https://github.com/morrisalp/unikud) | nikud restoration | MIT | yes | link |
| [Phonikud (code)](https://github.com/thewh1teagle/phonikud) | Hebrew grapheme-to-phoneme | CC-BY-4.0 | yes | link |
| [YAP parser](https://github.com/OnlpLab/yap) | morphology + dependency parsing | Apache-2.0 | yes | link |
| [hebrew (Python package)](https://github.com/avi-perl/Hebrew) | text normalization, nikud, gematria | MIT | yes | link |
| [Hspell](https://github.com/synhershko/hspell) | spell checking / morphology | AGPL-3.0 | yes | link |
| [alef-tools (ocr-fix, handwriting, nikud packages)](https://github.com/ALENZACODES/alef-tools) | browser OCR clean-up, letter checker, nikud packs | MIT (author's own code) | yes | link |

### Fonts for synthetic training data

| Name | Use | Licence | Commercial use | In repo |
|---|---|---|---|---|
| [Frank Ruhl Libre](https://github.com/google/fonts/tree/main/ofl/frankruhllibre) | synthetic training data (serif print) | OFL-1.1 | yes | link |
| [David Libre](https://github.com/google/fonts/tree/main/ofl/davidlibre) | synthetic training data (print) | OFL-1.1 | yes | link |
| [Noto Sans Hebrew](https://github.com/google/fonts/tree/main/ofl/notosanshebrew) | synthetic training data (sans) | OFL-1.1 | yes | link |
| [Noto Serif Hebrew](https://github.com/google/fonts/tree/main/ofl/notoserifhebrew) | synthetic training data (serif, nikud) | OFL-1.1 | yes | link |
| [Culmus fonts](https://culmus.sourceforge.io/) | synthetic training data (incl. Taamey for teamim) | GPL-2.0, some fonts with embedding exception | yes | link |

### Web services (not open licences)

| Name | Use | Licence | Commercial use | In repo |
|---|---|---|---|---|
| [DiJeSt 3.0 (Transkribus)](https://www.transkribus.org/models/dijest-30) | printed Hebrew/Yiddish | platform terms (not an open licence) | unclear | link |
| [Dicta Nakdan (web)](https://nakdan.dicta.org.il/) | nikud | free web service; Dicta terms of use | unclear | link |

### Other lists

| Name | Use | Licence | Commercial use | In repo |
|---|---|---|---|---|
| [HTR-United catalog](https://htr-united.github.io/) | ground-truth catalog | CC0-1.0 | yes | link |
| [awesome-hebrew-nlp](https://github.com/iddoberger/awesome-hebrew-nlp) | resource list | none stated | unclear | link |
| [NNLP-IL Hebrew Resources](https://github.com/NNLP-IL/Hebrew-Resources) | resource list | per folder (see repo) | unclear | link |
<!-- catalog:end -->

## Licences at a glance

- **Heb1's own code** (`heb1/`, `fetch/`, `tools/`, `tests/`, guides) is MIT. See [LICENSE](LICENSE).
- **Vendored folders keep their own licences.** Only items whose licence allows redistribution are copied in, each with its LICENSE, NOTICE and an ATTRIBUTION.md giving the source, revision and checksum:
  - `vendor/tessdata-fast-heb/` holds Tesseract's `heb.traineddata` (Apache-2.0).
  - `vendor/heocr-r8b/` holds HeOCR R8b (Apache-2.0, with credits to the National Library of Israel and Project Ben-Yehuda in its NOTICE).
- **Commercial use "yes"** means the stated licence allows it: MIT, Apache-2.0, BSD, CC0, CC-BY, OFL, public domain, and the copyleft GPL, AGPL, MPL and CC-BY-SA, which come with share-alike or source-sharing duties. Always read the licence yourself.
- **"no"** means non-commercial (CC-BY-NC, CC-BY-NC-SA). These are listed and fetched from the source only, never copied here.
- **"unclear"** means no licence is stated, "other", or platform terms. These are also listed and fetched only. A missing licence means **all rights reserved** until the author says otherwise.
- **"conditional"** means the terms depend on who you are or which part you use (for example Surya's weights, or Sefaria texts with per-text licences).
- Big model weights are never committed. No file in this repository is over 50 MB, and CI checks this.

### Left out because of licensing

These are catalogued but **not** vendored:
- **Non-commercial:** the BiblIA dataset (CC-BY-NC-SA-4.0) and the Sofer Mahir models (CC-BY-NC-SA-4.0).
- **No licence stated:**
  - testing-trOCR-hebrew-handwritten, hebrew-htr-trocr, ocr-rec-hebrew-crnn and the Qwen3-VL HTR adapters;
  - D-Nikud;
  - the synth-HTR, hebrew-ocr-doctags and hebrew-ocr-dataset datasets;
  - awesome-hebrew-nlp.
- **"Other" or gated terms:** the ivrit.ai handwriting benchmark and matan words.
- **Conflicting tags:** DiffusionPen Hebrew.
- **Platform or site terms:** DiJeSt 3.0 on Transkribus, Dicta Nakdan on the web, and NLI items with per-item rights.
- **Conditional weights:** Surya.

Allowed licences that were still not vendored, to keep the repo small, are linked with a fetch entry. Examples are the BiblIA kraken models (16 MB each), the DictaBERT family (0.7–1.7 GB) and HHD (43 MB).

## Repository layout

```
heb1/            the pipeline (text.py clean-up, preprocess.py, ocr.py, correct.py, cli.py)
catalog/         catalog.json, built from tools/catalog_src.py
fetch/fetch.py   download a linked resource from its source, licence first
vendor/          redistributable models, each with its own LICENSE + ATTRIBUTION.md
guides/          how-to guides
tools/           build_catalog.py (README tables), check_links.py
tests/           pytest; OCR tests run when Tesseract is installed (always in CI)
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). New resources need a source link and the licence exactly as the source states it.

## Credits

Heb1 stands on the work of the Tesseract project, HeOCR, Dicta, the BiblIA and Sofer Mahir projects (EPHE-PSL and partners), and the HHD authors (Rabaev, Kurar Barakat, Churkin and El-Sana). It also builds on Project Ben-Yehuda volunteers, the National Library of Israel, Sefaria, and everyone in the catalog. Each resource's own licence and citation request applies.
