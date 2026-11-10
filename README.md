# Storefront Fonts Catalog

Curated, open-license typography catalog for e-ink readers (Kindle, Kobo, Boox, PocketBook, and Android). Powered by the [Storefront KOReader Plugin](https://github.com/ultimatejimmy/storefront.koplugin).

🌐 **[Browse the Web Specimen Gallery](https://ultimatejimmy.github.io/storefront-fonts/)**

---

## Overview

This repository serves three main purposes:
1. **Catalog Source of Truth (`fonts.json` & `fonts.lite.json`)**: An automated JSON catalog consumed by the Storefront KOReader plugin to browse and install font families directly on e-readers.
2. **Compact Subsetted Preview Pack (`previews/font_previews.zip`)**: Micro-subsetted `.ttf` font files (~5–12 KB each) enabling razor-sharp FreeType/MuPDF font rendering in the plugin catalog without bloating device storage.
3. **[Interactive Web Specimen Gallery](https://ultimatejimmy.github.io/storefront-fonts/)**: A responsive web application to test-type custom text, adjust point sizes, and submit new font requests.

---

## Open-License Submissions (Zero Binary Uploads)

To maintain strict compliance with font licensing and avoid copyright infringement:
* **No font files are accepted via uploads or PR attachments.**
* Users submit font requests via **GitHub Issues** by providing the font name, designer/foundry, open-source license (`SIL OFL 1.1`, `Apache 2.0`, `MIT`), and official upstream repository link.
* Automated CI tooling inspects the upstream repository, validates license headers, and builds the distribution packages and subsetted previews.

---

## Attribution & Legal

All fonts in this catalog are distributed in accordance with their respective open licenses. Every `.zip` package includes the original copyright notice and `OFL.txt` / `LICENSE.txt`. Full attributions are listed in [`CREDITS.md`](CREDITS.md).
