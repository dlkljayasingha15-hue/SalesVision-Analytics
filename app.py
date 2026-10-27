import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="SalesVision Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)
DATA_PATH = Path(__file__).parent / "salesvision_cleaned.csv"

# ---------------- THEME ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}

.stApp {
    background-color: #f4f7f0;
}

[data-testid="stSidebar"] {
    background-color: #173d30;
}

[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

.main-title {
    color: #173d30;
    font-size: 34px;
    font-weight: 700;
}

.subtitle {
    color: #60756a;
    font-size: 14px;
    margin-bottom: 22px;
}

.kpi-card {
    background: #ffffff;
    border-left: 5px solid #38765b;
    padding: 20px;
    border-radius: 12px;
    box-shadow: 0 3px 12px rgba(30, 70, 50, 0.08);
    min-height: 115px;
}

.kpi-label {
    color: #60756a;
    font-size: 13px;
    font-weight: 500;
}

.kpi-value {
    color: #173d30;
    font-size: 25px;
    font-weight: 700;
    margin-top: 8px;
}

.section-title {
    color: #173d30;
    font-size: 21px;
    font-weight: 600;
    margin-top: 10px;
}

.insight-card {
    background: #e6efe5;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 10px;
    color: #173d30;
}

div[data-testid="stMetric"] {
    background: #ffffff;
    padding: 16px;
    border-radius: 10px;
}

.stDownloadButton button {
    background-color: #245640;
    color: white;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_data():
    data = pd.read_csv(DATA_PATH)
    data["Order Date"] = pd.to_datetime(
        data["Order Date"], errors="coerce"
    )

    for col in ["Sales", "Profit", "Quantity"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.dropna(
        subset=["Order Date", "Sales", "Profit", "Quantity"]
    )

    if "Year_Month" not in data.columns:
        data["Year_Month"] = (
            data["Order Date"].dt.to_period("M").astype(str)
        )

    return data

if not DATA_PATH.exists():
    st.error("Dataset not found. Please upload and clean the CSV in Colab first.")
    st.stop()

df = load_data()

# ---------------- SIDEBAR ----------------
st.sidebar.markdown("# 🌿 SalesVision")
st.sidebar.markdown("### Analytics Dashboard")
st.sidebar.markdown("---")
st.sidebar.write("Explore your business performance.")
st.sidebar.markdown("### 🔎 Filters")

regions = sorted(df["Region"].dropna().unique().tolist())
categories = sorted(df["Category"].dropna().unique().tolist())

selected_regions = st.sidebar.multiselect(
    "Select Region",
    regions,
    default=regions
)

selected_categories = st.sidebar.multiselect(
    "Select Category",
    categories,
    default=categories
)

min_date = df["Order Date"].min().date()
max_date = df["Order Date"].max().date()

date_range = st.sidebar.date_input(
    "Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range[0]

filtered = df[
    df["Region"].isin(selected_regions)
    & df["Category"].isin(selected_categories)
    & (df["Order Date"].dt.date >= start_date)
    & (df["Order Date"].dt.date <= end_date)
].copy()

# ---------------- HEADER ----------------
st.markdown(
    '<div class="main-title">📊 SalesVision Analytics Dashboard</div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="subtitle">Monitor sales, profit and business performance in one place.</div>',
    unsafe_allow_html=True
)

if filtered.empty:
    st.warning("No records match the selected filters. Please change your filters.")
    st.stop()

# ---------------- KPIs ----------------
total_sales = filtered["Sales"].sum()
total_profit = filtered["Profit"].sum()
total_quantity = filtered["Quantity"].sum()
total_orders = (
    filtered["Order ID"].nunique()
    if "Order ID" in filtered.columns
    else len(filtered)
)
profit_margin = (
    total_profit / total_sales * 100 if total_sales else 0
)

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-label">💰 TOTAL SALES</div>'
        f'<div class="kpi-value">${total_sales:,.2f}</div></div>',
        unsafe_allow_html=True
    )

with k2:
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-label">📈 TOTAL PROFIT</div>'
        f'<div class="kpi-value">${total_profit:,.2f}</div></div>',
        unsafe_allow_html=True
    )

with k3:
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-label">📦 QUANTITY SOLD</div>'
        f'<div class="kpi-value">{total_quantity:,.0f}</div></div>',
        unsafe_allow_html=True
    )

with k4:
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-label">🎯 PROFIT MARGIN</div>'
        f'<div class="kpi-value">{profit_margin:.2f}%</div></div>',
        unsafe_allow_html=True
    )

st.write("")

# ---------------- CHARTS ----------------
st.markdown(
    '<div class="section-title">Sales Performance</div>',
    unsafe_allow_html=True
)

left, right = st.columns(2)

with left:
    monthly = (
        filtered.groupby("Year_Month", as_index=False)["Sales"]
        .sum()
        .sort_values("Year_Month")
    )

    fig_monthly = px.line(
        monthly,
        x="Year_Month",
        y="Sales",
        markers=True,
        title="Monthly Sales Trend",
        labels={"Year_Month": "Month", "Sales": "Sales ($)"}
    )
    fig_monthly.update_traces(
        line=dict(color="#38765b", width=3),
        marker=dict(size=7)
    )
    fig_monthly.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_color="#173d30",
        margin=dict(l=20, r=20, t=55, b=20)
    )
    st.plotly_chart(fig_monthly, use_container_width=True)

with right:
    category_sales = (
        filtered.groupby("Category", as_index=False)["Sales"]
        .sum()
        .sort_values("Sales", ascending=False)
    )

    fig_category = px.bar(
        category_sales,
        x="Category",
        y="Sales",
        title="Sales by Category",
        color="Sales",
        color_continuous_scale=["#c9dfca", "#245640"],
        labels={"Sales": "Sales ($)"}
    )
    fig_category.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_color="#173d30",
        showlegend=False,
        coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=55, b=20)
    )
    st.plotly_chart(fig_category, use_container_width=True)

left2, right2 = st.columns(2)

with left2:
    region_data = (
        filtered.groupby("Region", as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
    )

    fig_region = px.bar(
        region_data,
        x="Region",
        y="Sales",
        title="Sales by Region",
        color="Region",
        color_discrete_sequence=[
            "#245640", "#4c8767", "#8bb89a", "#b8d5bd"
        ],
        labels={"Sales": "Sales ($)"}
    )
    fig_region.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_color="#173d30",
        showlegend=False,
        margin=dict(l=20, r=20, t=55, b=20)
    )
    st.plotly_chart(fig_region, use_container_width=True)

with right2:
    subcategory_profit = (
        filtered.groupby("Sub-Category", as_index=False)["Profit"]
        .sum()
        .sort_values("Profit", ascending=True)
    )

    fig_profit = px.bar(
        subcategory_profit,
        x="Profit",
        y="Sub-Category",
        orientation="h",
        title="Profit by Sub-Category",
        color="Profit",
        color_continuous_scale=["#bd6b60", "#f2f2e8", "#38765b"],
        labels={"Profit": "Profit ($)"}
    )
    fig_profit.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_color="#173d30",
        showlegend=False,
        coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=55, b=20)
    )
    st.plotly_chart(fig_profit, use_container_width=True)

# ---------------- BUSINESS INSIGHTS ----------------
st.markdown(
    '<div class="section-title">💡 Business Insights</div>',
    unsafe_allow_html=True
)

best_category = (
    filtered.groupby("Category")["Profit"].sum().idxmax()
    if not filtered.empty else "N/A"
)

best_region = (
    filtered.groupby("Region")["Profit"].sum().idxmax()
    if not filtered.empty else "N/A"
)

worst_subcategory = (
    filtered.groupby("Sub-Category")["Profit"].sum().idxmin()
    if not filtered.empty else "N/A"
)

ins1, ins2, ins3 = st.columns(3)

with ins1:
    st.markdown(
        f'<div class="insight-card"><b>🏆 Most Profitable Category</b><br>'
        f'{best_category}</div>',
        unsafe_allow_html=True
    )

with ins2:
    st.markdown(
        f'<div class="insight-card"><b>🌍 Best Region by Profit</b><br>'
        f'{best_region}</div>',
        unsafe_allow_html=True
    )

with ins3:
    st.markdown(
        f'<div class="insight-card"><b>⚠️ Lowest Profit Subcategory</b><br>'
        f'{worst_subcategory}</div>',
        unsafe_allow_html=True
    )

# ---------------- DATA TABLE ----------------
st.markdown(
    '<div class="section-title">📋 Detailed Sales Data</div>',
    unsafe_allow_html=True
)

st.caption(f"Showing {len(filtered):,} records matching your filters.")

st.dataframe(
    filtered,
    use_container_width=True,
    hide_index=True
)

csv_download = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Download Filtered Data as CSV",
    data=csv_download,
    file_name="salesvision_filtered_data.csv",
    mime="text/csv"
)

st.markdown("---")
st.caption("SalesVision Analytics | Built with Python, Pandas, Plotly and Streamlit")
