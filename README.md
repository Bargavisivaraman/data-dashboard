# 📊 Data Dashboard

An interactive Streamlit dashboard for exploring any CSV or Excel dataset.

## Setup

```bash
# 1. Create a virtual environment
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the dashboard
streamlit run dashboard.py
```

The dashboard opens at https://data-dashboard-2026.streamlit.app

## Features

- Upload any CSV or Excel file
- Auto-detected column types (numeric, categorical, date)
- Sidebar filters for categorical columns and date ranges
- KPI metrics row
- Histogram with color grouping
- Bar chart with Sum / Mean / Count aggregations
- Scatter plot with optional OLS trendline
- Time series / area chart with frequency toggle
- Sortable raw data table + CSV export

## Tips

- Try the built-in **sample sales dataset** to explore all features first
- Works best with datasets that have at least one date column and a few numeric + categorical columns
- Large files (>100k rows) may be slow — consider pre-aggregating
