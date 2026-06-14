"""
Day 3 – EDA Chart Generation
Bluestock Capstone Project I – Mutual Fund Analytics
Generates all 15+ charts as PNGs for embedding into the notebook
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings, os

warnings.filterwarnings("ignore")

PROCESSED = "/home/claude/bluestock_mf/data/processed"
CHARTS    = "/home/claude/bluestock_mf/Day-3/charts"
os.makedirs(CHARTS, exist_ok=True)

# ── colour palette ──────────────────────────────────────────────
BLUE   = "#1f77b4"
ORANGE = "#ff7f0e"
GREEN  = "#2ca02c"
RED    = "#d62728"
PURPLE = "#9467bd"
TEAL   = "#17becf"
PALETTE = [BLUE, ORANGE, GREEN, RED, PURPLE, TEAL,
           "#8c564b","#e377c2","#7f7f7f","#bcbd22"]

sns.set_theme(style="whitegrid", palette=PALETTE)
plt.rcParams.update({"figure.dpi": 150, "font.family": "DejaVu Sans"})

# ── load data ───────────────────────────────────────────────────
print("Loading data …")
nav   = pd.read_csv(f"{PROCESSED}/02_nav_history_clean.csv",
                    parse_dates=["date"])
aum   = pd.read_csv(f"{PROCESSED}/03_aum_by_fund_house_clean.csv",
                    parse_dates=["date"])
sip   = pd.read_csv(f"{PROCESSED}/04_monthly_sip_inflows_clean.csv",
                    parse_dates=["month"])
cat   = pd.read_csv(f"{PROCESSED}/05_category_inflows_clean.csv",
                    parse_dates=["month"])
folio = pd.read_csv(f"{PROCESSED}/06_industry_folio_count_clean.csv",
                    parse_dates=["month"])
perf  = pd.read_csv(f"{PROCESSED}/07_scheme_performance_clean.csv")
txn   = pd.read_csv(f"{PROCESSED}/08_investor_transactions_clean.csv",
                    parse_dates=["transaction_date"])
ph    = pd.read_csv(f"{PROCESSED}/09_portfolio_holdings_clean.csv")
fm    = pd.read_csv(f"{PROCESSED}/01_fund_master_clean.csv")

print("  All files loaded ✓")

# ═══════════════════════════════════════════════════════════════
# CHART 1 – NAV Trend for all 40 schemes (Plotly → PNG)
# ═══════════════════════════════════════════════════════════════
print("Chart 1 – NAV trend …")

nav_merged = nav.merge(fm[["amfi_code","scheme_name","category"]], on="amfi_code", how="left")
# Normalise to 100 at start for comparability
nav_norm = nav_merged.copy()
base = nav_norm.groupby("amfi_code")["nav"].transform("first")
nav_norm["nav_idx"] = nav_norm["nav"] / base * 100

fig, ax = plt.subplots(figsize=(14, 6))
for code, grp in nav_norm.groupby("amfi_code"):
    ax.plot(grp["date"], grp["nav_idx"], lw=0.6, alpha=0.45, color=BLUE)

# Highlight bull run 2023 and correction 2024
ax.axvspan(pd.Timestamp("2023-01-01"), pd.Timestamp("2023-12-31"),
           alpha=0.12, color=GREEN, label="2023 Bull Run")
ax.axvspan(pd.Timestamp("2024-03-01"), pd.Timestamp("2024-06-30"),
           alpha=0.12, color=RED, label="2024 Correction")

ax.set_title("NAV Trend – All 40 Schemes (Indexed to 100 at Jan 2022)", fontsize=14, fontweight="bold")
ax.set_xlabel("Date")
ax.set_ylabel("NAV Index (Base = 100)")
ax.legend(loc="upper left", fontsize=9)
plt.tight_layout()
plt.savefig(f"{CHARTS}/chart01_nav_trend.png", dpi=150)
plt.close()
print("  ✓ chart01_nav_trend.png")

# ═══════════════════════════════════════════════════════════════
# CHART 2 – AUM grouped bar by fund house per year (Seaborn)
# ═══════════════════════════════════════════════════════════════
print("Chart 2 – AUM bar chart …")

aum["year"] = aum["date"].dt.year
aum_yr = aum.groupby(["year","fund_house"])["aum_crore"].mean().reset_index()
aum_yr["aum_lakh_cr"] = aum_yr["aum_crore"] / 1e5

fig, ax = plt.subplots(figsize=(14, 6))
sns.barplot(data=aum_yr, x="fund_house", y="aum_lakh_cr", hue="year",
            palette="Blues_d", ax=ax)

# Highlight SBI bars
for bar in ax.patches:
    if bar.get_height() > 10:          # SBI is the largest
        bar.set_edgecolor(RED)
        bar.set_linewidth(2)

ax.set_title("AUM Growth by Fund House (2022–2025)", fontsize=14, fontweight="bold")
ax.set_xlabel("Fund House")
ax.set_ylabel("Average AUM (₹ Lakh Crore)")
ax.tick_params(axis="x", rotation=30)
ax.annotate("SBI dominates\n₹12.5L Cr", xy=(0, 12.5),
            xytext=(1.2, 13.5),
            arrowprops=dict(arrowstyle="->", color=RED),
            color=RED, fontsize=9, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{CHARTS}/chart02_aum_bar.png", dpi=150)
plt.close()
print("  ✓ chart02_aum_bar.png")

# ═══════════════════════════════════════════════════════════════
# CHART 3 – SIP inflow time-series (Plotly → PNG via kaleido)
# ═══════════════════════════════════════════════════════════════
print("Chart 3 – SIP time-series …")

fig, ax = plt.subplots(figsize=(13, 5))
ax.plot(sip["month"], sip["sip_inflow_crore"], color=BLUE, lw=2, marker="o",
        markersize=4, label="Monthly SIP Inflow")
ax.fill_between(sip["month"], sip["sip_inflow_crore"], alpha=0.15, color=BLUE)

# ATH annotation
ath_row = sip.loc[sip["sip_inflow_crore"].idxmax()]
ax.annotate(f"ATH ₹{int(ath_row['sip_inflow_crore']):,} Cr\n(Dec 2025)",
            xy=(ath_row["month"], ath_row["sip_inflow_crore"]),
            xytext=(ath_row["month"] - pd.DateOffset(months=8),
                    ath_row["sip_inflow_crore"] - 3000),
            arrowprops=dict(arrowstyle="->", color=RED),
            color=RED, fontsize=10, fontweight="bold")

ax.set_title("Monthly SIP Inflows – Jan 2022 to Dec 2025", fontsize=14, fontweight="bold")
ax.set_xlabel("Month")
ax.set_ylabel("SIP Inflow (₹ Crore)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"₹{int(x):,}"))
plt.tight_layout()
plt.savefig(f"{CHARTS}/chart03_sip_timeseries.png", dpi=150)
plt.close()
print("  ✓ chart03_sip_timeseries.png")

# ═══════════════════════════════════════════════════════════════
# CHART 4 – Category inflow heatmap (Seaborn)
# ═══════════════════════════════════════════════════════════════
print("Chart 4 – Category inflow heatmap …")

cat["yr_mo"] = cat["month"].dt.strftime("%Y-%m")
pivot = cat.pivot_table(index="category", columns="yr_mo",
                        values="net_inflow_crore", aggfunc="sum")

fig, ax = plt.subplots(figsize=(16, 5))
sns.heatmap(pivot, cmap="RdYlGn", center=0, linewidths=0.3,
            fmt=".0f", ax=ax,
            cbar_kws={"label": "Net Inflow (₹ Crore)"})
ax.set_title("Category-wise Net Inflows Heatmap (Month × Category)", fontsize=14, fontweight="bold")
ax.set_xlabel("Month")
ax.set_ylabel("Fund Category")
ax.tick_params(axis="x", rotation=60, labelsize=7)
plt.tight_layout()
plt.savefig(f"{CHARTS}/chart04_category_heatmap.png", dpi=150)
plt.close()
print("  ✓ chart04_category_heatmap.png")

# ═══════════════════════════════════════════════════════════════
# CHART 5a – Age group distribution pie
# ═══════════════════════════════════════════════════════════════
print("Chart 5 – Investor demographics …")

age_counts = txn["age_group"].value_counts()
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

axes[0].pie(age_counts.values, labels=age_counts.index,
            autopct="%1.1f%%", colors=PALETTE[:len(age_counts)],
            startangle=90, pctdistance=0.8)
axes[0].set_title("Age Group Distribution", fontweight="bold")

# CHART 5b – SIP amount box plot by age group
sip_txn = txn[txn["transaction_type"] == "SIP"]
age_order = sorted(txn["age_group"].dropna().unique())
sns.boxplot(data=sip_txn, x="age_group", y="amount_inr",
            order=age_order, palette="Set2", ax=axes[1])
axes[1].set_title("SIP Amount by Age Group", fontweight="bold")
axes[1].set_xlabel("Age Group")
axes[1].set_ylabel("Amount (₹)")
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"₹{int(x):,}"))
axes[1].tick_params(axis="x", rotation=20)

# CHART 5c – Gender split
gender_counts = txn["gender"].value_counts()
axes[2].pie(gender_counts.values, labels=gender_counts.index,
            autopct="%1.1f%%", colors=[BLUE, ORANGE, GREEN][:len(gender_counts)],
            startangle=90)
axes[2].set_title("Gender Split", fontweight="bold")

plt.suptitle("Investor Demographics Analysis", fontsize=15, fontweight="bold", y=1.02)
plt.tight_layout()
plt.savefig(f"{CHARTS}/chart05_demographics.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✓ chart05_demographics.png")

# ═══════════════════════════════════════════════════════════════
# CHART 6a – SIP amount by state (horizontal bar)
# ═══════════════════════════════════════════════════════════════
print("Chart 6 – Geographic distribution …")

state_sip = (txn[txn["transaction_type"] == "SIP"]
             .groupby("state")["amount_inr"].sum()
             .sort_values(ascending=True)
             .tail(15) / 1e7)   # crore

fig, axes = plt.subplots(1, 2, figsize=(15, 6))

state_sip.plot(kind="barh", ax=axes[0], color=BLUE, edgecolor="white")
axes[0].set_title("Top 15 States by SIP Amount", fontweight="bold")
axes[0].set_xlabel("Total SIP Amount (₹ Crore)")
axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"₹{x:.0f}Cr"))

# CHART 6b – T30 vs B30
tier_counts = txn["city_tier"].value_counts()
axes[1].pie(tier_counts.values, labels=tier_counts.index,
            autopct="%1.1f%%", colors=[BLUE, ORANGE, GREEN][:len(tier_counts)],
            startangle=90)
axes[1].set_title("T30 vs B30 City Tier Distribution", fontweight="bold")

plt.tight_layout()
plt.savefig(f"{CHARTS}/chart06_geographic.png", dpi=150)
plt.close()
print("  ✓ chart06_geographic.png")

# ═══════════════════════════════════════════════════════════════
# CHART 7 – Folio count growth with milestones
# ═══════════════════════════════════════════════════════════════
print("Chart 7 – Folio count growth …")

fig, ax = plt.subplots(figsize=(13, 5))
ax.plot(folio["month"], folio["total_folios_crore"],
        color=PURPLE, lw=2.5, marker="o", markersize=6)
ax.fill_between(folio["month"], folio["total_folios_crore"], alpha=0.15, color=PURPLE)

milestones = {
    "13.26 Cr\nJan 2022": (folio["month"].iloc[0],  folio["total_folios_crore"].iloc[0]),
    "20 Cr\nMilestone":   (folio.loc[(folio["total_folios_crore"] - 20).abs().idxmin(), "month"],  20),
    "26.12 Cr\nDec 2025": (folio["month"].iloc[-1], folio["total_folios_crore"].iloc[-1]),
}
for label, (x, y) in milestones.items():
    ax.annotate(label, xy=(x, y), xytext=(x, y + 0.8),
                ha="center", fontsize=8, color=PURPLE, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=PURPLE))

ax.set_title("Industry Folio Count Growth (Jan 2022 – Dec 2025)", fontsize=14, fontweight="bold")
ax.set_xlabel("Month")
ax.set_ylabel("Total Folios (Crore)")
plt.tight_layout()
plt.savefig(f"{CHARTS}/chart07_folio_growth.png", dpi=150)
plt.close()
print("  ✓ chart07_folio_growth.png")

# ═══════════════════════════════════════════════════════════════
# CHART 8 – NAV return correlation matrix (Seaborn)
# ═══════════════════════════════════════════════════════════════
print("Chart 8 – NAV return correlation …")

top10 = fm.head(10)[["amfi_code","scheme_name"]].copy()
nav_top = nav[nav["amfi_code"].isin(top10["amfi_code"])].copy()
nav_top["date"] = pd.to_datetime(nav_top["date"])
pivot_nav = nav_top.pivot_table(index="date", columns="amfi_code", values="nav")
returns   = pivot_nav.pct_change().dropna()
returns.columns = [top10.loc[top10["amfi_code"] == c, "scheme_name"].values[0].split("–")[0].strip()[:25]
                   for c in returns.columns]
corr = returns.corr()

fig, ax = plt.subplots(figsize=(11, 8))
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, mask=mask, annot=True, fmt=".2f",
            cmap="coolwarm", center=0, linewidths=0.5,
            ax=ax, cbar_kws={"label": "Pearson Correlation"})
ax.set_title("Pairwise NAV Return Correlation – 10 Selected Funds", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{CHARTS}/chart08_corr_matrix.png", dpi=150)
plt.close()
print("  ✓ chart08_corr_matrix.png")

# ═══════════════════════════════════════════════════════════════
# CHART 9 – Sector allocation donut
# ═══════════════════════════════════════════════════════════════
print("Chart 9 – Sector donut …")

equity_codes = fm[fm["category"] == "Equity"]["amfi_code"].tolist()
eq_ph = ph[ph["amfi_code"].isin(equity_codes)]
sector_wt = eq_ph.groupby("sector")["weight_pct"].sum().sort_values(ascending=False)

fig, ax = plt.subplots(figsize=(10, 8))
wedges, texts, autotexts = ax.pie(
    sector_wt.values,
    labels=sector_wt.index,
    autopct=lambda p: f"{p:.1f}%" if p > 3 else "",
    colors=PALETTE[:len(sector_wt)],
    startangle=90,
    pctdistance=0.82,
    wedgeprops=dict(width=0.55, edgecolor="white", linewidth=1.5)
)
for at in autotexts:
    at.set_fontsize(8)
ax.set_title("Sector Allocation – Aggregate Equity Fund Holdings", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig(f"{CHARTS}/chart09_sector_donut.png", dpi=150)
plt.close()
print("  ✓ chart09_sector_donut.png")

# ═══════════════════════════════════════════════════════════════
# CHART 10 – Risk vs Return scatter
# ═══════════════════════════════════════════════════════════════
print("Chart 10 – Risk vs Return …")

fig, ax = plt.subplots(figsize=(10, 6))
for cat_name, grp in perf.groupby("category"):
    ax.scatter(grp["std_dev_ann_pct"], grp["return_3yr_pct"],
               label=cat_name, s=80, alpha=0.8)
    for _, row in grp.iterrows():
        ax.annotate(row["scheme_name"].split("-")[0].strip()[:18],
                    (row["std_dev_ann_pct"], row["return_3yr_pct"]),
                    fontsize=6, alpha=0.7)

ax.axhline(perf["return_3yr_pct"].mean(), color="gray", ls="--", lw=1, label="Avg Return")
ax.set_title("Risk vs Return (3-Year CAGR vs Std Dev)", fontsize=13, fontweight="bold")
ax.set_xlabel("Annualised Std Dev (%)")
ax.set_ylabel("3-Year CAGR (%)")
ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig(f"{CHARTS}/chart10_risk_return.png", dpi=150)
plt.close()
print("  ✓ chart10_risk_return.png")

# ═══════════════════════════════════════════════════════════════
# CHART 11 – Sharpe ratio bar chart
# ═══════════════════════════════════════════════════════════════
print("Chart 11 – Sharpe ratio …")

perf_sorted = perf.sort_values("sharpe_ratio", ascending=True)
colors_sr = [GREEN if x >= 1 else ORANGE if x >= 0.7 else RED
             for x in perf_sorted["sharpe_ratio"]]

fig, ax = plt.subplots(figsize=(12, 7))
ax.barh(perf_sorted["scheme_name"].str.split("-").str[0].str.strip(),
        perf_sorted["sharpe_ratio"], color=colors_sr, edgecolor="white")
ax.axvline(1.0, color=GREEN, ls="--", lw=1.5, label="Sharpe ≥ 1 (Excellent)")
ax.axvline(0.7, color=ORANGE, ls="--", lw=1.5, label="Sharpe ≥ 0.7 (Good)")
ax.set_title("Sharpe Ratio by Fund Scheme", fontsize=13, fontweight="bold")
ax.set_xlabel("Sharpe Ratio")
ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig(f"{CHARTS}/chart11_sharpe_ratio.png", dpi=150)
plt.close()
print("  ✓ chart11_sharpe_ratio.png")

# ═══════════════════════════════════════════════════════════════
# CHART 12 – Transaction type distribution
# ═══════════════════════════════════════════════════════════════
print("Chart 12 – Transaction type …")

txn_type = txn.groupby("transaction_type")["amount_inr"].sum().sort_values(ascending=False) / 1e7
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

txn_type.plot(kind="bar", ax=axes[0], color=PALETTE[:len(txn_type)], edgecolor="white")
axes[0].set_title("Transaction Volume by Type (₹ Crore)", fontweight="bold")
axes[0].set_xlabel("Transaction Type")
axes[0].set_ylabel("Total Amount (₹ Crore)")
axes[0].tick_params(axis="x", rotation=20)

txn_cnt = txn["transaction_type"].value_counts()
axes[1].pie(txn_cnt.values, labels=txn_cnt.index,
            autopct="%1.1f%%", colors=PALETTE[:len(txn_cnt)], startangle=90)
axes[1].set_title("Transaction Count Share by Type", fontweight="bold")

plt.tight_layout()
plt.savefig(f"{CHARTS}/chart12_txn_type.png", dpi=150)
plt.close()
print("  ✓ chart12_txn_type.png")

# ═══════════════════════════════════════════════════════════════
# CHART 13 – Monthly transaction heatmap (state × month)
# ═══════════════════════════════════════════════════════════════
print("Chart 13 – State × month heatmap …")

txn["yr_mo"] = txn["transaction_date"].dt.strftime("%Y-%m")
top_states = txn.groupby("state")["amount_inr"].sum().nlargest(12).index
state_mo = (txn[txn["state"].isin(top_states)]
            .groupby(["state","yr_mo"])["amount_inr"].sum()
            .unstack(fill_value=0) / 1e5)   # lakh

fig, ax = plt.subplots(figsize=(16, 6))
sns.heatmap(state_mo, cmap="YlOrRd", linewidths=0.2, ax=ax,
            cbar_kws={"label": "Amount (₹ Lakh)"})
ax.set_title("State × Month Transaction Heatmap (Top 12 States)", fontsize=13, fontweight="bold")
ax.tick_params(axis="x", rotation=60, labelsize=7)
plt.tight_layout()
plt.savefig(f"{CHARTS}/chart13_state_month_heatmap.png", dpi=150)
plt.close()
print("  ✓ chart13_state_month_heatmap.png")

# ═══════════════════════════════════════════════════════════════
# CHART 14 – AUM vs Expense ratio scatter
# ═══════════════════════════════════════════════════════════════
print("Chart 14 – AUM vs Expense ratio …")

fig, ax = plt.subplots(figsize=(10, 6))
for cat_name, grp in perf.groupby("category"):
    ax.scatter(grp["expense_ratio_pct"], grp["return_1yr_pct"],
               label=cat_name, s=100, alpha=0.8)

ax.set_title("Expense Ratio vs 1-Year Return by Category", fontsize=13, fontweight="bold")
ax.set_xlabel("Expense Ratio (%)")
ax.set_ylabel("1-Year Return (%)")
ax.legend(fontsize=9)
plt.tight_layout()
plt.savefig(f"{CHARTS}/chart14_expense_vs_return.png", dpi=150)
plt.close()
print("  ✓ chart14_expense_vs_return.png")

# ═══════════════════════════════════════════════════════════════
# CHART 15 – SIP YoY growth bar
# ═══════════════════════════════════════════════════════════════
print("Chart 15 – SIP YoY growth …")

sip["year"] = sip["month"].dt.year
sip_yr = sip.groupby("year")["sip_inflow_crore"].sum().reset_index()
sip_yr["yoy_pct"] = sip_yr["sip_inflow_crore"].pct_change() * 100

fig, ax1 = plt.subplots(figsize=(10, 5))
ax2 = ax1.twinx()

bars = ax1.bar(sip_yr["year"], sip_yr["sip_inflow_crore"] / 1e3,
               color=BLUE, alpha=0.75, label="Annual SIP (₹ '000 Cr)")
ax2.plot(sip_yr["year"].iloc[1:], sip_yr["yoy_pct"].iloc[1:],
         color=RED, marker="D", lw=2, label="YoY Growth %")

ax1.set_title("Annual SIP Inflow and YoY Growth Rate", fontsize=13, fontweight="bold")
ax1.set_xlabel("Year")
ax1.set_ylabel("Total SIP Inflow (₹ '000 Crore)", color=BLUE)
ax2.set_ylabel("YoY Growth (%)", color=RED)

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=9)
plt.tight_layout()
plt.savefig(f"{CHARTS}/chart15_sip_yoy.png", dpi=150)
plt.close()
print("  ✓ chart15_sip_yoy.png")

print("\n✅  All 15 charts saved to", CHARTS)
