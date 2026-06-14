-- queries.sql
-- Bluestock Fintech | Mutual Fund Analytics
-- Day 2: 10 Analytical SQL Queries
-- Run against: data/db/bluestock_mf.db

-- ─────────────────────────────────────────────────────────────
-- Q1: Top 5 funds by AUM (scheme-level)
-- ─────────────────────────────────────────────────────────────
SELECT
    f.scheme_name,
    f.fund_house,
    f.category,
    p.aum_crore
FROM fact_performance p
JOIN dim_fund f ON f.amfi_code = p.amfi_code
ORDER BY p.aum_crore DESC
LIMIT 5;

-- ─────────────────────────────────────────────────────────────
-- Q2: Average NAV per month across all schemes
-- ─────────────────────────────────────────────────────────────
SELECT
    d.year,
    d.month,
    d.month_name,
    ROUND(AVG(n.nav), 2)  AS avg_nav,
    COUNT(*)              AS num_observations
FROM fact_nav n
JOIN dim_date d ON d.date_id = n.date
WHERE d.is_weekday = 1
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- ─────────────────────────────────────────────────────────────
-- Q3: SIP inflow YoY growth
-- ─────────────────────────────────────────────────────────────
SELECT
    month,
    sip_inflow_crore,
    yoy_growth_pct,
    active_sip_accounts_crore
FROM fact_sip_industry
ORDER BY month;

-- ─────────────────────────────────────────────────────────────
-- Q4: Total transaction amount by state
-- ─────────────────────────────────────────────────────────────
SELECT
    t.state,
    COUNT(*)                          AS num_transactions,
    SUM(t.amount_inr)                 AS total_amount_inr,
    ROUND(AVG(t.amount_inr), 0)       AS avg_amount_inr,
    SUM(CASE WHEN t.transaction_type = 'SIP'
             THEN 1 ELSE 0 END)       AS sip_count
FROM fact_transactions t
GROUP BY t.state
ORDER BY total_amount_inr DESC;

-- ─────────────────────────────────────────────────────────────
-- Q5: Funds with expense ratio below 1%
-- ─────────────────────────────────────────────────────────────
SELECT
    f.scheme_name,
    f.fund_house,
    f.category,
    f.sub_category,
    f.expense_ratio_pct,
    f.plan
FROM dim_fund f
WHERE f.expense_ratio_pct < 1.0
ORDER BY f.expense_ratio_pct ASC;

-- ─────────────────────────────────────────────────────────────
-- Q6: Top 10 funds by Sharpe ratio with risk grade
-- ─────────────────────────────────────────────────────────────
SELECT
    f.scheme_name,
    f.fund_house,
    f.category,
    p.sharpe_ratio,
    p.sortino_ratio,
    p.return_3yr_pct,
    p.risk_grade
FROM fact_performance p
JOIN dim_fund f ON f.amfi_code = p.amfi_code
WHERE p.sharpe_ratio IS NOT NULL
ORDER BY p.sharpe_ratio DESC
LIMIT 10;

-- ─────────────────────────────────────────────────────────────
-- Q7: Monthly transaction volume (count + amount) over time
-- ─────────────────────────────────────────────────────────────
SELECT
    SUBSTR(t.transaction_date, 1, 7)  AS month,
    t.transaction_type,
    COUNT(*)                           AS num_transactions,
    SUM(t.amount_inr)                  AS total_amount_inr
FROM fact_transactions t
GROUP BY SUBSTR(t.transaction_date, 1, 7), t.transaction_type
ORDER BY month, t.transaction_type;

-- ─────────────────────────────────────────────────────────────
-- Q8: Funds with positive alpha (outperforming benchmark)
-- ─────────────────────────────────────────────────────────────
SELECT
    f.scheme_name,
    f.category,
    f.sub_category,
    p.alpha,
    p.beta,
    p.return_3yr_pct,
    p.benchmark_3yr_pct
FROM fact_performance p
JOIN dim_fund f ON f.amfi_code = p.amfi_code
WHERE p.alpha > 0
ORDER BY p.alpha DESC;

-- ─────────────────────────────────────────────────────────────
-- Q9: Average SIP amount by age group and city tier
-- ─────────────────────────────────────────────────────────────
SELECT
    t.age_group,
    t.city_tier,
    COUNT(*)                        AS num_investors,
    ROUND(AVG(t.amount_inr), 0)     AS avg_sip_amount,
    SUM(t.amount_inr)               AS total_invested
FROM fact_transactions t
WHERE t.transaction_type = 'SIP'
GROUP BY t.age_group, t.city_tier
ORDER BY t.age_group, t.city_tier;

-- ─────────────────────────────────────────────────────────────
-- Q10: NAV performance for top 5 funds — latest vs 1-year-ago
-- ─────────────────────────────────────────────────────────────
WITH latest AS (
    SELECT amfi_code, MAX(date) AS max_date
    FROM fact_nav
    GROUP BY amfi_code
),
nav_latest AS (
    SELECT n.amfi_code, n.nav AS nav_now, l.max_date
    FROM fact_nav n
    JOIN latest l ON l.amfi_code = n.amfi_code AND l.max_date = n.date
),
nav_1yr AS (
    SELECT n.amfi_code, n.nav AS nav_1yr
    FROM fact_nav n
    JOIN latest l ON l.amfi_code = n.amfi_code
    WHERE n.date = DATE(l.max_date, '-365 days')
)
SELECT
    f.scheme_name,
    f.fund_house,
    ROUND(nl.nav_now, 2)                                    AS nav_latest,
    ROUND(n1.nav_1yr, 2)                                    AS nav_1yr_ago,
    ROUND((nl.nav_now - n1.nav_1yr) / n1.nav_1yr * 100, 2) AS return_1yr_pct
FROM nav_latest nl
JOIN nav_1yr n1    ON n1.amfi_code = nl.amfi_code
JOIN dim_fund f    ON f.amfi_code  = nl.amfi_code
ORDER BY return_1yr_pct DESC
LIMIT 10;
