# Agent Task Log

## 2026-03-24
### Task: Create Django-based REST API for Stock Data
- Initialized Django project `gs_stock_api` and app `data_api`.
- Created virtual environment and installed dependencies: `django`, `djangorestframework`, `pandas`.
- Developed `CSVDataView` to dynamically serve CSV files from the `data/` directory.
- Mapped endpoint names to filenames (e.g., `/barchart` -> `gs_barchart.csv`).
- Introduced a random delay (0.1s - 2.0s) in the API response.
- Configured project to run on `localhost:8080`.
- Verified functionality with `curl`.

## Data Analysis (2026-03-24)
### Data Depiction
The `data/` directory contains historical stock data for Goldman Sachs (GS) sourced from various financial platforms. Each file represents a different data source:
- **gs_barchart.csv**: Data from Barchart.
- **gs_investing_com.csv**: Data from Investing.com.
- **gs_marketwatch.csv**: Data from MarketWatch.
- **gs_nasdaq.csv**: Data from NASDAQ (featuring more recent dates and currency symbols).
- **gs_yahoo_finance.csv**: Data from Yahoo Finance.
- **gs_master_dataset.csv**: A consolidated or baseline dataset used for cross-source comparison.

### Relationships and Variations
- **Temporal Overlap**: The datasets cover overlapping time periods starting from 1999-05-04.
- **Price Discrepancies**: While the data depicts the same security, slight floating-point discrepancies exist between sources (likely due to different adjustment algorithms or rounding in proxies). For example, on 1999-05-04, Open prices vary slightly at the 6th-8th decimal place across Barchart, Investing.com, and MarketWatch.
- **Format Variations**: Most sources use ISO 8601-like timestamps, while `gs_nasdaq.csv` uses `MM/DD/YYYY` format and includes `$` symbols in price fields.

## Yahoo Finance Data Inferences (2026-04-02)

### Analysis Process
A statistical analysis was performed on `data/gs_yahoo_finance.csv` using Python and Pandas to quantify the relationships between stock price metrics, volume, dividends, and splits.

### Key Inferences and Relationships
1. **Price Inter-dependency**: Values for `Open`, `High`, `Low`, and `Close` exhibit extremely high positive correlation (> 0.999), indicating consistent intra-day movement and a narrow typical daily range relative to the stock price.
2. **Volatility and Volume**:
    - There is a strong correlation (**0.61**) between **Trading Volume** and **Daily Volatility %** (defined as the High-Low spread as a percentage of the Open price).
    - This suggests that significant price movements, rather than just absolute price levels, are the primary drivers of trading activity for GS stock.
3. **Volume and Price Relationship**: A weak negative correlation (**-0.19**) exists between the **Opening Price** and **Trading Volume**. This implies a slight trend towards higher trading volumes when the stock price is lower.
4. **Dividends**:
    - The dataset contains **108 dividend events**.
    - Dividend amounts range from **$0.12** to **$4.50**, with a mean payout of approximately **$0.88**.
5. **Stock Splits**: No stock split events were recorded in this specific dataset (all values set to 0.0), indicating that the Yahoo Finance source provided in this project likely uses split-adjusted historical prices without split event markers.

### Decisions Taken
- Used the project's virtual environment (`venv`) Python interpreter to ensure consistency with installed data science libraries.
- Computed correlations specifically on "Volatility %" instead of absolute "Daily Range" to normalize for the stock's growth over time (from ~$50 to ~$900+).
- Verified the integrity of the `Dividends` and `Stock Splits` columns by checking for non-zero occurrences.

## API and Data Transformation (2026-04-02)

### Cleanup Actions
- **Data Reduction**: Deleted all supplementary CSV files (`gs_barchart.csv`, `gs_investing_com.csv`, `gs_marketwatch.csv`, `gs_master_dataset.csv`, `gs_nasdaq.csv`) to focus exclusively on Yahoo Finance data.
- **Route Consolidation**: Removed all generic CSV endpoints from the Django application.

### Dynamic Data Generation
Modified the Django app to serve as a real-time data generator at `/yahoo-finance/latest`.
- **Logic**:
    - Each request computes the mean of the **last 5 rows** for all numeric columns.
    - Applies a random perturbation bounded by the **global standard deviation** of each column.
    - **Trend Adherence**:
        - **OHLC Coupling**: Ensures `High` and `Low` strictly bound `Open` and `Close` to maintain logical daily price limits.
        - **Volatility-Volume Correlation**: Implemented a bias factor that increases `Volume` generation when the generated `High-Low` spread (volatility) is above the historical average, respecting the documented **0.61** correlation.
    - **Persistence**: Every generated row is automatically appended to `data/gs_yahoo_finance.csv` and saved to disk.
- **Endpoint**: `GET /yahoo-finance/latest` returns a JSON object representing the newly created row.

### Decisions Taken
- Chose `datetime.now()` for the `Date` column to simulate live updates while maintaining the `-04:00` timezone offset observed in the raw data.
- Implemented **Volatility Scaling** for Volume generation to ensure that the synthetic data preserves the statistical signature of the original GS stock movements.
- Retained a small random delay (0.1s - 1.0s) in the API response to simulate network latency and processing time.

## PostgreSQL Migration and Table Maintenance (2026-04-02)

### Infrastructure Updates
- **Database Transition**: Migrated the application storage from a flat CSV file to a PostgreSQL database.
- **Connection Parameters**:
    - **Host**: `localhost`
    - **Port**: `5431`
    - **Database**: `yahoo_finance`
    - **User**: `postgres`
- **Dependencies**: Installed `psycopg2-binary` to enable Django's PostgreSQL backend.

### Data Migration
- **Schema Definition**: Created the `YahooFinanceData` model in `data_api/models.py` with appropriate indices on the `date` column.
- **Migration Command**: Developed a custom Django management command `migrate_csv_to_db` to iterate through the historical Yahoo Finance CSV and bulk-insert **6,755 rows** into the new table.

### API Evolution
The `GET /yahoo-finance/latest` endpoint was refactored to interact entirely with PostgreSQL:
- **Statistical Computation**: Now uses Django's `Avg` and `StdDev` aggregates on the database level to derive means from the last 5 records and perturbations from the global dataset.
- **Constant Table Size (FIFO)**: Implemented a "One In, One Out" logic:
    1.  A new statistically consistent row is generated and saved to the table.
    2.  The **oldest row** (determined by date) is immediately identified and deleted.
    3.  This ensures the database remains performant and doesn't grow indefinitely, maintaining a fixed window of historical data.

### Decisions Taken
- Chose `BigIntegerField` for `Volume` to handle potential large historical trading values.
- Implemented `db_index=True` on the `date` field to optimize the "identify oldest" and "fetch last 5" operations, which occur on every API call.
- Retained the statistically driven generation logic to ensure data continuity for any connected frontend or analysis tools.

## React Dashboard Integration and Real-time Visualization (2026-04-02)

### Visualization Architecture
- **React Frontend**: Scaled the system with a React dashboard built using **Vite**.
- **Data Streaming API**: Updated the `/yahoo-finance/latest` endpoint to return the **100 most recent records** in chronological order. This provides enough context for the frontend to render fluid line charts without maintaining local client-side state.
- **Refresh Mechanism**: Implemented a `useInterval` pattern that fetches data every **5 seconds**.
- **Stability and Performance**: 
    - Used **Recharts** with `isAnimationActive={false}` on the line/area components to ensure the UI remains snappy and stable during background refreshes.
    - Added a "Refreshed X seconds ago" timer to provide immediate feedback on the data's recency.

### Design and Aesthetics
- **Monochromatic Theme**: Applied a curated palette (`#000000`, `#e1e4e8`, `#9ca393`, `#939ca3`, etc.) to create a premium, high-frequency trading aesthetic.
- **Glassmorphism**: Utilized `backdrop-filter: blur(12px)` and subtle borders to give the dashboard a modern, layered feel.
- **Monospaced Typography**: Chose **JetBrains Mono** for pricing and volume data to ensure readability and alignment, crucial for financial dashboards.

### Decisions Taken
- **Area Charts over Line Charts**: Switched to Area charts with subtle gradients to provide a more visually "weighted" look that fits the monochromatic design better than thin lines.
- **Background Loading State**: Integrated a spinning refresh icon (`RefreshCw` from Lucide) that alerts the user to incoming data without interrupting the view or causing layout jumps.
- **History Size**: Fixed the return size to 100 rows; this strikes a balance between providing a long enough visual timeline and keeping the API response small (approx. 20-30KB).

## Smooth Stochastic Generation Strategy (2026-04-02)

### The "Jagged Data" Problem
Analysis of the initial generation logic revealed that synthetic points were too volatile. This was because the random walk was using global historical standard deviation (spanning 20 years) to determine each 5-second step, causing physically impossible "price jumps."

### Implementation: Momentum-Driven Random Walk
To achieve the "smooth but random" curves requested, the generator was overhauled with the following logic:
1.  **Anchor Splicing**: Every new point is now calculated as a percentage change from the *immediately preceding record*, rather than a mean of a window.
2.  **Momentum Tracking**: The system calculates the slope over the last 3-5 records. A positive slope adds a "drift" bias to the next point, simulating trend persistence.
3.  **Mean Reversion (Gravity)**: A weak pull towards the 20-year average was added to ensure the stock doesn't walk into unrealistic price territories over long sessions.
4.  **Local Noise Scaling**: Randomness is now constrained to a "Gaussian Noise" model with a strictly limited scale (approx. 0.3% max per 5s refresh).

### Execution Steps Taken
1.  **Database Purge**: Executed `YahooFinanceData.objects.all().delete()` to remove all noisy synthetic data.
2.  **Clean State Recovery**: Re-ran `migrate_csv_to_db` to restore the high-fidelity historical data.
3.  **Code Deployment**: Updated `views.py` with the new momentum logic and fixed linting errors regarding type casting.
4.  **Verified Dashboard**: Confirmed that the React dashboard now displays organic, smooth area transitions.

## 1-Year Momentum Tracking (2026-04-02)

### Shift to Long-Term Bias
The user requested that the generator account for trends over a much larger timeframe (at least one year). This transition from "local momentum" to "macro momentum" prevents the synthetic data from becoming trapped in short-term noise.

### Logic Updates
1.  **Window Expansion**: The generator now retrieves the record from **252 steps ago** (the standard count of trading days in a year) to calculate the `yearly_momentum`.
2.  **Normalized Drift**: The yearndly price change is normalized into a micro-step drift. This means that if the stock is in a long-term bull market (e.g., up 20% over the last year), the 5-second refreshes will have a very subtle but persistent upward bias.
3.  **Database Reset**: Flushed the database and re-migrated the 6,755 historical records to ensure the first generated point uses a high-context 1-year historical lookback.

### Decisions Taken
- **252-Record Index**: Chose 252 as the specific offset to represent a standard trading year.
- **Micro-scaling**: Scaled the yearly drift by a factor of `0.0001` per step to ensure that the "drift" doesn't overpower the "random walk" in the short term, maintaining a natural appearance.

## Row Generation Analysis and Improvement Strategy (2026-04-02)

### Current Generation Logic Review
The existing synthetic data generation in `data_api/views.py` uses a momentum-driven random walk with:
- Yearly momentum calculation (percentage change over ~252 records)
- Mean reversion towards global average price
- Fixed Gaussian noise scale (0.002)
- OHLC derivation based on open/close with random intra-day ranges
- Volume correlated with price change magnitude

### Key Issues Identified
1. **Static Volatility Modeling**: Uses global standard deviation, ignoring time-varying market volatility
2. **Lack of Volatility Clustering**: Real markets exhibit "volatility begets volatility" where high-vol days predict future high-vol periods
3. **Normal Distribution Assumption**: Historical returns show fat tails (extreme moves more common than Gaussian predicts)
4. **Coarse Trend Modeling**: Yearly momentum too broad for 5-second refresh intervals
5. **Simplified Volume Dynamics**: Lacks realistic volume patterns, seasonality, and elasticity

### Historical Data Insights from CSV Analysis
Analysis of `data/gs_yahoo_finance.csv` (25+ years of GS data) revealed:
- **Mean Daily Return**: ~0.08% (positive long-term growth)
- **Daily Volatility**: 1.5-2% (varies by period, shows clustering)
- **Distribution Characteristics**: Negative skewness, kurtosis 3-5 (fat tails)
- **Rolling 30-Day Volatility**: ~1.8% average, with persistent high-vol clusters
- **Volume Correlations**: Strong positive with absolute returns (~0.6)
- **Autocorrelation Patterns**: Returns nearly independent, squared returns show persistence (~0.2)
- **Intraday Ranges**: (High-Low)/Close typically 1-3%

### Improved Generation Strategy Implemented
1. **Rolling Volatility Calculation**: Replaced global std with 30-day rolling volatility for dynamic noise scaling
2. **Volatility Clustering Model**: Adjusts noise scale based on recent volatility levels (high recent vol increases future vol)
3. **Fat-Tailed Noise Distribution**: Switched from Gaussian to t-distribution (df=4.5) for realistic extreme moves
4. **Multi-Timeframe Momentum**: Combines yearly (30%), medium-term (50%), and short-term (20%) trends
5. **Enhanced Volume Modeling**: Elasticity to price changes, recent average volumes, and random components
6. **Realistic OHLC Generation**: Intraday ranges based on volatility, proper high/low bounds
7. **Seasonal Effects**: Day-of-week and monthly adjustments (Mondays higher vol, October volatility)
8. **Adaptive Mean Reversion**: Strength based on deviation from long-term mean

### Implementation Details
- **Volatility Scaling**: `vol_scale = max(0.005, min(0.05, rolling_std / current_price))`
- **Clustering Logic**: If recent avg volatility > 2%, scale up by 1.5x; if <1%, scale down by 0.7x
- **Noise Generation**: Uses scipy.stats.t for fat-tailed distribution
- **Trend Combination**: Weighted average of multiple momentum horizons
- **Volume Elasticity**: Multiplier = 1 + |price_change| * 2.0, with base from recent averages
- **OHLC Realism**: Range = mid_price * (0.015 + vol_scale * 10) * random(0.5-1.5)
- **Seasonal Adjustments**: Monday +20% vol, Friday -10% vol, October +30% vol

### Validation Metrics
Post-implementation verification ensures synthetic data matches historical:
- Return distribution statistics (mean, std, skew, kurtosis)
- Volatility clustering (autocorrelation of squared returns)
- Volume-price relationships and elasticity
- Intraday range patterns and OHLC consistency
- Absence of unrealistic jumps or mechanical patterns

### Decisions Taken
- **Rolling Window**: 30-day for volatility to balance responsiveness and stability
- **Distribution Parameters**: t-distribution with 4.5 degrees of freedom based on historical kurtosis
- **Momentum Weights**: Yearly 30% for macro trends, medium 50% for cycle, short 20% for noise
- **Volume Base**: Recent 10-day average to capture current market activity levels
- **Reversion Strength**: Scales with deviation (0.0005-0.002) to prevent over-correction
- **Seasonal Factors**: Conservative adjustments to avoid over-fitting specific periods

### Implementation Status
The improved generation strategy has been fully implemented in `data_api/views.py` with the following key changes:
- Added rolling volatility calculation using 30-day window
- Implemented volatility clustering based on recent activity
- Switched to t-distribution for fat-tailed noise (with Gaussian fallback)
- Enhanced multi-timeframe momentum weighting
- Improved volume modeling with elasticity and recent averages
- Realistic OHLC generation with volatility-based ranges
- Added seasonal adjustments for day-of-week and monthly effects
- Adaptive mean reversion strength based on deviation

### Dependencies
- Added scipy for t-distribution (optional, with fallback to Gaussian)
- No breaking changes to existing API or database schema

### Bug Fix: StdDev Aggregate Error (2026-04-02)
**Issue**: API returned error "std is not an aggregate expression" when computing rolling volatility.

**Root Cause**: Attempted to use custom `StdDevPop` Func class in `aggregate()`, but Django's aggregate functions require standard aggregates like `StdDev` (sample standard deviation) or `StdDevPop` as a direct import. The custom Func was not recognized as a valid aggregate expression.

**Fix Applied**: 
- Replaced `StdDevPop('close')` with `StdDev('close')` in the aggregate call
- Removed the unnecessary custom `StdDevPop` class definition
- `StdDev` provides sample standard deviation, which is appropriate for rolling volatility calculations

**Code Change**:
```python
# Before (error):
rolling_std = recent_30.aggregate(std=StdDevPop('close'))['std']

# After (fixed):
rolling_std = recent_30.aggregate(std=StdDev('close'))['std']
```

**Testing**: The API now correctly computes rolling volatility without aggregate errors.
