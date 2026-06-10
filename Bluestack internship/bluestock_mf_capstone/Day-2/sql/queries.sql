-- =============================================================
-- Bluestock Mutual Fund Analytics – 10 Analytical SQL Queries
-- Day 2 Deliverable | Capstone Project I
-- =============================================================

-- Q1: Top 5 Fund Houses by Latest AUM
-- Business use: Identify market leaders by assets under management
SELECT f.fund_house,
       f.scheme_name,
       p.return_1yr_pct,
       p.morningstar_rating,
       a.total_aum_crore
FROM   fact_performance p
JOIN   dim_fund f ON f.amfi_code = p.amfi_code
LEFT JOIN (
    SELECT fund_house, SUM(aum_crore) AS total_aum_crore
    FROM   fact_aum
    WHERE  date_key = (SELECT MAX(date_key) FROM fact_aum)
    GROUP  BY fund_house
) a ON a.fund_house = f.fund_house
ORDER  BY a.total_aum_crore DESC
LIMIT  5;

-- Q2: Average NAV Per Month (across all funds)
-- Business use: Track overall market NAV trend by calendar month
SELECT substr(n.date_key,1,4)               AS year,
       CAST(substr(n.date_key,6,2) AS INTEGER) AS month,
       ROUND(AVG(n.nav), 4)                  AS avg_nav,
       COUNT(*)                               AS records
FROM   fact_nav n
GROUP  BY year, month
ORDER  BY year, month;

-- Q3: SIP Transaction Count and Volume Year-on-Year
-- Business use: Track SIP adoption and growth over time
SELECT strftime('%Y', transaction_date)   AS yr,
       COUNT(*)                            AS sip_count,
       ROUND(SUM(amount_inr)/1e7, 2)      AS total_inr_crore
FROM   fact_transactions
WHERE  transaction_type = 'SIP'
GROUP  BY yr
ORDER  BY yr;

-- Q4: Transaction Count and Volume by State
-- Business use: Geographic distribution of investor activity
SELECT state,
       COUNT(*)                       AS txn_count,
       ROUND(SUM(amount_inr)/1e7, 2) AS total_crore
FROM   fact_transactions
GROUP  BY state
ORDER  BY txn_count DESC
LIMIT  15;

-- Q5: Funds with Expense Ratio Below 1%
-- Business use: Surface cost-efficient schemes for investors
SELECT f.scheme_name,
       f.fund_house,
       f.category,
       f.expense_ratio_pct
FROM   dim_fund f
WHERE  f.expense_ratio_pct < 1.0
ORDER  BY f.expense_ratio_pct ASC;

-- Q6: Top 10 Funds by 3-Year CAGR with Risk Metrics
-- Business use: Performance league table for equity advisors
SELECT f.scheme_name,
       f.category,
       p.return_3yr_pct,
       p.alpha,
       p.sharpe_ratio
FROM   fact_performance p
JOIN   dim_fund f ON f.amfi_code = p.amfi_code
WHERE  p.return_3yr_pct IS NOT NULL
ORDER  BY p.return_3yr_pct DESC
LIMIT  10;

-- Q7: KYC Status Distribution Among Investors
-- Business use: Compliance monitoring – what % of transactions are KYC-verified
SELECT kyc_status,
       COUNT(*) AS txn_count,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM   fact_transactions
GROUP  BY kyc_status
ORDER  BY txn_count DESC;

-- Q8: NAV 52-Week High / Low Range by Fund (2025)
-- Business use: Volatility screening for risk-aware investors
SELECT f.scheme_name,
       ROUND(MAX(n.nav), 4) AS high_52w,
       ROUND(MIN(n.nav), 4) AS low_52w,
       ROUND((MAX(n.nav) - MIN(n.nav)) / MIN(n.nav) * 100, 2) AS range_pct
FROM   fact_nav n
JOIN   dim_fund f ON f.amfi_code = n.amfi_code
WHERE  substr(n.date_key, 1, 4) = '2025'
GROUP  BY n.amfi_code
ORDER  BY range_pct DESC
LIMIT  10;

-- Q9: AUM by Fund House – Latest Month
-- Business use: Market-share snapshot for competitor benchmarking
SELECT fund_house,
       ROUND(SUM(aum_crore), 0) AS total_aum_crore
FROM   fact_aum
WHERE  date_key = (SELECT MAX(date_key) FROM fact_aum)
GROUP  BY fund_house
ORDER  BY total_aum_crore DESC;

-- Q10: Redemption-to-Purchase Ratio by Category
-- Business use: Detect net outflow risk by fund category
SELECT f.category,
       ROUND(SUM(CASE WHEN t.transaction_type = 'Redemption'
                      THEN t.amount_inr ELSE 0 END), 0)          AS redemptions_inr,
       ROUND(SUM(CASE WHEN t.transaction_type IN ('SIP','Lumpsum')
                      THEN t.amount_inr ELSE 0 END), 0)          AS purchases_inr,
       ROUND(
         SUM(CASE WHEN t.transaction_type = 'Redemption' THEN t.amount_inr ELSE 0 END) * 1.0
         / NULLIF(SUM(CASE WHEN t.transaction_type IN ('SIP','Lumpsum')
                           THEN t.amount_inr ELSE 0 END), 0)
       , 4)                                                        AS redemption_ratio
FROM   fact_transactions t
JOIN   dim_fund f ON f.amfi_code = t.amfi_code
GROUP  BY f.category
ORDER  BY redemption_ratio DESC;
