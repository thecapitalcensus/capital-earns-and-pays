# What the World's Capital Earns and Pays

Code and derived data for the third Capital Census research note:

> Nakanishi, K. (2026). *What the World's Capital Earns and Pays: The Global Market Portfolio in Dollars and in Hours of the World's Work.* Research note, draft v1.4, 23 September 2026. SSRN abstract 7515699, https://ssrn.com/abstract=7515699 (doi:10.2139/ssrn.7515699 on approval). Site version: https://thecapitalcensus.github.io/income.html

The note follows the investable global market portfolio (GMP) month by month from January 1976 to June 2026, splits its total return into cash distributions, valuation changes and the rest, and measures each in *world hours* (nominal GDP per hour worked across 43 countries). It extends the first two notes in the series:

- Nakanishi (2026a), *Owning the Market as It Is*, doi:10.2139/ssrn.7394599 (the GMP index)
- Nakanishi (2026b), *Measuring Assets in Hours of the World's Work*, doi:10.2139/ssrn.7445203 (the world hour)

## Layout

| Path | Content |
|---|---|
| `jst_equity_dy.py` | World equity dividend–price ratio: Macrohistory Database (JST R6) `eq_dp` for 16 countries weighted by World Bank listed market capitalisation, extended from 2021 with the ACWI fund's distributions plus fee (Table 1, Figure A1). Falls back to the shipped series when the JST workbook is absent. |
| `build_v2.py` | Everything else: floating weights, sleeve yields, the fund cross-check, the three-way decomposition, hours generated, flows as a share of world GDP, payers, holdings, sleeves, rolling windows, rent comparison, robustness, Figures 1–5. Writes `output_v2/`. |
| `build_paper_v2.py` | Fills `paper_v2_template.html` with all tables and every number quoted in the text; writes `output_v2/paper/income.html`. |
| `paper_v2_template.html` | The note's text with placeholders. |
| `output_v2/` | Derived series and tables (`*.csv`), `build_log.json` (input checksums, reproduction check, constants), `numbers_in_text.json`, figures, and `paper/` (HTML, PDF). |
| `output/` | `equity_dy_jst.csv` + `equity_dy_jst_meta.json` (the world D/P series and its coverage), and `sleeve_yields_v1_0.csv` (the v1.0 fund-calibrated yield series, used only for two robustness rows in Table 13). |
| `inputs/engine/` | The GMP index monthly return (`four_series_returns_corrected.csv`, first column = CC-GMP TR), the annual B6.1 weights (`b61/pit_weights_v2.csv`) and copies of the FRED / OECD yield series the note uses. |
| `inputs/world_hour/` | The world hour (`gdph` column only) at monthly and quarterly frequency, and the quarterly level in USD (CC-WH series). |
| `inputs/wb_pwt/` | World Bank world GDP and population (JSON), Penn World Table employment and hours per worker for the 43-country panel (via FRED). |
| `data/` | Public inputs that are redistributable (`DFII10.csv`, `wb_mktcap_countries.json`) and a README on how to obtain the ones that are not. |
| `fetch_data.py` | Downloads the public inputs (FRED, World Bank, Shiller, fund histories via `yfinance`). The Macrohistory workbook must be downloaded by hand. |
| `MANIFEST.md` | SHA-256 of every file in this repository, and of the inputs that are not included. |

## What is and is not included

Everything needed to **rebuild the paper's HTML from the shipped derived data** is here:

```bash
python3 build_paper_v2.py        # regenerates output_v2/paper/income.html from output_v2/*.csv and build_log.json
```

A **full recomputation** (`jst_equity_dy.py` then `build_v2.py`) needs three things that are not redistributed here:

1. `data/JSTdatasetR6.xlsx` — the Jordà–Schularick–Taylor Macrohistory Database, release 6, from https://www.macrohistory.net/database/ (CC BY-NC-SA 4.0; accept the terms there).
2. `data/ie_data_2026.xls` and `data/etf_*.csv` — Robert Shiller's online data and fund price/distribution histories from Yahoo Finance; `fetch_data.py` downloads them for your own use.
3. `inputs/engine/monthly_returns_corrected.csv` — the frozen engine's monthly sleeve returns behind the first two notes. Several sleeves are built from ICE BofA total-return indices distributed through FRED, whose terms do not allow redistribution, so the file is not included. Its SHA-256 is recorded in `output_v2/build_log.json` and in `MANIFEST.md`; the GMP-level return that it produces *is* included (`inputs/engine/four_series_returns_corrected.csv`, identical to the public CC-GMP TR series at https://thecapitalcensus.github.io/cc_gmp_tr.csv). Set `GMP_ENGINE_DIR` to a folder holding the file to run `build_v2.py`.

Environment variables (all optional): `GMP_ENGINE_DIR`, `CC_WH_DIR`, `CC_WB_PWT_DIR` override the `inputs/` sub-folders; `CC_SITE_DIR` points at a site folder to receive a copy of the HTML (skipped if the folder does not exist).

Differences from the code that produced v1.4: the three input-path lines at the top of `build_v2.py`, the optional site copy in `build_paper_v2.py`, the fallback branch in `jst_equity_dy.py`, and the renamed `output/sleeve_yields_v1_0.csv`. No numerical logic was changed; with the original inputs in place, `build_paper_v2.py` reproduces the v1.4 HTML byte for byte (checked 24 September 2026).

Requirements: Python 3.10+, `pandas`, `numpy`, `matplotlib`, `openpyxl`/`xlrd` (for the workbooks), `yfinance` (only for `fetch_data.py`). The PDF was rendered from the HTML with headless Chrome (`--print-to-pdf`).

## Licence

See `LICENSE.md`. In short: code MIT; the note's text (`paper_v2_template.html`, `output_v2/paper/`) CC BY-NC-ND 4.0; all derived series in `output/` and `output_v2/` CC BY-NC-SA 4.0 because they depend on the Macrohistory Database; the author's own input series in `inputs/engine/` and `inputs/world_hour/` CC BY-NC 4.0 (CC-GMP TR, CC-WH) except the annual weights, which are CC BY 4.0 (Zenodo doi:10.5281/zenodo.22151402); copies of FRED, OECD, World Bank and Penn World Table data remain under their sources' terms.

## Citation

```
Nakanishi, K. (2026). What the World's Capital Earns and Pays: The Global Market Portfolio in Dollars
and in Hours of the World's Work. Research note, draft v1.4. SSRN abstract 7515699, https://ssrn.com/abstract=7515699.
Code and data: https://github.com/thecapitalcensus/capital-earns-and-pays
```

A machine-readable version is in `CITATION.cff`.

## Contact

Keisuke Nakanishi, independent researcher — thecapitalcensus@gmail.com — ORCID 0009-0000-3780-9450
