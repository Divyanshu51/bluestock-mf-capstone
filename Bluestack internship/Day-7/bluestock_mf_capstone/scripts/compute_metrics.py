"""
compute_metrics.py
------------------
Standalone script to compute all performance and risk metrics
from the cleaned NAV data and save results to reports/.

Metrics computed:
    - Daily returns
    - CAGR (1yr, 3yr)
    - Sharpe Ratio (Rf = 6.5%)
    - Sortino Ratio
    - Alpha and Beta (OLS vs Nifty 100)
    - Maximum Drawdown
    - VaR and CVaR (95% historical)
    - Fund Scorecard (composite 0-100)

Run from project root:
    python scripts/compute_metrics.py

Outputs saved to reports/:
    - fund_scorecard.csv
    - alpha_beta.csv
    - var_cvar_report.csv
"""

import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

ROOT    = Path(__file__).resolve().parent.parent
PROC    = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)

RF_ANNUAL = 0.065
RF_DAILY  = RF_ANNUAL / 252


def load_data():
    """Load the datasets needed for metrics computation."""
    nav   = pd.read_csv(PROC / "02_nav_history_clean.csv")
    nav["date"] = pd.to_datetime(nav["date"])

    bench = pd.read_csv(PROC / "10_benchmark_indices_clean.csv")
    bench["date"] = pd.to_datetime(bench["date"])

    fund  = pd.read_csv(PROC / "01_fund_master_clean.csv")

    # daily returns — use pct_change directly from nav column
    nav = nav.sort_values(["amfi_code", "date"])
    nav["daily_return"] = nav.groupby("amfi_code")["nav"].pct_change()
    returns = nav.dropna(subset=["daily_return"]).copy()

    fund_names   = fund.set_index("amfi_code")["scheme_name"].to_dict()
    expense_map  = fund.set_index("amfi_code")["expense_ratio_pct"].to_dict()

    return nav, returns, bench, fund_names, expense_map


def compute_cagr(nav, fund_names):
    """Compute 1yr and 3yr CAGR for all schemes."""
    end   = nav["date"].max()
    s1    = end - pd.DateOffset(years=1)
    s3    = end - pd.DateOffset(years=3)

    nav_end = nav.groupby("amfi_code").apply(
        lambda g: g.sort_values("date").iloc[-1]["nav"]
    )
    records = []
    for code in nav["amfi_code"].unique():
        ne   = nav_end[code]
        g1   = nav[(nav["amfi_code"]==code) & (nav["date"]<=s1)].sort_values("date")
        g3   = nav[(nav["amfi_code"]==code) & (nav["date"]<=s3)].sort_values("date")
        n1   = g1.iloc[-1]["nav"] if len(g1) > 0 else np.nan
        n3   = g3.iloc[-1]["nav"] if len(g3) > 0 else np.nan
        c1   = round(((ne/n1)**1-1)*100, 2)       if not pd.isna(n1) else np.nan
        c3   = round(((ne/n3)**(1/3)-1)*100, 2)   if not pd.isna(n3) else np.nan
        records.append({"amfi_code": code, "scheme_name": fund_names.get(code, str(code)),
                        "cagr_1yr_pct": c1, "cagr_3yr_pct": c3})

    return pd.DataFrame(records).sort_values("cagr_3yr_pct", ascending=False).reset_index(drop=True)


def compute_sharpe(returns, fund_names):
    """Sharpe = (Rp - Rf) / Std(Rp) * sqrt(252)."""
    records = []
    for code, group in returns.groupby("amfi_code"):
        r         = group["daily_return"]
        ann_mean  = (r.mean() - RF_DAILY) * 252
        ann_std   = r.std() * np.sqrt(252)
        sharpe    = ann_mean / ann_std if ann_std > 0 else np.nan
        records.append({
            "amfi_code": code, "scheme_name": fund_names.get(code, str(code)),
            "ann_return_pct": round(r.mean()*252*100, 2),
            "ann_vol_pct": round(ann_std*100, 2),
            "sharpe_ratio": round(sharpe, 4),
        })
    df = pd.DataFrame(records).sort_values("sharpe_ratio", ascending=False).reset_index(drop=True)
    df["sharpe_rank"] = range(1, len(df)+1)
    return df


def compute_sortino(returns, fund_names):
    """Sortino = (Rp - Rf) / Downside_Std * sqrt(252)."""
    records = []
    for code, group in returns.groupby("amfi_code"):
        r          = group["daily_return"]
        excess_ann = (r.mean() - RF_DAILY) * 252
        neg        = r[r < RF_DAILY] - RF_DAILY
        ds         = neg.std() * np.sqrt(252) if len(neg) > 1 else np.nan
        sortino    = excess_ann / ds if (ds and ds > 0) else np.nan
        records.append({
            "amfi_code": code, "scheme_name": fund_names.get(code, str(code)),
            "sortino_ratio": round(sortino, 4),
        })
    return pd.DataFrame(records).sort_values("sortino_ratio", ascending=False).reset_index(drop=True)


def compute_alpha_beta(returns, bench, fund_names):
    """OLS regression of fund returns on Nifty 100 daily returns."""
    n100 = bench[bench["index_name"]=="NIFTY100"].copy().sort_values("date")
    n100["nifty_return"] = n100["close_value"].pct_change()
    n100 = n100.dropna(subset=["nifty_return"])[["date","nifty_return"]]

    records = []
    for code, group in returns.groupby("amfi_code"):
        merged = group[["date","daily_return"]].merge(n100, on="date", how="inner")
        if len(merged) < 30:
            continue
        slope, intercept, r_val, p_val, _ = stats.linregress(
            merged["nifty_return"], merged["daily_return"]
        )
        records.append({
            "amfi_code":   code,
            "scheme_name": fund_names.get(code, str(code)),
            "alpha_ann":   round(intercept * 252 * 100, 4),
            "beta":        round(slope, 4),
            "r_squared":   round(r_val**2, 4),
            "p_value":     round(p_val, 4),
            "n_obs":       len(merged),
        })
    df = pd.DataFrame(records).sort_values("alpha_ann", ascending=False).reset_index(drop=True)
    df["alpha_rank"] = range(1, len(df)+1)
    return df


def compute_max_drawdown(nav, fund_names):
    """Max Drawdown = min(NAV / running_max - 1)."""
    records = []
    for code, group in nav.groupby("amfi_code"):
        g = group.sort_values("date").copy()
        g["running_max"] = g["nav"].cummax()
        g["drawdown"]    = g["nav"] / g["running_max"] - 1
        max_dd   = g["drawdown"].min()
        dd_end   = g.loc[g["drawdown"].idxmin(), "date"]
        peak_idx = g.loc[:g["drawdown"].idxmin(), "nav"].idxmax()
        dd_start = g.loc[peak_idx, "date"]
        records.append({
            "amfi_code": code, "scheme_name": fund_names.get(code, str(code)),
            "max_drawdown_pct": round(max_dd*100, 2),
            "dd_start": dd_start.date(), "dd_end": dd_end.date(),
        })
    df = pd.DataFrame(records).sort_values("max_drawdown_pct").reset_index(drop=True)
    df["dd_rank"] = range(1, len(df)+1)
    return df


def compute_var_cvar(returns, fund_names):
    """Historical VaR and CVaR at 95% confidence."""
    records = []
    for code, group in returns.groupby("amfi_code"):
        r = group["daily_return"].dropna()
        if len(r) < 50:
            continue
        var_95  = np.percentile(r, 5)
        cvar_95 = r[r <= var_95].mean()
        records.append({
            "amfi_code":      code,
            "scheme_name":    fund_names.get(code, str(code)),
            "var_95_pct":     round(var_95*100, 4),
            "cvar_95_pct":    round(cvar_95*100, 4),
            "ann_return_pct": round(r.mean()*252*100, 2),
            "n_days":         len(r),
        })
    return pd.DataFrame(records).sort_values("var_95_pct").reset_index(drop=True)


def compute_scorecard(cagr_df, sharpe_df, ab_df, dd_df, expense_map):
    """Composite scorecard: 30% CAGR + 25% Sharpe + 20% Alpha + 15% Expense + 10% DD."""
    sc = cagr_df[["amfi_code","scheme_name","cagr_3yr_pct"]].copy()
    sc = sc.merge(sharpe_df[["amfi_code","sharpe_ratio"]], on="amfi_code", how="left")
    sc = sc.merge(ab_df[["amfi_code","alpha_ann"]],        on="amfi_code", how="left")
    sc = sc.merge(dd_df[["amfi_code","max_drawdown_pct"]], on="amfi_code", how="left")
    sc["expense_ratio_pct"] = sc["amfi_code"].map(expense_map)
    n  = len(sc)

    def r2s(col, asc):
        rank = sc[col].rank(ascending=asc)
        return ((n - rank) / (n - 1) * 100).round(2)

    sc["composite_score"] = (
        0.30 * r2s("cagr_3yr_pct",     False) +
        0.25 * r2s("sharpe_ratio",     False) +
        0.20 * r2s("alpha_ann",        False) +
        0.15 * r2s("expense_ratio_pct",True ) +
        0.10 * r2s("max_drawdown_pct", False)
    ).round(2)

    sc = sc.sort_values("composite_score", ascending=False).reset_index(drop=True)
    sc.index = sc.index + 1
    return sc


def main():
    print("\nBluestock Fintech — Compute Metrics")
    print("Computing all performance and risk metrics...\n")

    nav, returns, bench, fund_names, expense_map = load_data()
    print(f"Data loaded: {len(returns):,} return observations | {returns['amfi_code'].nunique()} schemes")

    cagr_df   = compute_cagr(nav, fund_names)
    print(f"CAGR computed for {len(cagr_df)} schemes")

    sharpe_df = compute_sharpe(returns, fund_names)
    print(f"Sharpe computed  | range: {sharpe_df['sharpe_ratio'].min():.3f} to {sharpe_df['sharpe_ratio'].max():.3f}")

    sortino_df = compute_sortino(returns, fund_names)
    print(f"Sortino computed | range: {sortino_df['sortino_ratio'].min():.3f} to {sortino_df['sortino_ratio'].max():.3f}")

    ab_df     = compute_alpha_beta(returns, bench, fund_names)
    print(f"Alpha/Beta computed for {len(ab_df)} schemes")

    dd_df     = compute_max_drawdown(nav, fund_names)
    print(f"Drawdown computed | worst: {dd_df.iloc[0]['max_drawdown_pct']}%")

    var_df    = compute_var_cvar(returns, fund_names)
    print(f"VaR/CVaR computed | worst VaR: {var_df.iloc[0]['var_95_pct']}%")

    scorecard = compute_scorecard(cagr_df, sharpe_df, ab_df, dd_df, expense_map)
    print(f"Scorecard built   | top fund: {scorecard.iloc[0]['scheme_name'][:45]}")

    # save outputs
    out_cols = ["amfi_code","scheme_name","cagr_1yr_pct","cagr_3yr_pct",
                "sharpe_ratio","alpha_ann","max_drawdown_pct",
                "expense_ratio_pct","composite_score"]
    scorecard[out_cols].to_csv(REPORTS / "fund_scorecard.csv", index=True, index_label="rank")
    ab_df.to_csv(REPORTS / "alpha_beta.csv", index=False)
    var_df.to_csv(REPORTS / "var_cvar_report.csv", index=False)

    print(f"\nOutputs saved to {REPORTS}:")
    print("  fund_scorecard.csv")
    print("  alpha_beta.csv")
    print("  var_cvar_report.csv")


if __name__ == "__main__":
    main()
