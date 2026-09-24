# -*- coding: utf-8 -*-
"""What the world's capital earns and pays (note 3, v1.2): total return of the frozen GMP index split into cash,
valuation change and the rest; hours of world work generated per 1,000 hours of capital; flows as a share of world GDP;
the cash distribution yield by sleeve and by payer; holdings in world hours; rent outside the GMP; robustness.
No MSCI data: the world equity dividend yield is the Macrohistory Database (JST R6) panel weighted by World Bank market
capitalisation, extended from 2021 with the ACWI fund's distributions (jst_equity_dy.py). Outputs to output_v2/."""
import os, sys, json, hashlib, glob, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

B = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(B, "data"); OUT = os.path.join(B, "output_v2"); os.makedirs(OUT, exist_ok=True)
# Release version: input locations can be overridden by environment variables (defaults are the repository's inputs/ folder).
# The author's working copy used ~/gmp_bt_b61 (frozen engine) and ~/composite_numeraire (world hour); logic is unchanged.
B61 = os.environ.get("GMP_ENGINE_DIR", os.path.join(B, "inputs", "engine")); B61D = os.path.join(B61, "data")
CN = os.environ.get("CC_WH_DIR", os.path.join(B, "inputs", "world_hour")); CND = os.environ.get("CC_WB_PWT_DIR", os.path.join(B, "inputs", "wb_pwt"))
if not os.path.exists(os.path.join(B61, "monthly_returns_corrected.csv")):
    raise SystemExit("monthly_returns_corrected.csv (the frozen engine's monthly sleeve returns) is not part of this release; "
                     "see README.md, section 'What is and is not included'. Set GMP_ENGINE_DIR to a folder that holds it.")
IDX = pd.date_range("1975-12-31", "2026-06-30", freq="ME"); M = IDX[1:]
SL = ["EQ", "GOV", "IG", "SEC", "GOLD", "EMD", "ILB", "HY"]; LOG = {}
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()

# ------------------------------------------------------------------ 1. frozen engine
R = pd.read_csv(os.path.join(B61, "monthly_returns_corrected.csv"), index_col=0, parse_dates=True); R.index = R.index + pd.offsets.MonthEnd(0)
gmp_r = pd.read_csv(os.path.join(B61, "four_series_returns_corrected.csv"), index_col=0, parse_dates=True).iloc[:, 0]; gmp_r.index = gmp_r.index + pd.offsets.MonthEnd(0); gmp_r = gmp_r.dropna()
Wp = pd.read_csv(os.path.join(B61, "b61", "pit_weights_v2.csv"), index_col=0)[SL]
LOG["inputs_sha256"] = {f: sha(os.path.join(B61, *f.split("/"))) for f in ["monthly_returns_corrected.csv", "four_series_returns_corrected.csv", "b61/pit_weights_v2.csv"]}
for f in ["world_yardsticks_usd.csv", "world_q_yardsticks_usd.csv", "world_q_gdp_per_hour_level_usd.csv"]: LOG["inputs_sha256"][f] = sha(os.path.join(CN, f))
def float_weights(Wp, lag=1, start="1976-01"):
    Wp = Wp / 100.0; idx = R.loc[start:].index; cur = None; w_rows, r_rows, ix = [], [], []
    for t in idx:
        if cur is None or t.month == 1:
            y = t.year - lag
            if y in Wp.index: w = Wp.loc[y].values.astype(float); cur = pd.Series(w / w.sum(), index=SL)
        if cur is None: continue
        row = R.loc[t, SL]; w_rows.append(cur.copy()); r_rows.append(float((cur * row).sum())); ix.append(t)
        cur = cur * (1 + row); cur = cur / cur.sum()
    return pd.DataFrame(w_rows, index=ix), pd.Series(r_rows, index=ix)
W, rep = float_weights(Wp); chk = float((rep - gmp_r.reindex(rep.index)).abs().max()); LOG["reproduction_max_abs_diff"] = chk; assert chk < 1e-9
W = W.reindex(M); W2, _ = float_weights(Wp, lag=2, start="1977-01")   # robustness: two-year lag
r_gmp = gmp_r.reindex(M)

# ------------------------------------------------------------------ 2. yields (market-yield basis)
def fred(id_, d=B61D):
    df = pd.read_csv(os.path.join(d, f"{id_}.csv")); df.columns = ["date", "v"]; df["date"] = pd.to_datetime(df["date"]) + pd.offsets.MonthEnd(0)
    return pd.to_numeric(df.set_index("date")["v"], errors="coerce")
def fred_daily_eom(id_, d=B61D):
    df = pd.read_csv(os.path.join(d, f"{id_}.csv")); df.columns = ["date", "v"]; df["date"] = pd.to_datetime(df["date"]); df["v"] = pd.to_numeric(df["v"], errors="coerce")
    return df.set_index("date")["v"].resample("ME").last().dropna()
cpi = fred("CPIAUCSL").interpolate().reindex(IDX).ffill()          # Oct/Nov 2025 not published: interpolated
gs5 = fred("GS5").reindex(IDX); aaa = fred("AAA").reindex(IDX); baa = fred("BAA").reindex(IDX); dgs10 = fred_daily_eom("DGS10").reindex(IDX)
dfii10 = fred_daily_eom("DFII10", D).reindex(IDX)
ylds = {c: fred(f"y_IRLTLT01{c}M156N") for c in ["JP", "DE", "GB", "CA", "FR", "IT"]}; ylds["US"] = dgs10
W_CTRY = {"US": 0.42, "JP": 0.22, "DE": 0.10, "GB": 0.08, "FR": 0.08, "CA": 0.05, "IT": 0.05}
Yc = pd.DataFrame({c: ylds[c].reindex(IDX) for c in W_CTRY}); wc = pd.DataFrame({c: np.where(Yc[c].notna(), W_CTRY[c], np.nan) for c in W_CTRY}, index=IDX); wc = wc.div(wc.sum(axis=1), axis=0)
GOV_Y = (Yc * wc).sum(axis=1, min_count=1)
infl12 = (cpi.pct_change(12) * 100); pi_e = (cpi.pct_change(12).rolling(120, min_periods=36).mean() * 100)
real_proxy = (dgs10 - pi_e).clip(lower=-2.0); REAL = dfii10.combine_first(real_proxy)      # TIPS real yield from 2003
IG_Y = (aaa + baa) / 2; SEC_Y = 0.5 * gs5 + 0.5 * IG_Y
ER = {"ACWI": 0.32, "VT": 0.07, "LQD": 0.14, "HYG": 0.49, "EMB": 0.39, "MBB": 0.04, "TIP": 0.18, "IEF": 0.15, "BWX": 0.35, "IGOV": 0.20, "SPY": 0.09, "EFA": 0.32, "EEM": 0.70}
def etf_yield(t, maturity=24):
    h = pd.read_csv(os.path.join(D, f"etf_{t}.csv"), index_col=0, parse_dates=True); px = h["Close"].resample("ME").last(); dv = h["Dividends"].resample("ME").sum()
    y = dv.rolling(12).sum() / px * 100 + ER[t]; y = y[px.index >= px.index[0] + pd.DateOffset(months=maturity)]; return y.reindex(IDX)
ETF = {t: etf_yield(t) for t in ER}
def const_to_fund(base, fund):
    ov = fund.dropna().index; return float((fund.loc[ov] - base.loc[ov]).mean()), str(ov[0].date()), len(ov)
c_emd, emd_from, n_emd = const_to_fund(baa, ETF["EMB"]); c_hy, hy_from, n_hy = const_to_fund(baa, ETF["HYG"])
EMD_Y = baa + c_emd; HY_Y = baa + c_hy; ILB_Y = REAL + infl12; GOLD_Y = pd.Series(0.0, index=IDX)
sys.path.insert(0, B); import jst_equity_dy as jst
EQ_Y = jst.out.reindex(IDX); DP_WORLD = EQ_Y                          # world dividend-price ratio (JST + ACWI), %
Y = pd.DataFrame({"EQ": EQ_Y, "GOV": GOV_Y, "IG": IG_Y, "SEC": SEC_Y, "GOLD": GOLD_Y, "EMD": EMD_Y, "ILB": ILB_Y, "HY": HY_Y}).reindex(IDX)
Y.round(4).to_csv(os.path.join(OUT, "sleeve_yields.csv"))
LOG["yield_constants"] = {"EMD_Baa_plus": round(c_emd, 3), "EMD_fund_from": emd_from, "HY_Baa_plus": round(c_hy, 3), "HY_fund_from": hy_from,
                          "EQ_panel_minus_ACWI_2011_20": round(jst.lvl, 3), "EQ_countries": jst.common}
# cross-check: modelled yields vs fund distributions + fee
XC = []
for lab, model, fund in [("Equities : ACWI", EQ_Y, ETF["ACWI"]), ("Equities : VT", EQ_Y, ETF["VT"]), ("Government : 0.42 IEF + 0.58 BWX", GOV_Y, 0.42 * ETF["IEF"] + 0.58 * ETF["BWX"]),
                         ("Investment-grade : LQD", IG_Y, ETF["LQD"]), ("Securitised : MBB", SEC_Y, ETF["MBB"]), ("EM debt : EMB", EMD_Y, ETF["EMB"]), ("Inflation-linked : TIP", ILB_Y, ETF["TIP"]), ("High yield : HYG", HY_Y, ETF["HYG"])]:
    f = fund.dropna(); ov = f.index.intersection(model.dropna().index)
    XC.append({"pair": lab, "from": ov[0].strftime("%Y-%m"), "months": len(ov), "model": model.loc[ov].mean(), "fund": f.loc[ov].mean(), "corr": model.loc[ov].corr(f.loc[ov])})
XC = pd.DataFrame(XC).round(2); XC.to_csv(os.path.join(OUT, "table_crosscheck.csv"), index=False)

# ------------------------------------------------------------------ 3. valuation measures
sh = pd.read_excel(os.path.join(D, "ie_data_2026.xls"), sheet_name="Data", header=None, skiprows=8).iloc[:, [0, 1, 2, 3, 12]]; sh.columns = ["ym", "P", "D", "E", "CAPE"]
sh = sh[pd.to_numeric(sh["ym"], errors="coerce").notna()]; ym = sh["ym"].astype(float); yr = ym.astype(int); mo = ((ym - yr) * 100).round().astype(int)
sh.index = pd.to_datetime(dict(year=yr, month=mo, day=1)) + pd.offsets.MonthEnd(0); sh = sh.apply(pd.to_numeric, errors="coerce")
PE_US = (sh["P"] / sh["E"]).reindex(IDX).ffill(); CAPE_US = sh["CAPE"].reindex(IDX).ffill(); DP_US = (sh["D"] / sh["P"] * 100).reindex(IDX).ffill()
MAT = {"GOV": 10, "IG": 7, "SEC": 6, "EMD": 8, "ILB": 8, "HY": 5}
def par_price_change(y0, y1, Mx):
    """log price change of a par bond (coupon y0, maturity Mx years, semi-annual) when its yield moves from y0 to y1."""
    y0 = y0 / 100; y1 = y1 / 100; n = 2 * Mx; d = 1 + y1 / 2; cpn = 100 * y0 / 2
    p1 = np.where(np.abs(y1) < 1e-9, cpn * n + 100, cpn * (1 - d ** (-n)) / (y1 / 2) + 100 * d ** (-n)); return np.log(p1 / 100)

def decompose(eq_val_series):
    """Per-sleeve monthly log components: cash, valuation, rest; index M."""
    comp = {}
    for s in SL:
        ltr = np.log1p(R[s].reindex(M)); cash = np.log1p(Y[s].shift(1).reindex(M) / 1200)
        if s == "EQ": val = eq_val_series.reindex(M)
        elif s == "GOLD": val = ltr.copy(); cash = pd.Series(0.0, index=M)
        else:
            yy = REAL if s == "ILB" else Y[s]; val = pd.Series(par_price_change(yy.shift(1).reindex(M).values, yy.reindex(M).values, MAT[s]), index=M)
        rest = ltr - cash - val; comp[s] = pd.DataFrame({"ltr": ltr, "cash": cash, "val": val, "rest": rest})
    return comp
EQV = {"world_dp": -np.log(DP_WORLD).diff(), "us_pe": np.log(PE_US).diff(), "us_cape": np.log(CAPE_US).diff()}
COMP = {k: decompose(v) for k, v in EQV.items()}
def wx(s, x, Wv=None):
    """weight x component, treated as zero where the sleeve has no weight (its yield may be undefined before it enters)"""
    Wv = W if Wv is None else Wv; return (Wv[s] * x.reindex(Wv.index)).where(Wv[s] > 0, 0.0)
def gmp_components(comp):
    ltr = np.log1p(r_gmp); cash = sum(wx(s, comp[s]["cash"]) for s in SL); val = sum(wx(s, comp[s]["val"]) for s in SL)
    return pd.DataFrame({"ltr": ltr, "cash": cash, "val": val, "rest": ltr - cash - val,
                         **{f"val_{s}": wx(s, comp[s]["val"]) for s in ["EQ", "GOLD"]}, "val_bonds": sum(wx(s, comp[s]["val"]) for s in ["GOV", "IG", "SEC", "EMD", "ILB", "HY"])})
G = {k: gmp_components(v) for k, v in COMP.items()}; GB = G["world_dp"]
yld = sum(wx(s, Y[s]) for s in SL)                                    # GMP cash distribution yield, % (start-of-month weights)
GB["yield_pct"] = yld; GB.round(7).to_csv(os.path.join(OUT, "gmp_components_monthly.csv"))

# ------------------------------------------------------------------ 4. world hour
wh_idx = pd.read_csv(os.path.join(CN, "world_yardsticks_usd.csv"), index_col=0, parse_dates=True)["gdph"]
wh_q = pd.read_csv(os.path.join(CN, "world_q_yardsticks_usd.csv"), index_col=0, parse_dates=True)["gdph"]
lvl_q = pd.read_csv(os.path.join(CN, "world_q_gdp_per_hour_level_usd.csv"), index_col=0, parse_dates=True).iloc[:, 0]
anchor = float(lvl_q.loc["2014-03-31"]); H = wh_idx / float(wh_idx.loc["2014-01-31":"2014-03-31"].mean()) * anchor
if H.index[-1] < IDX[-1]:
    g = float(wh_q.loc["2026-06-30"] / wh_q.loc["2026-03-31"]) ** (1 / 3); ext = pd.Series([H.iloc[-1] * g ** k for k in range(1, 4)], index=pd.date_range(H.index[-1], periods=4, freq="ME")[1:]); H = pd.concat([H, ext])
H = H.reindex(IDX); dlogH = np.log(H).diff().reindex(M); HARD_END = pd.Timestamp("2025-06-30")
LOG["world_hour"] = {"anchor_2014Q1": round(anchor, 3), "level_1975_12": round(float(H.iloc[0]), 3), "level_2026_06": round(float(H.iloc[-1]), 3), "provisional_from": "2025-07-31"}

# ------------------------------------------------------------------ 5. hours generated per 1,000 hours of capital (Table 3, Fig 1)
PER = [("1976-01", "1981-12", "1976-1981"), ("1982-01", "2000-12", "1982-2000"), ("2001-01", "2021-12", "2001-2021"), ("2022-01", "2026-06", "2022-2026"), ("1976-01", "2026-06", "1976-2026")]
def ann(x): return float(x.mean() * 12 * 100)                         # log, % a year
rows = []
for a, b, lab in PER:
    g = GB.loc[a:b]; h = dlogH.loc[a:b]
    rows.append({"period": lab, "total": ann(g["ltr"]) * 10, "cash": ann(g["cash"]) * 10, "price": ann(g["ltr"] - g["cash"]) * 10, "val_eq": ann(g["val_EQ"]) * 10, "val_bonds": ann(g["val_bonds"]) * 10,
                 "val_gold": ann(g["val_GOLD"]) * 10, "rest": ann(g["rest"]) * 10, "ex_val": ann(g["ltr"] - g["val"]) * 10, "needed": ann(h) * 10})
T3 = pd.DataFrame(rows); T3["net"] = T3["total"] - T3["needed"]; T3["net_ex_val"] = T3["ex_val"] - T3["needed"]; T3 = T3.round(1); T3.to_csv(os.path.join(OUT, "table3_hours_generated.csv"), index=False)
rows = []
for k, lab in [("world_dp", "World dividend-price ratio (baseline)"), ("us_pe", "US trailing P/E"), ("us_cape", "US CAPE")]:
    g = G[k]; e = COMP[k]["EQ"]
    rows.append({"measure": lab, "eq_val_sleeve": ann(e["val"]), "eq_val_gmp": ann(g["val_EQ"]), "all_val": ann(g["val"]), "tr_ex_val": ann(g["ltr"] - g["val"]), "net_ex_val": ann(g["ltr"] - g["val"]) - ann(dlogH)})
T4 = pd.DataFrame(rows).round(2); T4.to_csv(os.path.join(OUT, "table4_valuation_measures.csv"), index=False)
LOG["us_equity"] = {"price_log_pct": round(float(np.log(sh["P"].loc["2026-06-30"] / sh["P"].loc["1976-01-31"]) / 50.42 * 100), 2), "earnings_log_pct": round(float(np.log(sh["E"].loc["2026-06-30"] / sh["E"].loc["1976-01-31"]) / 50.42 * 100), 2),
                    "dividends_log_pct": round(float(np.log(sh["D"].loc["2026-06-30"] / sh["D"].loc["1976-01-31"]) / 50.42 * 100), 2), "pe_1976": round(float(PE_US.loc["1976-01-31"]), 1), "pe_2026": round(float(PE_US.loc["2026-06-30"]), 1)}

# ------------------------------------------------------------------ 6. aggregate values (bn USD, year-end) and flows as % of world GDP (Table 5, Fig 2; Table 9)
sys.path.insert(0, B61); import build_pit_v2 as v2
boj = v2.boj_series(v2.BOJ_SHARE_PRE, v2.BOJ_SHARE_POST); V = v2.b6.V.copy(); rows = {}
for y in V.index:
    gov, cor = float(V.GOVBLK[y]), float(V.CORBLK[y]); d_gov = float(v2.FED_TSY.get(y, 0.0)) + float(v2.ECB.get(y, 0.0)) + float(boj.get(y, 0.0))
    gov = max(gov - d_gov, gov * 0.05); cor = max(cor - float(v2.FED_MBS.get(y, 0.0)), cor * 0.05); s_ilb = v2.ilb_share(y); s_sec = float(v2.SEC_SHARE.get(y, 0.0))
    g_ilb = gov * s_ilb; g_nom = gov - g_ilb; c_sec = cor * s_sec; rest = cor - c_sec; c_ig, c_hy = (rest * 15.1 / 16.8, rest * 1.7 / 16.8) if y >= 1984 else (rest, 0.0)
    rows[y] = dict(EQ=float(V.EQ[y]), GOV=g_nom, IG=c_ig, SEC=c_sec, GOLD=float(V.GOLD[y]), EMD=float(V.EMD[y]), ILB=g_ilb, HY=c_hy)
USD = pd.DataFrame(rows).T[SL]; assert (USD.div(USD.sum(axis=1), axis=0) * 100 - Wp.reindex(USD.index)).abs().max().max() < 1e-6
gdp_w = pd.Series({int(d["date"]): d["value"] for d in json.load(open(os.path.join(CND, "wb_gdp.json")))[1] if d["countryiso3code"] == "WLD" and d["value"]}).sort_index() / 1e9
pop_w = pd.Series({int(d["date"]): d["value"] for d in json.load(open(os.path.join(CND, "wb_pop.json")))[1] if d["countryiso3code"] == "WLD" and d["value"]}).sort_index()
cap_ye = USD.sum(axis=1); cap_avg = (cap_ye + cap_ye.shift(1)) / 2
ann_comp = GB[["ltr", "cash", "val", "rest"]].resample("YE").sum(); ann_comp.index = ann_comp.index.year; ann_h = dlogH.resample("YE").sum(); ann_h.index = ann_h.index.year
FL = pd.DataFrame({"capital_avg_bn": cap_avg, "gdp_bn": gdp_w}).loc[1976:2025]
for c in ["ltr", "cash", "val", "rest"]: FL[c + "_bn"] = ann_comp[c].reindex(FL.index) * FL["capital_avg_bn"]
FL["needed_bn"] = ann_h.reindex(FL.index) * FL["capital_avg_bn"]
for c in ["ltr", "cash", "val", "rest", "needed"]: FL[c + "_pct_gdp"] = FL[c + "_bn"] / FL["gdp_bn"] * 100
FL["price_pct_gdp"] = FL["ltr_pct_gdp"] - FL["cash_pct_gdp"]; FL["net_pct_gdp"] = FL["ltr_pct_gdp"] - FL["needed_pct_gdp"]
g_gdp = np.log(gdp_w / gdp_w.shift(1))                                # growth of world nominal GDP in US dollars (g in Piketty's sense)
FL["needed_gdp_pct_gdp"] = g_gdp.reindex(FL.index) * FL["capital_avg_bn"] / FL["gdp_bn"] * 100; FL["net_gdp_pct_gdp"] = FL["ltr_pct_gdp"] - FL["needed_gdp_pct_gdp"]
LOG["g_vs_hour"] = {"world_gdp_growth_log_pct_1976_2025": round(float(g_gdp.loc[1976:2025].mean() * 100), 2), "hour_growth_log_pct_1976_2025": round(float(ann_h.loc[1976:2025].mean() * 100), 2),
                    "implied_hours_worked_growth_pct": round(float((g_gdp.loc[1976:2025].mean() - ann_h.loc[1976:2025].mean()) * 100), 2)}
FL.round(3).to_csv(os.path.join(OUT, "flows_annual.csv"))
DEC = [(1976, 1980), (1981, 1990), (1991, 2000), (2001, 2010), (2011, 2020), (2021, 2025), (1976, 2025)]
T5 = pd.DataFrame([{"period": f"{a}-{b}", **{k: FL.loc[a:b, k + "_pct_gdp"].mean() for k in ["ltr", "cash", "price", "needed", "net", "val", "needed_gdp", "net_gdp"]}} for a, b in DEC]).round(1); T5.to_csv(os.path.join(OUT, "table5_flows_pct_gdp.csv"), index=False)
Ydec = Y.resample("YE").last(); Ydec.index = Ydec.index.year; Yavg = Y.resample("YE").mean(); Yavg.index = Yavg.index.year
CASH = (USD * Ydec.reindex(USD.index) / 100).where(USD > 0, 0.0)    # cash distributions by sleeve, bn USD (year-end capital x year-end yield)
T9 = pd.DataFrame({"capital_ye_trn": cap_ye / 1000, "capital_avg_trn": cap_avg / 1000, "gdp_trn": gdp_w.reindex(cap_ye.index) / 1000}); T9["cap_gdp_pct"] = T9["capital_ye_trn"] / T9["gdp_trn"] * 100
T9["cash_trn"] = CASH.sum(axis=1) / 1000; T9["cash_gdp_pct"] = T9["cash_trn"] / T9["gdp_trn"] * 100; T9["cash_yield_pct"] = T9["cash_trn"] / T9["capital_ye_trn"] * 100
Hdec = H.resample("YE").last(); Hdec.index = Hdec.index.year; T9["usd_per_hour"] = Hdec.reindex(T9.index); T9["cash_bn_hours"] = T9["cash_trn"] * 1000 / T9["usd_per_hour"]
T9["hours_per_inhabitant"] = T9["cash_bn_hours"] * 1e9 / pop_w.reindex(T9.index)
# hours worked in the 43-country panel (PWT), for the share
def pwt(f):
    x = pd.read_csv(f); x.columns = ["date", "v"]; x["date"] = pd.to_datetime(x["date"]); return pd.to_numeric(x.set_index("date")["v"], errors="coerce")
EMP = {os.path.basename(f)[6:8]: pwt(f) for f in glob.glob(os.path.join(CND, "EMPENG*A148NRUG.csv"))}; AVH = {os.path.basename(f)[6:8]: pwt(f) for f in glob.glob(os.path.join(CND, "AVHWPE*A065NRUG.csv"))}
hrs = pd.DataFrame({c: e * (AVH[c] if c in AVH and AVH[c].notna().any() else pd.Series(2100.0, index=e.index)).reindex(e.index) / 1000 for c, e in EMP.items()}); hrs.index = hrs.index.year
hrs = hrs.interpolate(limit=1, limit_area="inside"); full = hrs.notna().all(axis=1); T9["panel_hours_bn"] = hrs.sum(axis=1).where(full).reindex(T9.index); T9["cash_share_panel_hours_pct"] = T9["cash_bn_hours"] / T9["panel_hours_bn"] * 100
T9.round(3).to_csv(os.path.join(OUT, "table9_aggregate.csv"))
# who pays (Table 8): governments = GOV + ILB; companies interest = IG + HY; households mortgage = SEC; dividends = EQ; EM issuers = EMD
PAY = pd.DataFrame({"Governments": CASH["GOV"] + CASH["ILB"], "Companies: interest": CASH["IG"] + CASH["HY"], "Companies: dividends": CASH["EQ"], "Households: mortgage interest": CASH["SEC"], "Emerging-market issuers": CASH["EMD"]})
T8 = PAY.div(PAY.sum(axis=1), axis=0) * 100; T8.round(1).to_csv(os.path.join(OUT, "table8_payers.csv"))

# ------------------------------------------------------------------ 7. the cash yield: annual averages (Table 6), change decomposition (Table 7), Fig 3
Wa = W.resample("YE").mean(); Wa.index = Wa.index.year; ya = yld.resample("YE").mean(); ya.index = ya.index.year; Yavg = Yavg.fillna(0.0)
T6 = pd.concat([Yavg.loc[1976:2025].T, ya.rename("GMP").to_frame().T]); T6.loc["equity weight, %"] = Wa["EQ"] * 100; T6 = T6.round(2); T6.to_csv(os.path.join(OUT, "table6_yields_annual.csv"))
def bennet(y0, y1):
    w0, w1 = Wa.loc[y0], Wa.loc[y1]; s0, s1 = Yavg.loc[y0], Yavg.loc[y1]; dw = (w1 - w0) * (s0 + s1) / 2; dy = (w0 + w1) / 2 * (s1 - s0)
    return {"change": float(ya.loc[y1] - ya.loc[y0]), "weights": float(dw.sum()), "yields": float(dy.sum()), "largest_yield": f"{NMs[dy.abs().idxmax()]} {dy[dy.abs().idxmax()]:+.2f}", "largest_weight": f"{NMs[dw.abs().idxmax()]} {dw[dw.abs().idxmax()]:+.2f}"}
NMs = {"EQ": "Equities", "GOV": "DM government bonds", "IG": "Investment-grade credit", "SEC": "Securitised", "GOLD": "Gold", "EMD": "EM debt", "ILB": "Inflation-linked", "HY": "High yield"}
T7 = pd.DataFrame({f"{a} -> {b}": bennet(a, b) for a, b in [(1981, 2021), (2021, 2025), (1976, 2025)]}); T7.to_csv(os.path.join(OUT, "table7_yield_change.csv"))
LOG["yield_extremes"] = {"max": [str(yld.idxmax().date()), round(float(yld.max()), 2)], "min": [str(yld.idxmin().date()), round(float(yld.min()), 2)], "first": round(float(yld.iloc[0]), 2), "last": round(float(yld.iloc[-1]), 2),
                         "last_above_5": str(yld[yld > 5].index[-1].date()), "last12m_mean": round(float(yld.iloc[-12:].mean()), 2)}

# ------------------------------------------------------------------ 8. holdings in world hours (Table 10, Fig 4); cash vs total return in hours (Table 12, Fig 5); sleeves (Table 11)
L = np.exp(GB["ltr"].cumsum()); P = np.exp((GB["ltr"] - GB["cash"]).cumsum())          # reinvested / spent (price path), Jan 1976 start = 1
L.loc[IDX[0]] = 1; P.loc[IDX[0]] = 1; L = L.sort_index(); P = P.sort_index()
h0 = float(H.iloc[0]); SCALE = 10000                                                        # holding worth 10,000 hours in January 1976
HO = pd.DataFrame(index=IDX); HO["usd_per_hour"] = H; HO["reinvested_hours"] = L * h0 / H * SCALE; HO["spent_value_hours"] = P * h0 / H * SCALE
dist_usd = (P.shift(1) * yld.reindex(IDX) / 1200).loc[M]                                   # distributions on the spent holding, per 1 USD initial (value at start of month x that month's yield)
HO["dist_12m_hours"] = (dist_usd * h0 * SCALE / H.reindex(M)).rolling(12).sum().reindex(IDX)
HO["dist_12m_usd_idx"] = dist_usd.rolling(12).sum().reindex(IDX); HO["dist_12m_usd_idx"] = HO["dist_12m_usd_idx"] / HO["dist_12m_usd_idx"].loc["1976-12-31"] * 100
HO["dist_12m_real_idx"] = (dist_usd / cpi.reindex(M)).rolling(12).sum().reindex(IDX); HO["dist_12m_real_idx"] = HO["dist_12m_real_idx"] / HO["dist_12m_real_idx"].loc["1976-12-31"] * 100
HO["dist_12m_hours_idx"] = HO["dist_12m_hours"] / HO["dist_12m_hours"].loc["1976-12-31"] * 100
HO.round(4).to_csv(os.path.join(OUT, "holdings_monthly.csv"))
T10 = HO.loc[["1976-12-31", "1981-12-31", "1990-12-31", "2000-12-31", "2008-12-31", "2021-12-31", "2026-06-30"]].round(1); T10.to_csv(os.path.join(OUT, "table10_holdings.csv"))
LOG["holding"] = {"reinvested_x": round(float(HO["reinvested_hours"].iloc[-1] / SCALE), 2), "reinvested_min": [str(HO["reinvested_hours"].idxmin().date()), round(float(HO["reinvested_hours"].min()))],
                  "spent_value_share": round(float(HO["spent_value_hours"].iloc[-1] / SCALE), 2), "dist_usd_pct": round(float(np.log(HO["dist_12m_usd_idx"].iloc[-1] / 100) / 49.5 * 100), 2),
                  "dist_real_pct": round(float(np.log(HO["dist_12m_real_idx"].iloc[-1] / 100) / 49.5 * 100), 2), "dist_hours_pct": round(float(np.log(HO["dist_12m_hours_idx"].iloc[-1] / 100) / 49.5 * 100), 2)}
# Table 12 and rolling windows
def t12(a, b):
    g = GB.loc[a:b]; h = dlogH.loc[a:b]; cy = float(yld.loc[a:b].mean()); pr = ann(g["ltr"] - g["cash"]); tr = ann(g["ltr"]); hg = ann(h); return {"cash_yield": cy, "price_return": pr, "total_return": tr, "hour": hg, "tr_in_hours": tr - hg, "excess_cash": cy - (tr - hg)}
T12 = pd.DataFrame({lab: t12(a, b) for a, b, lab in PER}).round(1); T12.to_csv(os.path.join(OUT, "table12_cash_vs_tr.csv"))
ROLL = {}
for n in (20, 10):
    k = 12 * n; trh = ((GB["ltr"] - dlogH).rolling(k).mean() * 1200).dropna(); cy = yld.rolling(k).mean().reindex(trh.index); ex = cy - trh
    ROLL[n] = {"windows": len(ex), "share_cash_exceeds_pct": round(float((ex > 0).mean() * 100), 1), "median_excess": round(float(ex.median()), 2), "n_short": int((ex <= 0).sum()),
               "short_first": str(ex[ex <= 0].index.min().date()) if (ex <= 0).any() else None, "short_last": str(ex[ex <= 0].index.max().date()) if (ex <= 0).any() else None,
               "tr_hours_min": [str(trh.idxmin().date()), round(float(trh.min()), 2)], "tr_hours_median": round(float(trh.median()), 2)}
    if n == 20: R20 = pd.DataFrame({"cash_yield_20y": cy, "tr_in_hours_20y": trh})
LOG["rolling"] = ROLL; R20.round(3).to_csv(os.path.join(OUT, "rolling20.csv"))
AVAIL = {"EQ": "1976-01", "GOV": "1976-01", "IG": "1976-01", "SEC": "1976-01", "GOLD": "1976-01", "HY": "1984-01", "EMD": "1993-01", "ILB": "1997-02"}
rows = []
for s in SL:
    c = COMP["world_dp"][s].loc[AVAIL[s]:]; h = dlogH.loc[AVAIL[s]:]; inc = float(Y[s].loc[AVAIL[s]:].mean())
    rows.append({"sleeve": NMs[s], "from": AVAIL[s][:4], "income": inc, "price": ann(c["ltr"] - c["cash"]), "valuation": ann(c["val"]), "price_ex_val": ann(c["rest"]), "hour": ann(h), "total_ex_val_minus_hour": ann(c["ltr"] - c["val"]) - ann(h)})
T11 = pd.DataFrame(rows).round(1); T11.to_csv(os.path.join(OUT, "table11_sleeves.csv"), index=False)

# ------------------------------------------------------------------ 9. rent outside the GMP (JST housing rent yield, GDP-weighted in USD)
d = pd.read_excel(os.path.join(D, "JSTdatasetR6.xlsx")); d = d[d.year >= 1970]
ry = d.pivot(index="year", columns="iso", values="housing_rent_yd") * 100; gusd = (d.pivot(index="year", columns="iso", values="gdp") / d.pivot(index="year", columns="iso", values="xrusd"))
wr = gusd[ry.columns].where(ry.notna()); wr = wr.div(wr.sum(axis=1), axis=0); RENT = (ry * wr).sum(axis=1, min_count=1)
LOG["rent"] = {"countries": int(ry.notna().loc[2020].sum()), **{str(y): round(float(RENT.loc[y]), 2) for y in [1976, 2000, 2020]}, **{f"gmp_cash_{y}": round(float(ya.loc[y]), 2) for y in [1976, 2000, 2020]}}

# ------------------------------------------------------------------ 10. robustness (Table 13)
def spent_path_stats(Yv, Wv=W):
    yv = sum(wx(s, Yv[s], Wv) for s in SL); cash = sum(wx(s, np.log1p(Yv[s].shift(1) / 1200), Wv) for s in SL)
    ltr = np.log1p(gmp_r.reindex(Wv.index)); pr = ann(ltr - cash); Pp = np.exp((ltr - cash).cumsum()); Hh = H.reindex(Wv.index)
    dh = (Pp.shift(1).fillna(1.0) * yv / 1200 / Hh).rolling(12).sum(); ratio = float(dh.iloc[-1] / dh.dropna().iloc[0])
    return {"mean": float(yv.mean()), "1981": float(yv.loc["1981"].mean()), "2021": float(yv.loc["2021"].mean()), "last12m": float(yv.iloc[-12:].mean()), "price_return": pr, "dist_hours_end_over_start": ratio}
comp_old = pd.read_csv(os.path.join(B, "output", "sleeve_yields_v1_0.csv"), index_col=0, parse_dates=True)   # v1.0 series (fund-calibrated bonds, Shiller+EFA/EEM equity)
V = {"Baseline": Y}
V["Equities: Shiller US only"] = Y.assign(EQ=DP_US)
V["Equities: Shiller US + EFA/EEM/ACWI fund composite (v1.0)"] = Y.assign(EQ=comp_old["EQ"].reindex(IDX))
V["Government: seven-year trailing mean yield (running coupon)"] = Y.assign(GOV=GOV_Y.rolling(84, min_periods=12).mean())
V["Inflation-linked: real coupon only, no accretion"] = Y.assign(ILB=REAL)
V["EM debt: Baa + 2.0 (the return proxy's yield)"] = Y.assign(EMD=baa + 2.0)
V["All credit sleeves 1 point lower"] = Y.assign(IG=IG_Y - 1, SEC=SEC_Y - 1, EMD=EMD_Y - 1, HY=HY_Y - 1)
V["Bond sleeves at index-fund cash-distribution levels"] = Y.assign(**{s: comp_old[s].reindex(IDX) for s in ["IG", "SEC", "EMD", "ILB", "HY"]})
T13 = pd.DataFrame({k: spent_path_stats(v) for k, v in V.items()}).T
T13.loc["Weights: two-year lag (from 1977)"] = spent_path_stats(Y, W2)
T13 = T13.round(2); T13.to_csv(os.path.join(OUT, "table13_robustness.csv"))

# ------------------------------------------------------------------ 11. figures
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
C = {"cash": "#1f4e79", "rest": "#6b8e6b", "val": "#c98a2b", "need": "k"}
fig, ax = plt.subplots(figsize=(8.4, 4.4)); x = np.arange(len(T3)); wdt = 0.55
for i, r in T3.iterrows():
    val = r["val_eq"] + r["val_bonds"] + r["val_gold"]; ax.bar(i, r["cash"], wdt, color=C["cash"], label="Paid in cash" if i == 0 else None)
    ax.bar(i, r["rest"], wdt, bottom=r["cash"], color=C["rest"], label="Earnings growth and other" if i == 0 else None)
    ax.bar(i, val, wdt, bottom=(r["cash"] + r["rest"]) if val >= 0 else 0, color=C["val"], label="Valuation change" if i == 0 else None)
    ax.plot([i - wdt / 2, i + wdt / 2], [r["needed"]] * 2, color="k", ls="--", lw=1.4, label="Needed to keep pace with the hour" if i == 0 else None)
    ax.plot(i, r["total"], "D", color="k", ms=5, label="Total return" if i == 0 else None); ax.annotate(f"{r['total']:.0f}", (i, r["total"]), xytext=(7, 0), textcoords="offset points", fontsize=8, va="center")
ax.axhline(0, color="grey", lw=0.8); ax.set_xticks(x); ax.set_xticklabels([p if p != "1976-2026" else "Full sample" for p in T3["period"]]); ax.set_ylabel("hours a year"); ax.legend(fontsize=7.5, frameon=False, ncol=2, loc="upper right")
ax.set_title("Figure 1. Hours a year generated by GMP capital worth 1,000 world hours", loc="left", fontsize=9.5); fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig1_hours_generated.png"), dpi=160); plt.close(fig)

fig, ax = plt.subplots(figsize=(8.4, 4.2)); x = np.arange(len(T5)); wdt = 0.27
ax.bar(x - wdt, T5["ltr"], wdt, color="#3b3b8f", label="Total return"); ax.bar(x, T5["cash"], wdt, color="#7f9fbf", label="Cash distributions"); ax.bar(x + wdt, T5["net"], wdt, color="#6b8e6b", label="Net of the growth of the hour")
for i, v in enumerate(T5["ltr"]): ax.annotate(f"{v:.1f}", (i - wdt, v), xytext=(0, 2), textcoords="offset points", ha="center", fontsize=7.5)
ax.axhline(0, color="grey", lw=0.8); ax.set_xticks(x); ax.set_xticklabels([p if p != "1976-2025" else "Full sample" for p in T5["period"]]); ax.set_ylabel("% of world GDP"); ax.set_ylim(None, float(T5["ltr"].max()) * 1.25); ax.legend(fontsize=8, frameon=False, loc="upper left")
ax.set_title("Figure 2. Flows on the whole investable GMP, % of world GDP a year", loc="left", fontsize=9.5); fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig2_flows_gdp.png"), dpi=160); plt.close(fig)

fig, ax = plt.subplots(figsize=(8.4, 4.2)); Ym = Y.reindex(M)
payer = pd.DataFrame({"Governments": wx("GOV", Y["GOV"]) + wx("ILB", Y["ILB"]), "Companies: interest": wx("IG", Y["IG"]) + wx("HY", Y["HY"]), "Households: mortgage interest": wx("SEC", Y["SEC"]), "Emerging-market issuers": wx("EMD", Y["EMD"]), "Companies: dividends": wx("EQ", Y["EQ"])})
ax.stackplot(payer.index, [payer[c] for c in payer.columns], labels=payer.columns, colors=["#7f9fbf", "#c98a2b", "#6b8e6b", "#8c4a3c", "#1f4e79"], lw=0)
ax.plot(yld.index, yld, color="k", lw=1.0); ax.set_ylabel("% a year"); ax.set_xlim(M[0], M[-1]); ax.set_ylim(0, None); ax.legend(fontsize=7.5, frameon=False, loc="upper right")
for t, v in [(yld.idxmax(), yld.max()), (yld.idxmin(), yld.min()), (yld.index[-1], yld.iloc[-1])]: ax.annotate(f"{v:.1f}%", (t, v), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=8)
ax.set_title("Figure 3. Cash distribution yield of the GMP, by payer, 1976-2026", loc="left", fontsize=9.5); fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig3_cash_yield_by_payer.png"), dpi=160); plt.close(fig)

fig, ax = plt.subplots(figsize=(8.4, 4.2)); A = HO.resample("YE").last().loc["1976":"2025"]; A.index = A.index.year
ax.plot(A.index, A["reinvested_hours"] / SCALE * 100, color="#6b8e6b", lw=1.8, label="Distributions reinvested: value, world hours")
ax.plot(A.index, A["dist_12m_usd_idx"], color="#7f9fbf", lw=1.4, label="Distributions spent: distributions, US dollars")
ax.plot(A.index, A["dist_12m_real_idx"], color="#c98a2b", lw=1.4, label="Distributions spent: distributions, US consumer prices")
ax.plot(A.index, A["dist_12m_hours_idx"], color="#1f4e79", lw=1.8, label="Distributions spent: distributions, world hours")
ax.axhline(100, color="grey", lw=0.8); ax.set_yscale("log"); ax.set_yticks([10, 20, 50, 100, 200, 500, 1000]); ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter()); ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
for c, col in [("reinvested_hours", "#6b8e6b"), ("dist_12m_usd_idx", "#7f9fbf"), ("dist_12m_real_idx", "#c98a2b"), ("dist_12m_hours_idx", "#1f4e79")]:
    v = A[c].iloc[-1] / (SCALE / 100 if c == "reinvested_hours" else 1); ax.annotate(f"{v:.0f}", (2025, v), xytext=(4, 0), textcoords="offset points", fontsize=8, color=col, va="center")
ax.set_xlim(1976, 2028); ax.legend(fontsize=7.5, frameon=False, loc="upper left"); ax.set_title("Figure 4. A GMP holding bought in January 1976, December 1976 = 100 (log)", loc="left", fontsize=9.5)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig4_holding.png"), dpi=160); plt.close(fig)

fig, ax = plt.subplots(figsize=(8.4, 4.0)); ax.plot(R20.index, R20["cash_yield_20y"], color="#1f4e79", lw=1.8, label="Cash distribution yield (20-year mean)"); ax.plot(R20.index, R20["tr_in_hours_20y"], color="#c98a2b", lw=1.6, label="Total return in world hours (20-year, log)")
ax.fill_between(R20.index, R20["tr_in_hours_20y"], R20["cash_yield_20y"], where=R20["cash_yield_20y"] > R20["tr_in_hours_20y"], color="#1f4e79", alpha=0.12, lw=0)
ax.axhline(0, color="grey", lw=0.8); ax.set_ylabel("% a year"); ax.set_xlabel("end of 20-year window"); ax.legend(fontsize=8, frameon=False)
ax.set_title("Figure 5. Cash paid out vs total return net of the growth of the hour, rolling 20-year windows", loc="left", fontsize=9.5); fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig5_cash_vs_tr.png"), dpi=160); plt.close(fig)

fig, ax = plt.subplots(figsize=(8.4, 3.8)); ax.plot(jst.res.index, jst.res["dy_jst_panel_annual_interp"], color="#1f4e79", lw=1.6, label="Macrohistory panel, 16 countries, market-cap weighted (annual, interpolated)")
ax.plot(jst.res.index, jst.res["acwi_dist_plus_fee"], color="k", lw=1.0, ls="--", label="iShares MSCI ACWI distributions + fee"); ax.plot(DP_US.index, DP_US, color="#7f9fbf", lw=1.0, label="US (Shiller)")
ax.plot(EQ_Y.index, EQ_Y, color="#c98a2b", lw=1.2, ls=":", label="Series used (panel to 2020, fund from 2021)"); ax.set_ylabel("% a year"); ax.set_ylim(0, None); ax.legend(fontsize=7.5, frameon=False)
ax.set_title("Figure A1. World equity dividend-price ratio: construction without index-vendor data", loc="left", fontsize=9.5); fig.tight_layout(); fig.savefig(os.path.join(OUT, "figA1_equity_dp.png"), dpi=160); plt.close(fig)

# ------------------------------------------------------------------ 12. log and summary
LOG["full_sample"] = {"tr_log_pct": round(ann(GB["ltr"]), 2), "cash_pct": round(ann(GB["cash"]), 2), "val_pct": round(ann(GB["val"]), 2), "rest_pct": round(ann(GB["rest"]), 2), "hour_pct": round(ann(dlogH), 2), "cash_yield_mean": round(float(yld.mean()), 2)}
json.dump(LOG, open(os.path.join(OUT, "build_log.json"), "w"), indent=1, default=str)
pd.set_option("display.width", 220)
print("reproduction:", chk); print("\nT3 hours generated:\n", T3.to_string(index=False)); print("\nT4 valuation measures:\n", T4.to_string(index=False)); print("US equity:", LOG["us_equity"])
print("\nT5 flows % GDP:\n", T5.to_string(index=False)); print("\nT6 yields (selected):\n", T6[[1976, 1981, 1990, 2000, 2007, 2012, 2021, 2025]].to_string()); print("\nT7:\n", T7.to_string())
print("\nT8 payers:\n", T8.loc[[1976, 1981, 1984, 1990, 2000, 2007, 2012, 2021, 2025]].round(0).to_string()); print("\nT9:\n", T9.loc[[1976, 1981, 1984, 1990, 2000, 2007, 2012, 2021, 2023, 2025]].round(2).to_string())
print("\nT10:\n", T10.to_string()); print("holding:", LOG["holding"]); print("\nT11:\n", T11.to_string(index=False)); print("\nT12:\n", T12.to_string()); print("rolling:", json.dumps(ROLL, indent=0))
print("\nrent:", LOG["rent"]); print("\nT13:\n", T13.to_string()); print("\ncrosscheck:\n", XC.to_string(index=False)); print("\ng vs hour:", LOG["g_vs_hour"]); print("\nyield extremes:", LOG["yield_extremes"]); print("constants:", LOG["yield_constants"]); print("full:", LOG["full_sample"]); print("world hour:", LOG["world_hour"])
