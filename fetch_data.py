# -*- coding: utf-8 -*-
"""Download the public inputs of 'What the World's Capital Earns and Pays'.

    python3 fetch_data.py --fred --wb --shiller --etf      # any subset; --all for everything

FRED and World Bank files are written under inputs/ and data/ in the layout the build scripts expect.
The Macrohistory workbook (data/JSTdatasetR6.xlsx) cannot be fetched by script: download it from
https://www.macrohistory.net/database/ after accepting its terms. Fund histories (--etf) need the
`yfinance` package and are for your own use only (see LICENSE.md)."""
import argparse, glob, io, json, os, sys, urllib.request

B = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (capital-earns-and-pays fetch_data.py)"}
FRED_ENGINE = ["DGS10", "GS5", "AAA", "BAA", "CPIAUCSL"] + [f"IRLTLT01{c}M156N" for c in ["JP", "DE", "GB", "CA", "FR", "IT"]]
PWT_CC = ["AR", "AT", "AU", "BE", "BR", "CA", "CH", "CL", "CN", "CO", "CZ", "DE", "DK", "ES", "FI", "FR", "GB", "GR", "HK", "HU", "ID",
          "IE", "IL", "IN", "IT", "JP", "KR", "MX", "MY", "NL", "NO", "NZ", "PH", "PL", "PT", "RU", "SA", "SE", "SG", "TH", "TR", "US", "ZA"]
ETFS = ["ACWI", "VT", "LQD", "HYG", "EMB", "MBB", "TIP", "IEF", "BWX", "IGOV", "SPY", "EFA", "EEM"]

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r: return r.read()

def fred_csv(series, path):
    """FRED CSV export; the build scripts rename the two columns, so the header wording does not matter."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "wb").write(get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}")); print("fred ", series, "->", os.path.relpath(path, B))

def wb_json(indicator, path, date="1960:2026"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    raw = get(f"https://api.worldbank.org/v2/country/all/indicator/{indicator}?format=json&per_page=20000&date={date}")
    j = json.loads(raw); assert isinstance(j, list) and len(j) == 2, "unexpected World Bank response"
    open(path, "wb").write(raw); print("wb   ", indicator, "->", os.path.relpath(path, B), len(j[1]), "rows")

def main():
    ap = argparse.ArgumentParser(); [ap.add_argument(f"--{k}", action="store_true") for k in ["fred", "wb", "shiller", "etf", "all"]]
    a = ap.parse_args(); on = lambda k: a.all or getattr(a, k)
    if not any(on(k) for k in ["fred", "wb", "shiller", "etf"]): ap.print_help(); return
    if on("fred"):
        for s in FRED_ENGINE: fred_csv(s, os.path.join(B, "inputs", "engine", "data", ("y_" if s.startswith("IRLTLT01") else "") + s + ".csv"))
        fred_csv("DFII10", os.path.join(B, "data", "DFII10.csv"))
        for c in PWT_CC:
            fred_csv(f"EMPENG{c}A148NRUG", os.path.join(B, "inputs", "wb_pwt", f"EMPENG{c}A148NRUG.csv"))
            try: fred_csv(f"AVHWPE{c}A065NRUG", os.path.join(B, "inputs", "wb_pwt", f"AVHWPE{c}A065NRUG.csv"))
            except Exception as e: print("  (no hours series for", c, "- 2,100 h/yr assumed by build_v2.py)")
    if on("wb"):
        wb_json("NY.GDP.MKTP.CD", os.path.join(B, "inputs", "wb_pwt", "wb_gdp.json"))
        wb_json("SP.POP.TOTL", os.path.join(B, "inputs", "wb_pwt", "wb_pop.json"))
        wb_json("CM.MKT.LCAP.CD", os.path.join(B, "data", "wb_mktcap_countries.json"), date="1975:2025")
    if on("shiller"):
        p = os.path.join(B, "data", "ie_data_2026.xls"); open(p, "wb").write(get("http://www.econ.yale.edu/~shiller/data/ie_data.xls")); print("shiller ->", os.path.relpath(p, B))
    if on("etf"):
        import yfinance as yf
        for t in ETFS:
            h = yf.Ticker(t).history(period="max", actions=True, auto_adjust=False)
            h.index = h.index.tz_localize(None).normalize(); h.index.name = "Date"
            h[["Close", "Adj Close", "Dividends"]].to_csv(os.path.join(B, "data", f"etf_{t}.csv")); print("etf  ", t, len(h), "rows")

if __name__ == "__main__": main()
