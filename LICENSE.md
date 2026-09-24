# Licences

This repository combines material under several licences. Each file falls into exactly one of the classes below.

## 1. Code — MIT

`jst_equity_dy.py`, `build_v2.py`, `build_paper_v2.py`, `fetch_data.py`, `make_manifest.py`.

Copyright (c) 2026 Keisuke Nakanishi

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## 2. The note's text — CC BY-NC-ND 4.0

`paper_v2_template.html`, `output_v2/paper/income.html`, `output_v2/paper/income.pdf`, `output_v2/paper/style.css`.
https://creativecommons.org/licenses/by-nc-nd/4.0/ — Any SSRN posting of the note is governed by SSRN's terms, with copyright retained by the author.

## 3. Derived series and figures — CC BY-NC-SA 4.0

Everything under `output/` and `output_v2/` other than the files in class 2, including the figures (`*.png`).
https://creativecommons.org/licenses/by-nc-sa/4.0/

These series depend on the world dividend–price ratio built from the Jordà–Schularick–Taylor Macrohistory Database (release 6), which is licensed CC BY-NC-SA 4.0. Under its share-alike condition, series derived from it are released only on the same terms and are not offered under any commercial licence. Use of the Macrohistory Database requires the following citations:

- Jordà, Ò., Schularick, M. and Taylor, A. M. (2017). "Macrofinancial History and the New Business Cycle Facts." In *NBER Macroeconomics Annual 2016*, vol. 31, University of Chicago Press.
- Jordà, Ò., Knoll, K., Kuvshinov, D., Schularick, M. and Taylor, A. M. (2019). "The Rate of Return on Everything, 1870–2015." *Quarterly Journal of Economics*, 134(3), 1225–1298.

The world dividend–price ratio from 2021 onward, and the fund cross-check table, use fund prices and distributions published by Yahoo Finance as a public source for the author's own calculations; the price and distribution series themselves are not redistributed.

## 4. The author's input series — CC BY-NC 4.0, and CC BY 4.0 for the weights

- `inputs/engine/four_series_returns_corrected.csv` (first column is the CC-GMP TR monthly return) and `inputs/world_hour/*` (the CC-WH world hour): CC BY-NC 4.0, https://creativecommons.org/licenses/by-nc/4.0/ — the same terms as on https://thecapitalcensus.github.io.
- `inputs/engine/b61/pit_weights_v2.csv` (annual B6.1 weights): CC BY 4.0, as released on Zenodo, doi:10.5281/zenodo.22151402.

## 5. Copies of third-party public data — their sources' terms

`inputs/engine/data/*.csv` (FRED: DGS10, GS5, AAA, BAA, CPIAUCSL; OECD IRLTLT01 via FRED), `data/DFII10.csv` (FRED), `data/wb_mktcap_countries.json` and `inputs/wb_pwt/wb_*.json` (World Bank, CC BY 4.0), `inputs/wb_pwt/EMPENG*.csv` and `AVHWPE*.csv` (Penn World Table via FRED, CC BY 4.0). They are included as convenience copies with their retrieval dates in `MANIFEST.md`; the sources' own terms of use apply.

Not included at all: the Macrohistory workbook, Shiller's `ie_data.xls`, Yahoo Finance fund histories, and the engine's monthly sleeve returns (see README).
