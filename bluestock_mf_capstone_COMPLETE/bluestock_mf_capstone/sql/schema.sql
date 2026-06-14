-- schema.sql
-- Bluestock Fintech - Mutual Fund Analytics
-- Day 2: SQLite star schema definition
--
-- Star schema design:
--   2 dimension tables : dim_fund, dim_date
--   6 fact tables      : fact_nav, fact_transactions, fact_performance,
--                        fact_aum, fact_sip_industry, fact_portfolio
--
-- All foreign keys reference dim_fund(amfi_code) or dim_date(date_id)


-- ─────────────────────────────────────────────────────────────
-- DIMENSION TABLES
-- ─────────────────────────────────────────────────────────────

-- dim_fund: one row per mutual fund scheme
-- this is the master reference for all fund-level attributes
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code           INTEGER PRIMARY KEY,
    fund_house          TEXT    NOT NULL,
    scheme_name         TEXT    NOT NULL,
    category            TEXT    NOT NULL,   -- Equity / Debt
    sub_category        TEXT,               -- Large Cap / Mid Cap / Liquid etc.
    plan                TEXT,               -- Regular / Direct
    launch_date         DATE,
    benchmark           TEXT,
    expense_ratio_pct   REAL,
    exit_load_pct       REAL,
    min_sip_amount      INTEGER,
    min_lumpsum_amount  INTEGER,
    fund_manager        TEXT,
    risk_category       TEXT,               -- Low / Moderate / High / Very High
    sebi_category_code  TEXT
);

-- dim_date: one row per calendar date
-- pre-computed date parts so SQL queries don't need to parse dates repeatedly
CREATE TABLE IF NOT EXISTS dim_date (
    date_id     TEXT    PRIMARY KEY,        -- stored as YYYY-MM-DD string
    year        INTEGER NOT NULL,
    month       INTEGER NOT NULL,           -- 1 to 12
    quarter     INTEGER NOT NULL,           -- 1 to 4
    month_name  TEXT    NOT NULL,           -- January, February etc.
    day_of_week INTEGER NOT NULL,           -- 0=Monday, 6=Sunday
    is_weekday  INTEGER NOT NULL            -- 1 if Mon-Fri, 0 if Sat-Sun
);


-- ─────────────────────────────────────────────────────────────
-- FACT TABLES
-- ─────────────────────────────────────────────────────────────

-- fact_nav: daily NAV per scheme — the core time-series fact table
CREATE TABLE IF NOT EXISTS fact_nav (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code           INTEGER NOT NULL REFERENCES dim_fund(amfi_code),
    date                TEXT    NOT NULL REFERENCES dim_date(date_id),
    nav                 REAL    NOT NULL,
    daily_return_pct    REAL,               -- (nav_today / nav_yesterday) - 1
    UNIQUE(amfi_code, date)
);

-- fact_transactions: individual investor SIP/Lumpsum/Redemption transactions
CREATE TABLE IF NOT EXISTS fact_transactions (
    tx_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id         TEXT    NOT NULL,
    transaction_date    TEXT    NOT NULL,
    amfi_code           INTEGER NOT NULL REFERENCES dim_fund(amfi_code),
    transaction_type    TEXT    NOT NULL,   -- SIP / Lumpsum / Redemption
    amount_inr          INTEGER NOT NULL,
    state               TEXT,
    city                TEXT,
    city_tier           TEXT,               -- T30 or B30
    age_group           TEXT,
    gender              TEXT,
    annual_income_lakh  REAL,
    payment_mode        TEXT,
    kyc_status          TEXT
);

-- fact_performance: computed risk/return metrics per scheme (as of latest date)
CREATE TABLE IF NOT EXISTS fact_performance (
    amfi_code           INTEGER PRIMARY KEY REFERENCES dim_fund(amfi_code),
    scheme_name         TEXT,
    return_1yr_pct      REAL,
    return_3yr_pct      REAL,
    return_5yr_pct      REAL,
    benchmark_3yr_pct   REAL,
    alpha               REAL,               -- excess return over benchmark
    beta                REAL,               -- market sensitivity
    sharpe_ratio        REAL,               -- risk-adjusted return
    sortino_ratio       REAL,               -- downside risk-adjusted return
    std_dev_ann_pct     REAL,               -- annualised volatility
    max_drawdown_pct    REAL,               -- worst peak-to-trough decline
    aum_crore           INTEGER,
    expense_ratio_pct   REAL,
    morningstar_rating  INTEGER,
    risk_grade          TEXT
);

-- fact_aum: quarterly AUM per fund house
CREATE TABLE IF NOT EXISTS fact_aum (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    date            TEXT    NOT NULL,
    fund_house      TEXT    NOT NULL,
    aum_lakh_crore  REAL,
    aum_crore       INTEGER,
    num_schemes     INTEGER,
    UNIQUE(date, fund_house)
);

-- fact_sip_industry: monthly industry-level SIP data (not per scheme)
CREATE TABLE IF NOT EXISTS fact_sip_industry (
    month                       TEXT    PRIMARY KEY,  -- YYYY-MM-DD (first of month)
    sip_inflow_crore            INTEGER,
    active_sip_accounts_crore   REAL,
    new_sip_accounts_lakh       REAL,
    sip_aum_lakh_crore          REAL,
    yoy_growth_pct              REAL                  -- NULL for first 12 months
);

-- fact_portfolio: top equity holdings per fund
CREATE TABLE IF NOT EXISTS fact_portfolio (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code           INTEGER NOT NULL REFERENCES dim_fund(amfi_code),
    stock_symbol        TEXT,
    stock_name          TEXT,
    sector              TEXT,
    weight_pct          REAL,
    market_value_cr     REAL,
    current_price_inr   REAL,
    portfolio_date      TEXT,
    UNIQUE(amfi_code, stock_symbol, portfolio_date)
);


-- ─────────────────────────────────────────────────────────────
-- INDEXES for faster query performance
-- ─────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_nav_amfi_date    ON fact_nav(amfi_code, date);
CREATE INDEX IF NOT EXISTS idx_nav_date         ON fact_nav(date);
CREATE INDEX IF NOT EXISTS idx_tx_date          ON fact_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_tx_amfi          ON fact_transactions(amfi_code);
CREATE INDEX IF NOT EXISTS idx_tx_state         ON fact_transactions(state);
CREATE INDEX IF NOT EXISTS idx_portfolio_amfi   ON fact_portfolio(amfi_code);
