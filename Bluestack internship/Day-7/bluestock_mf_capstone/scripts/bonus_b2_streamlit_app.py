"""
bonus_b2_streamlit_app.py
-------------------------
BONUS B2: Streamlit web app as an alternative to Power BI.

Install and run:
    pip install streamlit plotly
    streamlit run scripts/bonus_b2_streamlit_app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"

st.set_page_config(page_title="Bluestock MF Analytics", page_icon="chart_with_upwards_trend",
                   layout="wide", initial_sidebar_state="expanded")

@st.cache_data
def load_data():
    fund  = pd.read_csv(PROC / "01_fund_master_clean.csv")
    aum   = pd.read_csv(PROC / "03_aum_by_fund_house_clean.csv")
    sip   = pd.read_csv(PROC / "04_monthly_sip_inflows_clean.csv")
    cat   = pd.read_csv(PROC / "05_category_inflows_clean.csv")
    folio = pd.read_csv(PROC / "06_industry_folio_count_clean.csv")
    perf  = pd.read_csv(PROC / "07_scheme_performance_clean.csv")
    tx    = pd.read_csv(PROC / "08_investor_transactions_clean.csv")
    bench = pd.read_csv(PROC / "10_benchmark_indices_clean.csv")
    for df, col in [(aum,"date"),(sip,"month"),(cat,"month"),(bench,"date"),(tx,"transaction_date")]:
        df[col] = pd.to_datetime(df[col])
    return fund, aum, sip, cat, folio, perf, tx, bench

fund, aum, sip, cat, folio, perf, tx, bench = load_data()
PAL = ["#1565C0","#1E88E5","#00ACC1","#2E7D32","#E65100","#6A1B9A","#AD1457","#00695C","#F57F17","#4527A0"]

st.sidebar.title("Bluestock Fintech")
st.sidebar.caption("Mutual Fund Analytics Platform")
page = st.sidebar.radio("Navigate", [
    "Industry Overview", "Fund Performance", "Investor Analytics", "SIP and Market Trends"])

if page == "Industry Overview":
    st.title("Industry Overview")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Industry AUM",      "Rs.81L Crore",   "26% YoY")
    c2.metric("Monthly SIP Inflow","Rs.31,002 Cr",   "All-time high")
    c3.metric("Total Folios",      "26.12 Crore",    "2x since 2022")
    c4.metric("Active SIP Accounts","9.35 Crore",    "1,908 schemes")
    trend = aum.groupby("date")["aum_lakh_crore"].sum().reset_index()
    fig = px.area(trend, x="date", y="aum_lakh_crore",
                  title="Industry AUM Trend 2022-2025 (Rs. Lakh Crore)",
                  color_discrete_sequence=["#1565C0"])
    fig.update_layout(showlegend=False, plot_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        ah = aum.groupby("fund_house")["aum_lakh_crore"].max().sort_values(ascending=True).reset_index()
        fig2 = px.bar(ah, x="aum_lakh_crore", y="fund_house", orientation="h",
                      title="AUM by Fund House (Rs. L Cr)", color="aum_lakh_crore",
                      color_continuous_scale="Blues")
        fig2.update_layout(coloraxis_showscale=False, plot_bgcolor="white")
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        fig3 = px.line(sip, x="month", y="sip_inflow_crore",
                       title="Monthly SIP Inflow (Rs. Crore)", color_discrete_sequence=["#2E7D32"])
        fig3.update_layout(plot_bgcolor="white")
        st.plotly_chart(fig3, use_container_width=True)

elif page == "Fund Performance":
    st.title("Fund Performance")
    c1,c2,c3 = st.columns(3)
    hf = c1.selectbox("Fund House", ["All"] + sorted(perf["fund_house"].unique()))
    cf = c2.selectbox("Category",   ["All"] + sorted(perf["category"].unique()))
    pf = c3.selectbox("Plan",        ["All"] + sorted(perf["plan"].unique()))
    fp = perf.copy()
    if hf != "All": fp = fp[fp["fund_house"]==hf]
    if cf != "All": fp = fp[fp["category"]==cf]
    if pf != "All": fp = fp[fp["plan"]==pf]
    col1, col2 = st.columns(2)
    with col1:
        fig = px.scatter(fp, x="return_3yr_pct", y="std_dev_ann_pct", size="aum_crore",
                         color="category", hover_name="scheme_name",
                         title="Risk vs Return (bubble = AUM)", color_discrete_sequence=PAL)
        fig.update_layout(plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        ts = fp.nlargest(15, "sharpe_ratio")
        fig2 = px.bar(ts, x="sharpe_ratio", y="scheme_name", orientation="h",
                      title="Top 15 by Sharpe Ratio", color="sharpe_ratio",
                      color_continuous_scale="Blues")
        fig2.update_layout(coloraxis_showscale=False, plot_bgcolor="white", yaxis_title="")
        st.plotly_chart(fig2, use_container_width=True)
    st.subheader("Full Fund Table")
    dcols = ["scheme_name","fund_house","category","return_1yr_pct","return_3yr_pct",
             "sharpe_ratio","alpha","beta","max_drawdown_pct","risk_grade"]
    st.dataframe(fp[dcols].sort_values("return_3yr_pct", ascending=False).reset_index(drop=True),
                 use_container_width=True, height=380)

elif page == "Investor Analytics":
    st.title("Investor Analytics")
    c1,c2,c3 = st.columns(3)
    sf = c1.selectbox("State",     ["All"] + sorted(tx["state"].unique()))
    tf = c2.selectbox("City Tier", ["All","T30","B30"])
    af = c3.selectbox("Age Group", ["All"] + ["18-25","26-35","36-45","46-55","56+"])
    ft = tx.copy()
    if sf != "All": ft = ft[ft["state"]==sf]
    if tf != "All": ft = ft[ft["city_tier"]==tf]
    if af != "All": ft = ft[ft["age_group"]==af]
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Transactions", f"{len(ft):,}")
    c2.metric("Total Amount", f"Rs.{ft['amount_inr'].sum()/1e7:.0f} Cr")
    sp = len(ft[ft['transaction_type']=='SIP'])/max(len(ft),1)*100
    c3.metric("SIP Share", f"{sp:.0f}%")
    c4.metric("KYC Verified", "92%")
    col1, col2 = st.columns(2)
    with col1:
        sa = ft.groupby("state")["amount_inr"].sum().sort_values(ascending=True).reset_index()
        fig = px.bar(sa, x="amount_inr", y="state", orientation="h",
                     title="Transaction Amount by State", color="amount_inr",
                     color_continuous_scale="Blues")
        fig.update_layout(coloraxis_showscale=False, plot_bgcolor="white", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        td = ft.groupby("transaction_type")["amount_inr"].sum().reset_index()
        fig2 = px.pie(td, names="transaction_type", values="amount_inr",
                      title="Transaction Type Split", hole=0.5,
                      color_discrete_sequence=["#1565C0","#2E7D32","#E65100"])
        st.plotly_chart(fig2, use_container_width=True)

elif page == "SIP and Market Trends":
    st.title("SIP and Market Trends")
    n50 = bench[bench["index_name"]=="NIFTY50"].set_index("date")["close_value"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=sip["month"], y=sip["sip_inflow_crore"],
                         name="SIP Inflow (Rs. Cr)", marker_color="#1565C0", opacity=0.75))
    fig.add_trace(go.Scatter(x=n50.index, y=n50.values, name="Nifty 50",
                             yaxis="y2", line=dict(color="#E65100", width=2)))
    fig.update_layout(title="Monthly SIP Inflow vs Nifty 50",
                      yaxis=dict(title="SIP Inflow (Rs. Cr)"),
                      yaxis2=dict(overlaying="y", side="right", title="Nifty 50"),
                      plot_bgcolor="white", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        fy = cat[cat["month"].dt.year==2025].groupby("category")["net_inflow_crore"].sum()
        fy = fy.sort_values(ascending=True).reset_index()
        fig2 = px.bar(fy, x="net_inflow_crore", y="category", orientation="h",
                      title="Top Categories FY25 Net Inflow",
                      color="net_inflow_crore", color_continuous_scale="Blues")
        fig2.update_layout(coloraxis_showscale=False, plot_bgcolor="white")
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        pivot = cat.pivot_table(index="category",
                                columns=cat["month"].dt.strftime("%b %Y"),
                                values="net_inflow_crore", aggfunc="sum").fillna(0)
        fig3 = px.imshow(pivot, title="Category Inflow Heatmap", color_continuous_scale="Blues")
        st.plotly_chart(fig3, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.caption("Data: AMFI India | NSE | mfapi.in")
st.sidebar.caption("For educational purposes only")
