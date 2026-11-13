# Contributing to Heb1

Thank you for helping make Hebrew OCR easier for everyone.

## Adding a resource

1. Add an `add(...)` line to `tools/catalog_src.py`. Include:
   - the source URL;
   - the licence **exactly as the source states it**, and where it is stated (`license_source`);
   - `commercial`: `yes`, `no`, `unclear` or `conditional`.

   A missing licence is `"none stated"` / `unclear`. Never guess.
2. If the file can be downloaded, add a `fetch` entry (`hf`, `hf-dataset`, `zenodo`, `github` or `url`) that points at the **original** source.
3. Run `python tools/build_catalog.py` to regenerate `catalog/catalog.json` and the README tables, then `pytest`.

## Vendoring (copying files into `vendor/`)

Only when **all** of these are true:

- the licence allows redistribution (MIT, Apache-2.0, BSD, CC0, CC-BY, CC-BY-SA, OFL, GPL family with the licence kept);
- every file is under 50 MB (big weights stay as `fetch` entries);
- the folder contains the upstream `LICENSE` (and `NOTICE` if there is one), copied unchanged, plus an `ATTRIBUTION.md` with the source, revision and sha256.

Non-commercial and unclear licences are **never** vendored.

## Code

- Python 3.9+. Pillow is the only runtime dependency.
- Add tests in `tests/`. OCR tests that need Tesseract skip themselves locally and always run in CI.
- Images: commit none if you can (generate test images in the test). If you must commit one, strip its metadata first (`heb1 strip-metadata in.png out.png`).
- Sample text: write the divine Name as ה׳.

## Pull requests

Open a PR against `main`. CI must be green before merging. No force-pushes to `main`.
