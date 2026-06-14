-- =============================================================
-- Bluestock Mutual Fund Analytics – SQLite Star Schema
-- Day 2 Deliverable | Capstone Project I
-- =============================================================

PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────────────────────
-- DIMENSION: dim_fund
-- One row per mutual fund scheme (master / slowly-changing)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code           INTEGER PRIMARY KEY,          -- AMFI scheme code (natural key)
    fund_house          TEXT    NOT NULL,              -- AMC name (e.g. SBI Mutual Fund)
    scheme_name         TEXT    NOT NULL,              -- Full SEBI-registered scheme name
    category            TEXT,                          -- Broad category: Equity / Debt / Hybrid
    sub_category        TEXT,                          -- E.g. Large Cap, Short Duration
    plan                TEXT,                          -- Regular / Direct
    launch_date         TEXT,                          -- Scheme inception date (YYYY-MM-DD)
    benchmark           TEXT,                          -- E.g. NIFTY 50 TRI
    expense_ratio_pct   REAL    CHECK (expense_ratio_pct BETWEEN 0.0 AND 5.0),
    exit_load_pct       REAL,
    min_sip_amount      INTEGER,                       -- Minimum SIP instalment (INR)
    min_lumpsum_amount  INTEGER,                       -- Minimum one-time investment (INR)
    fund_manager        TEXT,
    risk_category       TEXT,                          -- Low / Moderate / High / Very High
    sebi_category_code  TEXT                           -- SEBI standardisation code
);

-- ─────────────────────────────────────────────────────────────
-- DIMENSION: dim_date
-- Pre-populated calendar for join-free time analytics
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_date (
    date_key    TEXT    PRIMARY KEY,    -- YYYY-MM-DD (ISO 8601)
    year        INTEGER NOT NULL,
    quarter     INTEGER NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    month       INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    week        INTEGER,                -- ISO week number
    day         INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,       -- 0=Monday … 6=Sunday
    is_weekend  INTEGER NOT NULL DEFAULT 0  -- 1 if Saturday or Sunday
);

-- ─────────────────────────────────────────────────────────────
-- FACT: fact_nav
-- Daily NAV observations (forward-filled for non-trading days)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code       INTEGER NOT NULL REFERENCES dim_fund(amfi_code),
    date_key        TEXT    NOT NULL REFERENCES dim_date(date_key),
    nav             REAL    NOT NULL CHECK (nav > 0),
    nav_pct_change  REAL,               -- Day-on-day % change (NULL for first row)
    nav_anomaly     INTEGER DEFAULT 0,  -- 1 if |pct_change| > 20 %
    UNIQUE (amfi_code, date_key)
);

-- ─────────────────────────────────────────────────────────────
-- FACT: fact_transactions
-- Individual investor buy / sell / switch orders
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_transactions (
    txn_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id         TEXT    NOT NULL,
    transaction_date    TEXT    NOT NULL,
    amfi_code           INTEGER NOT NULL REFERENCES dim_fund(amfi_code),
    transaction_type    TEXT    NOT NULL
                          CHECK (transaction_type IN ('SIP','Lumpsum','Redemption','Switch','SWP','STP')),
    amount_inr          REAL    NOT NULL CHECK (amount_inr > 0),
    state               TEXT,
    city                TEXT,
    city_tier           TEXT,           -- Tier 1 / Tier 2 / Tier 3
    age_group           TEXT,           -- E.g. 25-34, 35-44
    gender              TEXT,
    annual_income_lakh  REAL,
    payment_mode        TEXT,           -- UPI / NetBanking / Cheque / NACH
    kyc_status          TEXT            -- Verified / Pending / Rejected / Not Submitted
);

-- ─────────────────────────────────────────────────────────────
-- FACT: fact_performance
-- Scheme-level risk/return metrics (point-in-time snapshot)
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_performance (
    perf_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code           INTEGER NOT NULL REFERENCES dim_fund(amfi_code),
    return_1yr_pct      REAL,           -- Trailing 1-year absolute return (%)
    return_3yr_pct      REAL,           -- Trailing 3-year CAGR (%)
    return_5yr_pct      REAL,           -- Trailing 5-year CAGR (%)
    benchmark_3yr_pct   REAL,           -- Benchmark 3-year CAGR (%)
    alpha               REAL,           -- Jensen's Alpha vs benchmark
    beta                REAL,           -- Market sensitivity (1 = market)
    sharpe_ratio        REAL,           -- Risk-adjusted return (rf = 6.5%)
    sortino_ratio       REAL,           -- Downside risk-adjusted return
    std_dev_ann_pct     REAL,           -- Annualised standard deviation (%)
    max_drawdown_pct    REAL,           -- Maximum peak-to-trough decline (%)
    expense_ratio_pct   REAL,
    morningstar_rating  INTEGER CHECK (morningstar_rating BETWEEN 1 AND 5),
    risk_grade          TEXT            -- Low / Moderate / High / Very High
);

-- ─────────────────────────────────────────────────────────────
-- FACT: fact_aum
-- Monthly AUM aggregated at fund-house level
-- ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date_key        TEXT    NOT NULL REFERENCES dim_date(date_key),
    fund_house      TEXT    NOT NULL,
    aum_crore       REAL,               -- AUM in INR Crore
    aum_lakh_crore  REAL,               -- AUM in INR Lakh Crore (convenience)
    num_schemes     INTEGER,
    UNIQUE (date_key, fund_house)
);

-- ─────────────────────────────────────────────────────────────
-- INDEXES for common join/filter patterns
-- ─────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_nav_amfi_date     ON fact_nav(amfi_code, date_key);
CREATE INDEX IF NOT EXISTS idx_txn_date          ON fact_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_txn_type          ON fact_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_txn_state         ON fact_transactions(state);
CREATE INDEX IF NOT EXISTS idx_aum_date          ON fact_aum(date_key);
