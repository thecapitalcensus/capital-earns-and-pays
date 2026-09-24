# -*- coding: utf-8 -*-
"""Fill paper_v2_template.html from output_v2/ (tables and every number quoted in the text) and write
output_v2/paper/income.html (+ img/, style.css) and the site copy ~/CapitalCensus/site/income.html."""
import os, sys, json, shutil, numpy as np, pandas as pd
B = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(B, "output_v2"); P = os.path.join(OUT, "paper"); SITE = os.environ.get("CC_SITE_DIR", os.path.expanduser("~/CapitalCensus/site"))  # site copy is written only if this folder exists
os.makedirs(os.path.join(P, "img"), exist_ok=True); HAS_SITE = os.path.isdir(SITE)
if HAS_SITE: os.makedirs(os.path.join(SITE, "img"), exist_ok=True)
L = json.load(open(os.path.join(OUT, "build_log.json")))
def rd(f, **k): return pd.read_csv(os.path.join(OUT, f), **k)
def table(caption, head, rows, numcols=None, bold=()):
    numcols = set(range(1, len(head))) if numcols is None else numcols
    h = ["<div class=\"scroll\"><table>", f"<caption style=\"text-align:left;caption-side:top;font-size:.93rem;color:var(--muted);padding:.3rem 0\">{caption}</caption>",
         "<thead><tr>" + "".join(f"<th{' style=\"text-align:right\"' if i in numcols else ''}>{c}</th>" for i, c in enumerate(head)) + "</tr></thead><tbody>"]
    for j, r in enumerate(rows):
        h.append(f"<tr{' class=\"bold\"' if j in bold else ''}>" + "".join(f"<td class=\"num\">{c}</td>" if i in numcols else f"<td>{c}</td>" for i, c in enumerate(r)) + "</tr>")
    h.append("</tbody></table></div>"); return "\n".join(h)
f0 = lambda x: f"{x:,.0f}"; f1 = lambda x: f"{x:,.1f}"; f2 = lambda x: f"{x:,.2f}"; sg1 = lambda x: f"{x:+.1f}"; sg2 = lambda x: f"{x:+.2f}"
def mon(s): return pd.Timestamp(s).strftime("%B %Y")
N = {}; T = {}

# ---- tables and numbers
T3 = rd("table3_hours_generated.csv").set_index("period"); T4 = rd("table4_valuation_measures.csv").set_index("measure"); T5 = rd("table5_flows_pct_gdp.csv").set_index("period")
T6 = rd("table6_yields_annual.csv", index_col=0); T6.columns = [int(c) for c in T6.columns]; T7 = rd("table7_yield_change.csv", index_col=0); T8 = rd("table8_payers.csv", index_col=0); T9 = rd("table9_aggregate.csv", index_col=0)
T10 = rd("table10_holdings.csv", index_col=0); T11 = rd("table11_sleeves.csv").set_index("sleeve"); T12 = rd("table12_cash_vs_tr.csv", index_col=0); T13 = rd("table13_robustness.csv", index_col=0); XC = rd("table_crosscheck.csv")
sys.path.insert(0, B); import jst_equity_dy as jst
fs = T3.loc["1976-2026"]
N.update(total_full=f0(fs["total"]), tr_full=f1(fs["total"] / 10), cash_full=f0(fs["cash"]), price_full=f0(fs["price"]), val_full=f0(fs["val_eq"] + fs["val_bonds"] + fs["val_gold"]), exval_full=f0(fs["ex_val"]),
         hour_full=f1(fs["needed"] / 10), needed_full=f0(fs["needed"]), net_full=f0(fs["net"]), netex_full=f0(fs["net_ex_val"]))
nx = T4["net_ex_val"]; N.update(netex_lo=f0(nx.min() * 10), netex_hi=f0(nx.max() * 10), netex_lo_pct=f1(nx.min()), netex_hi_pct=f1(nx.max()), netex_full_pct=f1(nx.min()), net_full_pct=f1(fs["net"] / 10))
t5 = T5.loc["1976-2025"]; N.update(t5_ltr=f1(t5["ltr"]), t5_cash=f1(t5["cash"]), t5_price=f1(t5["price"]), t5_net=f1(t5["net"]), t5_val=f1(t5["val"]), t5_exval=f1(t5["ltr"] - t5["val"]), t5_netex=f1(t5["ltr"] - t5["val"] - t5["needed"]),
                                   t5_80s=f1(T5.loc["1981-1990", "ltr"]), t5_90s=f1(T5.loc["1991-2000", "ltr"]), t5_70s=f1(T5.loc["1976-1980", "ltr"]), t5_20s=f1(T5.loc["2021-2025", "ltr"]), t5_net_20s=f1(T5.loc["2021-2025", "net"]))
oth = T5.loc[["1981-1990", "1991-2000", "2011-2020"], "net"]; N.update(t5_net_lo=f1(oth.min()), t5_net_hi=f1(oth.max()))
gh = L["g_vs_hour"]; N.update(g_gdp=f2(gh["world_gdp_growth_log_pct_1976_2025"]), g_hour_25=f2(gh["hour_growth_log_pct_1976_2025"]), g_hours_worked=f2(gh["implied_hours_worked_growth_pct"]),
         t5_needed_gdp=f1(t5["needed_gdp"]), t5_net_gdp=f1(t5["net_gdp"]), t5_netex_gdp=f1(t5["net_gdp"] - t5["val"]), t5_needed=f1(t5["needed"]))
ye = L["yield_extremes"]; N.update(y_first=f1(ye["first"]), y_max=f1(ye["max"][1]), y_max_date=mon(ye["max"][0]), y_min=f1(ye["min"][1]), y_min_date=mon(ye["min"][0]), y_last=f1(ye["last"]), last_above_5=mon(ye["last_above_5"]), cash_yield_mean=f1(L["full_sample"]["cash_yield_mean"]))
c = T7["1981 -> 2021"]; N.update(dy_8121=f1(-float(c["change"])), dy_8121_y=f1(-float(c["yields"])), dy_8121_w=f1(-float(c["weights"])), gov_8121_abs=f1(-float(c["largest_yield"].split()[-1])))
N.update(dy_7625_w_abs=f1(-float(T7.loc["weights", "1976 -> 2025"])))
ue = L["us_equity"]; N.update(us_div=f1(ue["dividends_log_pct"]), us_earn=f1(ue["earnings_log_pct"]), us_price=f1(ue["price_log_pct"]), us_rerate=f1(ue["price_log_pct"] - ue["earnings_log_pct"]), us_div_gap=f1(ue["earnings_log_pct"] - ue["dividends_log_pct"]), pe_1976=f1(ue["pe_1976"]), pe_2026=f1(ue["pe_2026"]))
eq = T11.loc["Equities"]; N.update(eq_exval=f1(eq["price_ex_val"]), eq_over_hour=f1(eq["total_ex_val_minus_hour"]), eq_income=f1(eq["income"]), gold_net=f1(T11.loc["Gold", "valuation"] - T11.loc["Gold", "hour"]))
bn = T11.loc[["DM government bonds", "Investment-grade credit", "Securitised", "EM debt", "Inflation-linked", "High yield"], "total_ex_val_minus_hour"]; N.update(bond_net_lo=f1(bn.min()), bond_net_hi=f1(bn.max()))
ho = L["holding"]; N.update(dist_hours_end=f0(T10.loc["2026-06-30", "dist_12m_hours_idx"]), reinv_x=f1(ho["reinvested_x"]), reinv_pct=f1(np.log(ho["reinvested_x"]) / 50.42 * 100), reinv_min=f"{ho['reinvested_min'][1]:,}", reinv_min_date=mon(ho["reinvested_min"][0]),
         dist_usd_pct=f1(ho["dist_usd_pct"]), dist_real_pct=f1(-ho["dist_real_pct"]), dist_hours_pct=f1(-ho["dist_hours_pct"]), spent_share=f0(ho["spent_value_share"] * 100))
cov = jst.cov; N.update(jst_cov_1976=f0(cov.loc[1976] * 100), jst_cov_2000=f0(cov.loc[2000] * 100), jst_cov_2020=f0(cov.loc[2020] * 100), jst_gap=sg2(jst.lvl))
yc = L["yield_constants"]; N.update(c_emd=sg2(yc["EMD_Baa_plus"]), c_hy=sg2(yc["HY_Baa_plus"]))
dp = jst.out; N.update(dp_1976=f1(dp.loc["1976-01-31"]), dp_2026=f1(dp.loc["2026-06-30"]))
p1, p2, p3, p4 = T3.loc["1976-1981"], T3.loc["1982-2000"], T3.loc["2001-2021"], T3.loc["2022-2026"]
N.update(exval_7681=f0(p1["ex_val"]), valloss_7681=f0(-(p1["val_eq"] + p1["val_bonds"] + p1["val_gold"])), val_8200=f0(p2["val_eq"] + p2["val_bonds"] + p2["val_gold"]), exval_8200=f0(p2["ex_val"]), hour_8200=f1(p2["needed"] / 10), net_8200=f0(p2["net"]),
         net_0121=f0(p3["net"]), net_2226=f0(p4["net"]), valloss_2226=f0(-p4["val_bonds"]))
N.update(eqv_dp=f1(T4.loc["World dividend-price ratio (baseline)", "eq_val_sleeve"]), eqv_pe=f1(T4.loc["US trailing P/E", "eq_val_sleeve"]), eqv_cape=f1(T4.loc["US CAPE", "eq_val_sleeve"]))
N.update(capgdp_1976=f0(T9.loc[1976, "cap_gdp_pct"]), capgdp_2025=f0(T9.loc[2025, "cap_gdp_pct"]), cap_2025=f0(T9.loc[2025, "capital_ye_trn"]), cashgdp_1981=f1(T9.loc[1981, "cash_gdp_pct"]), cashgdp_2025=f1(T9.loc[2025, "cash_gdp_pct"]),
         cash_hours_2025=f0(T9.loc[2025, "cash_bn_hours"]), hours_pp_2025=f0(T9.loc[2025, "hours_per_inhabitant"]), panel_share_lo=f1(T9["cash_share_panel_hours_pct"].min()), panel_share_hi=f1(T9["cash_share_panel_hours_pct"].max()),
         panel_share_lo_year=str(int(T9["cash_share_panel_hours_pct"].idxmin())), panel_share_hi_year=str(int(T9["cash_share_panel_hours_pct"].idxmax())))
N.update(eqy_1981=f1(T6.loc["EQ", 1981]), eqy_2021=f1(T6.loc["EQ", 2021]))
t12 = T12["1976-2026"]; N.update(excess_full=f1(t12["excess_cash"]), excess_exval=f1(t12["cash_yield"] - (T4.loc["World dividend-price ratio (baseline)", "net_ex_val"])))
r20, r10 = L["rolling"]["20"], L["rolling"]["10"]
N.update(w20_n=f0(r20["windows"]), w20_share=f0(r20["share_cash_exceeds_pct"]), w20_med=f1(r20["median_excess"]), w20_short=f0(r20["n_short"]), w20_short_first=mon(r20["short_first"]), w20_short_last=mon(r20["short_last"]), w20_trmin=f1(r20["tr_hours_min"][1]), w20_trmin_date=mon(r20["tr_hours_min"][0]), w20_trmed=f1(r20["tr_hours_median"]),
         w10_n=f0(r10["windows"]), w10_share=f0(r10["share_cash_exceeds_pct"]), w10_med=f1(r10["median_excess"]), w10_trmin=f1(r10["tr_hours_min"][1]), w10_trmin_date=mon(r10["tr_hours_min"][0]), w10_trmed=f1(r10["tr_hours_median"]))
rt = L["rent"]; N.update(rent_n=f0(rt["countries"]), rent_1976=f1(rt["1976"]), rent_2000=f1(rt["2000"]), rent_2020=f1(rt["2020"]), gmpcash_1976=f1(rt["gmp_cash_1976"]), gmpcash_2000=f1(rt["gmp_cash_2000"]), gmpcash_2020=f1(rt["gmp_cash_2020"]))
lo = T13["mean"].min(); N.update(cash_full_lo=f0(fs["cash"] * lo / T13.loc["Baseline", "mean"]), excess_lo=f1(lo - t12["tr_in_hours"]))

# ---- tables
T["T1"] = table("Table 1. Sleeve yields: construction and sources (author&rsquo;s construction)", ["Sleeve", "Yield", "Source"],
    [["Equities", "Dividend&ndash;price ratio of a sixteen-country panel, weighted by listed market capitalisation, annual to 2020 interpolated to months; from 2021 the ACWI fund&rsquo;s trailing twelve-month distributions plus expense ratio, shifted by the 2011&ndash;2020 panel-minus-fund gap", "Macrohistory Database R6 (eq_dp; Jord&agrave; et al. 2019, CC BY-NC-SA 4.0); World Bank CM.MKT.LCAP.CD; Yahoo Finance"],
     ["DM government bonds", "Ten-year yields of the US, Japan, Germany, the UK, France, Canada and Italy at the sleeve&rsquo;s fixed country weights, renormalised over the countries with data", "FRED (DGS10, OECD IRLTLT01)"],
     ["Investment-grade credit", "Average of Moody&rsquo;s Aaa and Baa yields", "FRED"], ["Securitised", "Half 5-year Treasury, half investment-grade credit (as the return proxy)", "FRED"],
     ["EM debt", f"Baa + constant; constant ({N['c_emd']}) set so the mean equals the fund&rsquo;s distributions plus expense ratio, EMB, 2009&ndash;2026", "FRED; Yahoo Finance"],
     ["High yield", f"Baa + constant; constant ({N['c_hy']}) from HYG on the same basis, 2009&ndash;2026", "FRED; Yahoo Finance"],
     ["Inflation-linked", "Real 10-year yield (TIPS from 2003; before that the return proxy&rsquo;s nominal yield minus trailing ten-year inflation) plus trailing twelve-month US CPI inflation, the principal accretion that inflation-linked bonds accrue as income", "FRED (DFII10, DGS10, CPIAUCSL)"],
     ["Gold", "Zero", "&mdash;"]], numcols=set())
T["T2"] = table("Table 2. Modelled yields vs index-fund cash distributions plus expense ratio, % a year (author&rsquo;s calculations)", ["Sleeve : fund", "From", "Months", "Model", "Fund", "Correlation"],
                [[r["pair"], r["from"], f0(r["months"]), f2(r["model"]), f2(r["fund"]), f2(r["corr"])] for _, r in XC.iterrows()])
cols = ["1976-1981", "1982-2000", "2001-2021", "2022-2026", "1976-2026"]
def t3row(lab, key, sign=1): return [lab] + [f0(sign * T3.loc[c, key]) for c in cols]
rows = [t3row("Total return (a)", "total"), t3row("&mdash; paid in cash", "cash"), t3row("&mdash; price", "price"), t3row("&mdash;&mdash; valuation: world dividend&ndash;price ratio", "val_eq"), t3row("&mdash;&mdash; valuation: bond yields", "val_bonds"),
        t3row("&mdash;&mdash; valuation: gold price", "val_gold"), t3row("&mdash;&mdash; earnings growth and other", "rest"), t3row("Total return excluding valuation (b)", "ex_val"), t3row("Needed to keep pace with the hour (c)", "needed"), t3row("Net gain in hours: (a) &minus; (c)", "net"), t3row("Net gain excluding valuation: (b) &minus; (c)", "net_ex_val")]
T["T3"] = table("Table 3. Hours a year generated by capital worth 1,000 world hours (author&rsquo;s calculations). Equal to the annual log return in percent &times; 10. Periods are calendar years; 2026 runs to June. Components may not add exactly because of rounding", ["", "1976&ndash;1981", "1982&ndash;2000", "2001&ndash;2021", "2022&ndash;2026", "1976&ndash;2026"], rows, bold=(0, 7, 9, 10))
T["T4"] = table("Table 4. Full-sample valuation change under three equity measures, GMP level, % a year (author&rsquo;s calculations)", ["Equity valuation measure", "Equity valuation, sleeve", "Equity valuation, GMP level", "All valuation changes", "Total return excluding valuation", "Net of the hour, excluding valuation"],
                [[i, f2(r["eq_val_sleeve"]), f2(r["eq_val_gmp"]), f2(r["all_val"]), f2(r["tr_ex_val"]), f2(r["net_ex_val"])] for i, r in T4.iterrows()], bold=(0,))
pc = list(T5.index); rows = [["Total return"] + [f1(T5.loc[p, "ltr"]) for p in pc], ["&mdash; cash"] + [f1(T5.loc[p, "cash"]) for p in pc], ["&mdash; price"] + [f1(T5.loc[p, "price"]) for p in pc], ["&mdash;&mdash; of which valuation change"] + [f1(T5.loc[p, "val"]) for p in pc],
                             ["Needed to keep pace with the hour"] + [f1(T5.loc[p, "needed"]) for p in pc], ["Net of the hour"] + [f1(T5.loc[p, "net"]) for p in pc],
                             ["<em>Memo: needed to keep pace with world GDP (g)</em>"] + [f"<em>{f1(T5.loc[p, 'needed_gdp'])}</em>" for p in pc], ["<em>Memo: net of world GDP growth (r &minus; g)</em>"] + [f"<em>{f1(T5.loc[p, 'net_gdp'])}</em>" for p in pc]]
T["T5"] = table("Table 5. Flows on the whole investable GMP, % of world GDP, annual averages (author&rsquo;s calculations)", [""] + [p.replace("-", "&ndash;") for p in pc], rows, bold=(0, 5))
yrs = [1976, 1981, 1990, 2000, 2007, 2012, 2021, 2025]; NM = {"EQ": "Equities", "GOV": "DM government bonds", "IG": "Investment-grade credit", "SEC": "Securitised", "EMD": "EM debt", "ILB": "Inflation-linked", "HY": "High yield", "GOLD": "Gold"}
rows = [[NM[s]] + [("&mdash;" if pd.isna(T6.loc[s, y]) else f1(T6.loc[s, y])) for y in yrs] for s in ["EQ", "GOV", "IG", "SEC", "EMD", "ILB", "HY", "GOLD"]]
rows.append(["<strong>GMP</strong>"] + [f"<strong>{f1(T6.loc['GMP', y])}</strong>" for y in yrs]); rows.append(["<em>Memo: equity weight, %</em>"] + [f"<em>{f0(T6.loc['equity weight, %', y])}</em>" for y in yrs])
T["T6"] = table("Table 6. Sleeve yields and the GMP cash distribution yield, annual averages, % a year (author&rsquo;s calculations)", [""] + [str(y) for y in yrs], rows)
cc = list(T7.columns); rows = [["Change in GMP yield"] + [sg2(float(T7.loc["change", c])) for c in cc], ["of which: weights"] + [sg2(float(T7.loc["weights", c])) for c in cc], ["of which: sleeve yields"] + [sg2(float(T7.loc["yields", c])) for c in cc],
                              ["Largest yield component"] + [T7.loc["largest_yield", c] for c in cc], ["Largest weight component"] + [T7.loc["largest_weight", c] for c in cc]]
T["T7"] = table("Table 7. Change in the GMP&rsquo;s cash distribution yield between annual averages, percentage points (author&rsquo;s calculations)", [""] + [c.replace("->", "&rarr;") for c in cc], rows)
yrs8 = [1976, 1981, 1984, 1990, 2000, 2007, 2012, 2021, 2025]; rows = [[c] + [f0(T8.loc[y, c]) for y in yrs8] for c in ["Governments", "Companies: interest", "Companies: dividends", "Households: mortgage interest", "Emerging-market issuers"]]
T["T8"] = table("Table 8. Cash distributions by payer, % of total (author&rsquo;s calculations)", [""] + [str(y) for y in yrs8], rows)
rows = [["Investable capital, year-end, US$ tn"] + [f1(T9.loc[y, "capital_ye_trn"]) for y in yrs8], ["World GDP, US$ tn"] + [f1(T9.loc[y, "gdp_trn"]) for y in yrs8], ["Capital &divide; GDP, %"] + [f0(T9.loc[y, "cap_gdp_pct"]) for y in yrs8],
        ["Cash distributions, US$ tn"] + [f2(T9.loc[y, "cash_trn"]) for y in yrs8], ["Cash distributions &divide; GDP, %"] + [f1(T9.loc[y, "cash_gdp_pct"]) for y in yrs8], ["Cash distributions, bn world hours"] + [f0(T9.loc[y, "cash_bn_hours"]) for y in yrs8],
        ["&hellip; per inhabitant, hours"] + [f0(T9.loc[y, "hours_per_inhabitant"]) for y in yrs8], ["&hellip; % of hours worked, 43-country panel"] + [("&mdash;" if pd.isna(T9.loc[y, "cash_share_panel_hours_pct"]) else f1(T9.loc[y, "cash_share_panel_hours_pct"])) for y in yrs8]]
T["T9"] = table("Table 9. Cash distributions on the whole investable GMP (author&rsquo;s calculations; capital and cash at year-end; hours worked from the Penn World Table, complete for 2005&ndash;2023)", [""] + [str(y) for y in yrs8], rows, bold=(4,))
d10 = [c for c in T10.index]; lab10 = [pd.Timestamp(c).strftime("%Y-%m") for c in d10]
rows = [["World hour, US$ (chained)"] + [f1(T10.loc[c, "usd_per_hour"]) for c in d10], ["<strong>Distributions reinvested: value, world hours</strong>"] + [f"<strong>{f0(T10.loc[c, 'reinvested_hours'])}</strong>" for c in d10],
        ["Distributions spent: value, world hours"] + [f0(T10.loc[c, "spent_value_hours"]) for c in d10], ["Distributions spent: past 12 months, world hours"] + [f0(T10.loc[c, "dist_12m_hours"]) for c in d10],
        ["Distributions spent: US$, 1976 = 100"] + [f0(T10.loc[c, "dist_12m_usd_idx"]) for c in d10], ["Distributions spent: US consumer prices, 1976 = 100"] + [f0(T10.loc[c, "dist_12m_real_idx"]) for c in d10], ["Distributions spent: world hours, 1976 = 100"] + [f0(T10.loc[c, "dist_12m_hours_idx"]) for c in d10]]
T["T10"] = table("Table 10. A GMP holding worth 10,000 world hours in January 1976 (author&rsquo;s calculations)", [""] + lab10, rows)
rows = [[i, str(int(r["from"])), f1(r["income"]), f1(r["price"]), f1(r["valuation"]), f1(r["price_ex_val"]), f1(r["hour"]), sg1(r["total_ex_val_minus_hour"])] for i, r in T11.iterrows()]
T["T11"] = table("Table 11. Income, price and valuation by sleeve, from the backtest engine&rsquo;s investability date for each sleeve to June 2026, % a year (author&rsquo;s calculations)", ["Sleeve", "From", "Income", "Price", "of which valuation", "Price excluding valuation", "World hour", "Total excluding valuation &minus; hour"], rows)
c12 = list(T12.columns); rows = [["Cash distribution yield (a)"] + [f1(T12.loc["cash_yield", c]) for c in c12], ["Price return, distributions spent"] + [f1(T12.loc["price_return", c]) for c in c12], ["Total return (log)"] + [f1(T12.loc["total_return", c]) for c in c12],
                                 ["Growth of the world hour in US$"] + [f1(T12.loc["hour", c]) for c in c12], ["Total return in world hours (b)"] + [f1(T12.loc["tr_in_hours", c]) for c in c12], ["Cash paid out in excess of (b): (a) &minus; (b)"] + [f1(T12.loc["excess_cash", c]) for c in c12]]
T["T12"] = table("Table 12. The GMP&rsquo;s cash distributions compared with its total return in world hours, % a year (author&rsquo;s calculations)", [""] + [c.replace("-", "&ndash;") for c in c12], rows, bold=(5,))
rows = [[i, f2(r["mean"]), f2(r["1981"]), f2(r["2021"]), f2(r["last12m"]), f2(r["price_return"]), f2(r["dist_hours_end_over_start"])] for i, r in T13.iterrows()]
T["T13"] = table("Table 13. The GMP&rsquo;s cash distribution yield and the spend-everything holding under alternative yield constructions (author&rsquo;s calculations)", ["Variant", "Mean 1976&ndash;2026, %", "1981, %", "2021, %", "Last 12 months, %", "Price return, % a year", "Distributions in hours, end &divide; start"], rows, bold=(0,))
T["T_FILES"] = table("", ["File", "Content"], [["<code>jst_equity_dy.py</code>", "World equity dividend&ndash;price ratio from the Macrohistory panel and the ACWI fund (Table 1, Figure A1)"],
    ["<code>build_v2.py</code>", "Floating weights, yields and the fund cross-check, the three-way decomposition, hours generated, flows as a share of world GDP, payers, holdings, sleeves, rolling windows, rent, robustness, Figures 1&ndash;5"],
    ["<code>build_paper_v2.py</code>", "All tables and every number quoted in the text, generated from <code>output_v2/</code>"], ["<code>output_v2/build_log.json</code>", "Input checksums, reproduction check, constants, rolling-window statistics"],
    ["<code>output_v2/*.csv</code>", "Monthly components, sleeve yields, flows, holdings, tables"]], numcols=set())
T["HASHES"] = "\n".join(f"{v}  {k}" for k, v in L["inputs_sha256"].items())

page = open(os.path.join(B, "paper_v2_template.html"), encoding="utf-8").read()
for k, v in T.items(): page = page.replace("{{" + k + "}}", v)
for k, v in N.items(): page = page.replace("{{n:" + k + "}}", str(v))
left = sorted(set(l[l.index("{{"):l.index("}}") + 2] for l in page.splitlines() if "{{" in l)); assert not left, left
for src, dst in [("fig1_hours_generated.png", "v2_fig1.png"), ("fig2_flows_gdp.png", "v2_fig2.png"), ("fig3_cash_yield_by_payer.png", "v2_fig3.png"), ("fig4_holding.png", "v2_fig4.png"), ("fig5_cash_vs_tr.png", "v2_fig5.png"), ("figA1_equity_dp.png", "v2_figA1.png")]:
    shutil.copy(os.path.join(OUT, src), os.path.join(P, "img", dst))
    if HAS_SITE: shutil.copy(os.path.join(OUT, src), os.path.join(SITE, "img", dst))
if HAS_SITE: shutil.copy(os.path.join(SITE, "style.css"), os.path.join(P, "style.css"))   # otherwise the copy shipped in output_v2/paper/ is used
open(os.path.join(P, "income.html"), "w", encoding="utf-8").write(page)
if HAS_SITE: open(os.path.join(SITE, "income.html"), "w", encoding="utf-8").write(page)
json.dump(N, open(os.path.join(OUT, "numbers_in_text.json"), "w"), indent=1)
print("written", len(page), "bytes;", len(N), "numbers filled")
