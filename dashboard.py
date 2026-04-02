import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from fpdf import FPDF
import tempfile, os, base64
from datetime import datetime

st.set_page_config(page_title="Data Dashboard", layout="wide", page_icon="📊")

st.markdown("""
<style>
.empty-state {
    background: #f8f9fa;
    border: 1.5px dashed #dee2e6;
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
    color: #6c757d;
}
.col-pill {
    display: inline-block;
    background: #e9ecef;
    border-radius: 6px;
    padding: 2px 10px;
    margin: 3px;
    font-size: 13px;
    font-family: monospace;
    color: #495057;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 Data Dashboard")
    st.divider()

    uploaded_file = st.file_uploader(
        "Upload a CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        help="Upload your dataset to get started"
    )

    st.divider()
    st.caption("No file? Use the sample dataset below.")
    use_sample = st.button("Load sample data", use_container_width=True)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_sample():
    np.random.seed(42)
    n = 300
    regions = ["North", "South", "East", "West"]
    categories = ["Electronics", "Clothing", "Food", "Books", "Sports"]
    months = pd.date_range("2023-01-01", periods=12, freq="MS")
    df = pd.DataFrame({
        "Date": np.random.choice(months, n),
        "Region": np.random.choice(regions, n),
        "Category": np.random.choice(categories, n),
        "Sales": np.random.randint(500, 15000, n),
        "Units": np.random.randint(1, 200, n),
        "Profit": np.random.randint(50, 5000, n),
        "Customer_Rating": np.round(np.random.uniform(2.5, 5.0, n), 1),
    })
    df["Date"] = pd.to_datetime(df["Date"])
    return df

@st.cache_data
def load_uploaded(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    for col in df.columns:
        if df[col].dtype == object:
            try:
                converted = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
                if converted.notna().mean() > 0.7:
                    df[col] = converted
            except Exception:
                pass
    return df

if "df" not in st.session_state:
    st.session_state.df = None

if uploaded_file:
    st.session_state.df = load_uploaded(uploaded_file)
elif use_sample:
    st.session_state.df = load_sample()

df = st.session_state.df

# ── Empty state (no file uploaded) ───────────────────────────────────────────
if df is None:
    st.markdown("## 👋 Welcome to the Data Dashboard")
    st.markdown("Upload a CSV or Excel file to get started, or try the sample dataset.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="empty-state">
            <div style="font-size:2rem">📁</div>
            <strong>Upload your file</strong><br>
            <span style="font-size:13px">CSV or Excel supported</span>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="empty-state">
            <div style="font-size:2rem">🔍</div>
            <strong>Explore & filter</strong><br>
            <span style="font-size:13px">Sidebar filters auto-detect your columns</span>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="empty-state">
            <div style="font-size:2rem">📤</div>
            <strong>Export to PDF</strong><br>
            <span style="font-size:13px">Download a summary report instantly</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("#### What format does my file need to be?")
    st.markdown("""
    The dashboard works best with files that have at least:
    - **One numeric column** (Sales, Score, Count, etc.) for charts and KPIs
    - **One categorical column** (Region, Category, Status, etc.) for grouping
    - **One date column** *(optional)* for time series charts
    """)
    st.stop()

# ── Detect column types ───────────────────────────────────────────────────────
num_cols = df.select_dtypes(include="number").columns.tolist()
date_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
cat_cols = [c for c in df.select_dtypes(include=["object", "category"]).columns.tolist()
            if c not in date_cols]

# ── Sidebar filters ───────────────────────────────────────────────────────────
with st.sidebar:
    st.divider()
    st.subheader("Filters")

    filtered_df = df.copy()

    for col in cat_cols[:3]:
        unique_vals = df[col].dropna().unique()
        if len(unique_vals) > 50:
            continue
        raw = unique_vals.tolist()
        try:
            options = sorted(raw, key=lambda x: str(x))
        except Exception:
            options = raw
        selected = st.multiselect(col, options, default=options, key=f"filter_{col}")
        if selected:
            filtered_df = filtered_df[filtered_df[col].isin(selected)]

    if date_cols:
        dcol = date_cols[0]
        min_d = df[dcol].min().date()
        max_d = df[dcol].max().date()
        date_range = st.date_input("Date range", value=(min_d, max_d), min_value=min_d, max_value=max_d)
        if len(date_range) == 2:
            filtered_df = filtered_df[
                (filtered_df[dcol].dt.date >= date_range[0]) &
                (filtered_df[dcol].dt.date <= date_range[1])
            ]

    st.caption(f"Showing {len(filtered_df):,} of {len(df):,} rows")

    # ── Dataset info panel ────────────────────────────────────────────────────
    st.divider()
    st.subheader("Dataset info")
    st.markdown(f"**{len(df):,} rows · {len(df.columns)} columns**")

    if num_cols:
        st.markdown("**Numeric**")
        st.markdown(" ".join([f'<span class="col-pill">{c}</span>' for c in num_cols]), unsafe_allow_html=True)
    if cat_cols:
        st.markdown("**Categorical**")
        st.markdown(" ".join([f'<span class="col-pill">{c}</span>' for c in cat_cols]), unsafe_allow_html=True)
    if date_cols:
        st.markdown("**Date**")
        st.markdown(" ".join([f'<span class="col-pill">{c}</span>' for c in date_cols]), unsafe_allow_html=True)

# ── KPI row ───────────────────────────────────────────────────────────────────
st.subheader("Overview")

if not num_cols:
    st.markdown("""
    <div class="empty-state">
        <div style="font-size:2rem">🔢</div>
        <strong>No numeric columns detected</strong><br>
        <span style="font-size:13px">KPI metrics and charts need at least one numeric column (e.g. Sales, Count, Score).</span>
    </div>""", unsafe_allow_html=True)
else:
    kpi_cols = num_cols[:4]
    metric_cols = st.columns(len(kpi_cols))
    for i, col in enumerate(kpi_cols):
        total = filtered_df[col].sum()
        avg = filtered_df[col].mean()
        with metric_cols[i]:
            st.metric(
                label=col,
                value=f"{total:,.0f}" if abs(total) > 100 else f"{total:,.2f}",
                delta=f"avg {avg:,.1f}"
            )

st.divider()

# ── Distribution + Breakdown ──────────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Distribution")
    if not num_cols:
        st.markdown('<div class="empty-state"><div style="font-size:2rem">📊</div><strong>No numeric columns</strong><br><span style="font-size:13px">Add a numeric column to your dataset to see distributions.</span></div>', unsafe_allow_html=True)
    else:
        x_col = st.selectbox("Select column", num_cols, key="hist_col")
        color_col = st.selectbox("Color by", ["None"] + cat_cols, key="hist_color")
        color = color_col if color_col != "None" else None
        fig = px.histogram(filtered_df, x=x_col, color=color, nbins=30,
                           template="simple_white",
                           color_discrete_sequence=px.colors.qualitative.Set2)
        fig.update_layout(bargap=0.05, legend_title_text="")
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Breakdown")
    if not cat_cols:
        st.markdown('<div class="empty-state"><div style="font-size:2rem">🏷️</div><strong>No categorical columns</strong><br><span style="font-size:13px">Add a text/category column (e.g. Region, Status) to group your data.</span></div>', unsafe_allow_html=True)
    elif not num_cols:
        st.markdown('<div class="empty-state"><div style="font-size:2rem">🔢</div><strong>No numeric columns</strong><br><span style="font-size:13px">Need a numeric column to aggregate by group.</span></div>', unsafe_allow_html=True)
    else:
        group_col = st.selectbox("Group by", cat_cols, key="bar_group")
        value_col = st.selectbox("Value", num_cols, key="bar_val")
        agg = st.radio("Aggregation", ["Sum", "Mean", "Count"], horizontal=True)
        agg_fn = {"Sum": "sum", "Mean": "mean", "Count": "count"}[agg]
        grouped = filtered_df.groupby(group_col)[value_col].agg(agg_fn).reset_index()
        grouped = grouped.sort_values(value_col, ascending=False)
        fig2 = px.bar(grouped, x=group_col, y=value_col, template="simple_white",
                      color=group_col,
                      color_discrete_sequence=px.colors.qualitative.Set2)
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

# ── Correlation heatmap ───────────────────────────────────────────────────────
st.subheader("Correlation heatmap")

if len(num_cols) < 2:
    st.markdown('<div class="empty-state"><div style="font-size:2rem">🔗</div><strong>Need at least 2 numeric columns</strong><br><span style="font-size:13px">The heatmap shows how your numeric columns relate to each other.</span></div>', unsafe_allow_html=True)
else:
    corr = filtered_df[num_cols].corr().round(2)
    fig_heat = go.Figure(go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.columns.tolist(),
        colorscale="RdBu",
        zmid=0,
        zmin=-1, zmax=1,
        text=corr.values.round(2),
        texttemplate="%{text}",
        textfont={"size": 12},
        hoverongaps=False,
    ))
    fig_heat.update_layout(
        template="simple_white",
        height=400,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(tickangle=-30),
    )
    st.plotly_chart(fig_heat, use_container_width=True)
    st.caption("Values range from -1 (strong negative) to +1 (strong positive). Values near 0 mean little correlation.")

# ── Scatter ───────────────────────────────────────────────────────────────────
if len(num_cols) >= 2:
    st.subheader("Correlation scatter")
    sc1, sc2, sc3 = st.columns([2, 2, 1])
    with sc1:
        x_axis = st.selectbox("X axis", num_cols, index=0, key="sc_x")
    with sc2:
        y_axis = st.selectbox("Y axis", num_cols, index=min(1, len(num_cols)-1), key="sc_y")
    with sc3:
        trendline = st.checkbox("Trendline", value=True)
    color_scatter = cat_cols[0] if cat_cols else None
    fig3 = px.scatter(filtered_df, x=x_axis, y=y_axis, color=color_scatter,
                      trendline="ols" if trendline else None,
                      template="simple_white", opacity=0.7,
                      color_discrete_sequence=px.colors.qualitative.Set2)
    st.plotly_chart(fig3, use_container_width=True)

# ── Time series ───────────────────────────────────────────────────────────────
if date_cols and num_cols:
    st.subheader("Trend over time")
    ts_col = st.selectbox("Metric", num_cols, key="ts_metric")
    ts_group = st.selectbox("Group by", ["None"] + cat_cols, key="ts_group")
    freq = st.radio("Frequency", ["Day", "Week", "Month"], horizontal=True, index=2)
    freq_map = {"Day": "D", "Week": "W", "Month": "ME"}
    dcol = date_cols[0]
    if ts_group != "None":
        ts_df = (filtered_df.groupby([pd.Grouper(key=dcol, freq=freq_map[freq]), ts_group])[ts_col]
                 .sum().reset_index())
        fig4 = px.line(ts_df, x=dcol, y=ts_col, color=ts_group, template="simple_white",
                       color_discrete_sequence=px.colors.qualitative.Set2)
    else:
        ts_df = filtered_df.groupby(pd.Grouper(key=dcol, freq=freq_map[freq]))[ts_col].sum().reset_index()
        fig4 = px.area(ts_df, x=dcol, y=ts_col, template="simple_white",
                       color_discrete_sequence=["#5DCAA5"])
    fig4.update_layout(legend_title_text="")
    st.plotly_chart(fig4, use_container_width=True)
elif not date_cols and df is not None:
    st.subheader("Trend over time")
    st.markdown('<div class="empty-state"><div style="font-size:2rem">📅</div><strong>No date column detected</strong><br><span style="font-size:13px">Add a date/time column to your dataset to see trends over time.</span></div>', unsafe_allow_html=True)

# ── Raw data ──────────────────────────────────────────────────────────────────
with st.expander("Raw data", expanded=False):
    sort_col = st.selectbox("Sort by", df.columns.tolist(), key="sort")
    sort_asc = st.checkbox("Ascending", value=True)
    try:
        sorted_df = filtered_df.sort_values(sort_col, ascending=sort_asc, key=lambda x: x.astype(str))
    except Exception:
        sorted_df = filtered_df
    st.dataframe(sorted_df, use_container_width=True, height=300)
    csv = filtered_df.to_csv(index=False)
    st.download_button("⬇️ Download filtered data as CSV", csv, "filtered_data.csv", "text/csv")

# ── PDF Export ────────────────────────────────────────────────────────────────
st.divider()
st.subheader("Export report")

if st.button("📄 Generate PDF report", use_container_width=False):
    with st.spinner("Building your PDF report..."):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Title
        pdf.set_font("Helvetica", "B", 20)
        pdf.cell(0, 12, "Data Dashboard Report", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 6, f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M')}", ln=True)
        pdf.ln(4)

        # Dataset summary
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, "Dataset Summary", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Total rows: {len(df):,}  |  Filtered rows: {len(filtered_df):,}  |  Columns: {len(df.columns)}", ln=True)
        pdf.cell(0, 6, f"Numeric columns: {', '.join(num_cols) if num_cols else 'None'}", ln=True)
        pdf.cell(0, 6, f"Categorical columns: {', '.join(cat_cols) if cat_cols else 'None'}", ln=True)
        pdf.cell(0, 6, f"Date columns: {', '.join(date_cols) if date_cols else 'None'}", ln=True)
        pdf.ln(4)

        # KPI summary
        if num_cols:
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 8, "KPI Summary (filtered data)", ln=True)
            pdf.set_font("Helvetica", "", 10)
            for col in num_cols[:6]:
                total = filtered_df[col].sum()
                avg = filtered_df[col].mean()
                mn = filtered_df[col].min()
                mx = filtered_df[col].max()
                pdf.cell(0, 6, f"{col}:  sum={total:,.1f}   avg={avg:,.1f}   min={mn:,.1f}   max={mx:,.1f}", ln=True)
            pdf.ln(4)

        # Correlation table
        if len(num_cols) >= 2:
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 8, "Correlation Matrix", ln=True)
            pdf.set_font("Helvetica", "", 9)
            corr = filtered_df[num_cols].corr().round(2)
            col_w = min(35, 170 // (len(num_cols) + 1))
            # Header row
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(col_w, 7, "", border=1, fill=True)
            for c in num_cols:
                pdf.cell(col_w, 7, c[:10], border=1, fill=True)
            pdf.ln()
            for row_name in num_cols:
                pdf.cell(col_w, 7, row_name[:10], border=1)
                for c in num_cols:
                    val = corr.loc[row_name, c]
                    pdf.cell(col_w, 7, str(val), border=1)
                pdf.ln()
            pdf.ln(4)

        # Categorical breakdown
        if cat_cols and num_cols:
            pdf.set_font("Helvetica", "B", 13)
            pdf.cell(0, 8, f"Breakdown by {cat_cols[0]}", ln=True)
            pdf.set_font("Helvetica", "", 10)
            grouped_pdf = filtered_df.groupby(cat_cols[0])[num_cols[0]].sum().reset_index()
            grouped_pdf = grouped_pdf.sort_values(num_cols[0], ascending=False)
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(90, 7, cat_cols[0], border=1, fill=True)
            pdf.cell(60, 7, f"{num_cols[0]} (sum)", border=1, fill=True)
            pdf.ln()
            for _, row in grouped_pdf.iterrows():
                pdf.cell(90, 7, str(row[cat_cols[0]])[:40], border=1)
                pdf.cell(60, 7, f"{row[num_cols[0]]:,.1f}", border=1)
                pdf.ln()

        # Save and offer download
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            pdf.output(tmp.name)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            pdf_bytes = f.read()
        os.unlink(tmp_path)

        b64 = base64.b64encode(pdf_bytes).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="dashboard_report.pdf" style="background:#1f77b4;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:bold;">⬇️ Download PDF Report</a>'
        st.markdown(href, unsafe_allow_html=True)
        st.success("Report ready!")
