"""
recommender.py
--------------
Day 6 task: Simple fund recommender based on investor risk appetite.

Input  : risk appetite string — Low / Moderate / Moderately High / High / Very High
Output : top 3 funds by Sharpe ratio within that risk grade

Run from project root:
    python scripts/recommender.py
"""

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"


# valid risk grades in our dataset
VALID_RISK_GRADES = ["Low", "Moderate", "Moderately High", "High", "Very High"]


def load_performance_data():
    """Load scheme performance data with risk grades."""
    path = PROC / "07_scheme_performance_clean.csv"
    df = pd.read_csv(path)
    return df


def recommend_funds(risk_appetite: str, top_n: int = 3) -> pd.DataFrame:
    """
    Given a risk appetite string, return the top N funds
    by Sharpe ratio within that risk grade.

    Parameters:
        risk_appetite : one of Low / Moderate / Moderately High / High / Very High
        top_n         : number of funds to return (default 3)

    Returns:
        DataFrame with recommended funds and key metrics
    """
    # normalise input — title case and strip whitespace
    risk_input = risk_appetite.strip().title()

    if risk_input not in VALID_RISK_GRADES:
        print(f"Invalid risk appetite: '{risk_appetite}'")
        print(f"Valid options: {VALID_RISK_GRADES}")
        return pd.DataFrame()

    df = load_performance_data()

    # filter by risk grade
    filtered = df[df["risk_grade"] == risk_input].copy()

    if filtered.empty:
        print(f"No funds found for risk grade: {risk_input}")
        return pd.DataFrame()

    # rank by Sharpe ratio (higher is better)
    filtered = filtered.sort_values("sharpe_ratio", ascending=False)
    top_funds = filtered.head(top_n)

    result = top_funds[[
        "scheme_name", "fund_house", "category",
        "return_3yr_pct", "sharpe_ratio", "alpha",
        "max_drawdown_pct", "expense_ratio_pct", "risk_grade"
    ]].reset_index(drop=True)
    result.index = result.index + 1   # rank starts at 1

    return result


def print_recommendation(risk_appetite: str):
    """Print a nicely formatted recommendation table."""
    print()
    print("=" * 65)
    print(f"  BLUESTOCK FUND RECOMMENDER")
    print(f"  Risk Appetite : {risk_appetite.strip().title()}")
    print("=" * 65)

    result = recommend_funds(risk_appetite)

    if result.empty:
        return

    print(f"\n  Top {len(result)} recommended funds:\n")
    for rank, row in result.iterrows():
        print(f"  #{rank}  {row['scheme_name'][:52]}")
        print(f"       Fund House   : {row['fund_house']}")
        print(f"       Category     : {row['category']}")
        print(f"       3yr Return   : {row['return_3yr_pct']:.2f}%")
        print(f"       Sharpe Ratio : {row['sharpe_ratio']:.3f}")
        print(f"       Alpha        : {row['alpha']:.2f}")
        print(f"       Max Drawdown : {row['max_drawdown_pct']:.1f}%")
        print(f"       Expense Ratio: {row['expense_ratio_pct']:.2f}%")
        print()

    print("  Note: Rankings based on Sharpe Ratio (risk-adjusted returns).")
    print("  This is for educational purposes only — not financial advice.")
    print("=" * 65)


def main():
    print("\nBluestock Fintech — Fund Recommender")
    print("Based on Sharpe Ratio within each risk category\n")

    # run recommendations for all 5 risk levels
    for risk in VALID_RISK_GRADES:
        print_recommendation(risk)
        print()


if __name__ == "__main__":
    main()
