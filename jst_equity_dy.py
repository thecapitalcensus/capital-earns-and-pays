# -*- coding: utf-8 -*-
"""World equity dividend yield without MSCI data: Macrohistory Database (JST R6) eq_dp for 16 countries, 1975-2020,
weighted by World Bank listed market capitalisation; from 2021 the iShares MSCI ACWI fund's distributions + fee.
Also the world dividend-price ratio used as the equity valuation measure. Writes output/equity_dy_jst.csv."""
import os, json, numpy as np, pandas as pd
B = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(B, "data"); OUT = os.path.join(B, "output")
IDX = pd.date_range("1975-12-31", "2026-06-30", freq="ME")
JST = os.path.join(D, "JSTdatasetR6.xlsx")
if os.path.exists(JST):   # full computation from the Macrohistory workbook (not redistributed; see README)
    d = pd.read_excel(os.path.join(D, "JSTdatasetR6.xlsx"))
    dp = d[d.year >= 1970].pivot(index="year", columns="iso", values="eq_dp").replace(0.0, np.nan) * 100
    dp = dp.dropna(axis=1, how="all")                                   # drops CAN, IRL (no series)
    j = json.load(open(os.path.join(D, "wb_mktcap_countries.json")))[1]
    cap = pd.DataFrame({(int(x["date"]), x["countryiso3code"]): x["value"] for x in j if x["value"]}, index=[0]).T[0].unstack()
    cap = cap.reindex(range(1975, 2026)).ffill() / 1e9                    # bn USD; stale shares carried forward where WB stops
    common = [c for c in dp.columns if c in cap.columns]
    w = cap[common].where(dp[common].notna()); w = w.div(w.sum(axis=1), axis=0)
    dy_a = (dp[common] * w).sum(axis=1, min_count=1).loc[1975:2020]        # cap-weighted panel D/P, % (year-end)
    cov = cap[common].where(dp[common].notna()).sum(axis=1) / cap.sum(axis=1)
    # monthly: linear interpolation between year-ends
    s = pd.Series(dy_a.values, index=pd.to_datetime([f"{y}-12-31" for y in dy_a.index]))
    m = s.reindex(s.index.union(IDX)).interpolate(method="time", limit_area="inside").reindex(IDX)
    # fund extension from 2021: ACWI trailing distributions + fee, blended over 12 months
    h = pd.read_csv(os.path.join(D, "etf_ACWI.csv"), index_col=0, parse_dates=True)
    px = h["Close"].resample("ME").last(); dv = h["Dividends"].resample("ME").sum()
    acwi = (dv.rolling(12).sum() / px * 100 + 0.32); acwi = acwi[px.index >= px.index[0] + pd.DateOffset(months=24)].reindex(IDX)
    lvl = float((m - acwi).loc["2011-01-31":"2020-12-31"].mean())          # panel minus fund on the overlap (withholding, universe)
    out = m.copy(); ext = acwi.loc["2021-01-31":] + lvl
    bl = ext.index[:12]; lam = np.linspace(0, 1, 14)[1:-1]
    out.loc[bl] = (1 - lam) * m.loc["2020-12-31"] + lam * ext.loc[bl].values; out.loc[ext.index[12:]] = ext.loc[ext.index[12:]]
    res = pd.DataFrame({"dy_jst_world": out, "dy_jst_panel_annual_interp": m, "acwi_dist_plus_fee": acwi})
    res.round(4).to_csv(os.path.join(OUT, "equity_dy_jst.csv"))
else:                     # release fallback: the derived series shipped in output/ (CC BY-NC-SA 4.0)
    _meta = json.load(open(os.path.join(OUT, "equity_dy_jst_meta.json")))
    res = pd.read_csv(os.path.join(OUT, "equity_dy_jst.csv"), index_col=0, parse_dates=True)
    out, m, acwi = res["dy_jst_world"], res["dy_jst_panel_annual_interp"], res["acwi_dist_plus_fee"]
    lvl = _meta["lvl"]; common = _meta["common"]; cov = pd.Series({int(k): v for k, v in _meta["cov"].items()})
if __name__ == "__main__":
    print("countries:", common); print("panel share of world cap:", cov.loc[[1976, 1990, 2000, 2010, 2020]].round(2).to_dict())
    print("panel minus ACWI fund on 2011-20 overlap: %.2f pt" % lvl)
    old = pd.read_csv(os.path.join(OUT, "sleeve_yields_v1_0.csv"), index_col=0, parse_dates=True)["EQ"]
    cmp = pd.DataFrame({"JST world (new)": out, "composite (current note)": old}).resample("YE").mean(); cmp.index = cmp.index.year
    cmp["Opus v1.1 (MSCI+JST)"] = pd.Series({1976: 3.8, 1981: 4.4, 1990: 2.3, 2000: 1.4, 2007: 2.3, 2012: 2.9, 2021: 2.0, 2025: 1.9})
    print(cmp.loc[[1976, 1981, 1985, 1989, 1990, 1995, 2000, 2007, 2009, 2012, 2016, 2019, 2021, 2023, 2025]].round(2).to_string())
    # equity valuation change on world D/P: log change of P/D, % a year, 1976-01..2026-06
    v = -np.log(out.loc["2026-06-30"] / out.loc["1976-01-31"]) / ((2026 + 5 / 12) - (1976 + 0 / 12)) * 100
    print("equity valuation change on world D/P, %% a year 1976-2026: %.2f" % v)
