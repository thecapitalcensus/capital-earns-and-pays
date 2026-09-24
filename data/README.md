# data/ — raw inputs

Included (redistributable public data):

- `DFII10.csv` — FRED, 10-year TIPS real yield, daily (used for the inflation-linked sleeve from 2003).
- `wb_mktcap_countries.json` — World Bank CM.MKT.LCAP.CD, market capitalisation of listed domestic companies by country, current USD (weights for the 16-country dividend–price panel).

Not included — obtain them yourself before running `jst_equity_dy.py` / `build_v2.py`:

| File | Source | How |
|---|---|---|
| `JSTdatasetR6.xlsx` | Jordà–Schularick–Taylor Macrohistory Database, release 6 | https://www.macrohistory.net/database/ — download after accepting the CC BY-NC-SA 4.0 terms; save the R6 Excel workbook under this name. |
| `ie_data_2026.xls` | Robert Shiller, online data | `python3 fetch_data.py --shiller` (http://www.econ.yale.edu/~shiller/data/ie_data.xls) |
| `etf_<TICKER>.csv` | Yahoo Finance via `yfinance` | `python3 fetch_data.py --etf` — tickers ACWI, VT, LQD, HYG, EMB, MBB, TIP, IEF, BWX, IGOV, SPY, EFA, EEM; columns `Date,Close,Adj Close,Dividends`. |

`fetch_data.py --fred --wb` refreshes the FRED, World Bank and Penn World Table copies under `inputs/`. Refreshed copies will differ from the ones the note used; the note's inputs are identified by the SHA-256 values in `MANIFEST.md`.
