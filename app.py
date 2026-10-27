
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from pathlib import Path
from io import BytesIO

# =====================================================
# SALESVISION | UNIVERSAL DATA ANALYTICS DASHBOARD
# =====================================================

st.set_page_config(
    
# Dark green theme for input boxes and text
st.markdown("""
<style>
/* Main background and text */
.stApp {
    background-color: #102820;
    color: #E8F5E9;
}

/* Text inside input boxes */
.stTextInput input,
.stNumberInput input,
.stDateInput input,
.stSelectbox div[data-baseweb="select"],
.stMultiSelect div[data-baseweb="select"] {
    background-color: #1B4332 !important;
    color: #FFFFFF !important;
    border: 1px solid #40916C !important;
}

/* Date picker and calendar input */
[data-baseweb="datepicker"] input {
    background-color: #1B4332 !important;
    color: #FFFFFF !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background-color: #1B4332 !important;
    border: 1px solid #40916C !important;
    border-radius: 10px;
    padding: 12px;
    color: #FFFFFF !important;
}

/* General labels and text */
.stApp label,
.stApp p,
.stApp span {
    color: #E8F5E9;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #163A2D;
}
</style>
""", unsafe_allow_html=True)

    page_title="SalesVision | Smart Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).parent
DEFAULT_FILE = BASE_DIR / "salesvision_cleaned.csv"

# -------------------- THEME --------------------

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
    color: white;
}

.main-title {
    color: #173d30;
    font-size: 32px;
    font-weight: 700;
}

.subtitle {
    color: #64766a;
    margin-bottom: 20px;
}

.kpi-card {
    background: white;
    border-left: 5px solid #38765b;
    border-radius: 12px;
    padding: 17px;
    margin-bottom: 10px;
    min-height: 108px;
    box-shadow: 0 3px 12px rgba(30,70,50,0.08);
}

.kpi-label {
    color: #64766a;
    font-size: 12px;
    font-weight: 500;
}

.kpi-value {
    color: #173d30;
    font-size: 23px;
    font-weight: 700;
    margin-top: 8px;
    overflow-wrap: anywhere;
}

.section-title {
    color: #173d30;
    font-size: 21px;
    font-weight: 600;
    margin-top: 18px;
    margin-bottom: 8px;
}

.insight-card {
    background: #e6efe5;
    border-radius: 10px;
    padding: 15px;
    color: #173d30;
    margin-bottom: 8px;
}

div[data-testid="stPlotlyChart"] {
    background: white;
    border-radius: 12px;
    padding: 8px;
}

.stDownloadButton button {
    background: #245640;
    color: white;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)


# -------------------- HELPER FUNCTIONS --------------------

def clean_column_names(data):
    data = data.copy()
    data.columns = [
        str(c).strip() if str(c).strip() else f"Column_{i+1}"
        for i, c in enumerate(data.columns)
    ]
    return data


def find_column(data, possible_names):
    """Find a column using common name variations."""
    lookup = {str(c).strip().lower(): c for c in data.columns}

    for name in possible_names:
        if name.lower() in lookup:
            return lookup[name.lower()]

    # Try matching names that contain the requested term.
    for name in possible_names:
        for column in data.columns:
            if name.lower() in str(column).lower():
                return column

    return None


def detect_dates(data):
    """Identify date columns by name or successfully parsed values."""
    detected = []

    date_words = [
        "date", "time", "timestamp", "ordered", "created",
        "birth", "month", "year"
    ]

    for col in data.columns:
        name = str(col).lower()

        if pd.api.types.is_datetime64_any_dtype(data[col]):
            detected.append(col)
            continue

        if not any(word in name for word in date_words):
            continue

        parsed = pd.to_datetime(data[col], errors="coerce")

        if parsed.notna().mean() >= 0.70:
            data[col] = parsed
            detected.append(col)

    return detected


def format_number(value):
    if pd.isna(value):
        return "N/A"

    value = float(value)

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:,.2f}M"

    if abs(value) >= 10_000:
        return f"{value:,.0f}"

    return f"{value:,.2f}"


def make_chart(fig):
    fig.update_layout(
        template="plotly_white",
        font=dict(color="#173d30"),
        margin=dict(l=25, r=25, t=60, b=25),
        title_font_size=17,
        legend_title_text=""
    )
    return fig


# -------------------- HEADER --------------------

st.markdown(
    '<div class="main-title">📊 SalesVision Analytics</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Upload a dataset and automatically explore your data, '
    'visualizations and insights.'
    '</div>',
    unsafe_allow_html=True
)


# -------------------- SIDEBAR / UPLOAD --------------------

st.sidebar.markdown("# 🌿 SalesVision")
st.sidebar.markdown("### Smart Data Analytics")
st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader(
    "📂 Upload a CSV dataset",
    type=["csv"],
    help="Upload sales, student, finance, survey or other tabular data."
)

st.sidebar.caption(
    "No new file uploaded? The default dataset will be used."
)

# -------------------- LOAD DATA --------------------

try:
    if uploaded_file is not None:
        try:
            raw_df = pd.read_csv(
                BytesIO(uploaded_file.getvalue()),
                encoding="utf-8-sig"
            )
        except UnicodeDecodeError:
            raw_df = pd.read_csv(
                BytesIO(uploaded_file.getvalue()),
                encoding="latin1"
            )

        dataset_name = uploaded_file.name

    elif DEFAULT_FILE.exists():
        try:
            raw_df = pd.read_csv(DEFAULT_FILE, encoding="utf-8-sig")
        except UnicodeDecodeError:
            raw_df = pd.read_csv(DEFAULT_FILE, encoding="latin1")

        dataset_name = DEFAULT_FILE.name

    else:
        st.warning(
            "No dataset found. Upload a CSV file using the sidebar."
        )
        st.stop()

except Exception as error:
    st.error(f"Could not read this CSV file: {error}")
    st.stop()


if raw_df.empty:
    st.error("The uploaded dataset has no rows.")
    st.stop()

raw_df = clean_column_names(raw_df)

# Convert blank strings to missing values.
raw_df = raw_df.replace(r"^\s*$", np.nan, regex=True)

# Convert numeric-looking text columns when most values are numeric.
for col in raw_df.columns:
    if raw_df[col].dtype == "object":
        cleaned = (
            raw_df[col]
            .astype("string")
            .str.replace(",", "", regex=False)
            .str.replace("$", "", regex=False)
            .str.replace("£", "", regex=False)
            .str.replace("€", "", regex=False)
            .str.replace("%", "", regex=False)
            .str.strip()
        )

        converted = pd.to_numeric(cleaned, errors="coerce")

        if raw_df[col].notna().sum() > 0:
            numeric_ratio = (
                converted.notna().sum() / raw_df[col].notna().sum()
            )

            if numeric_ratio >= 0.85:
                raw_df[col] = converted

# Identify possible date columns.
date_columns = detect_dates(raw_df)

if raw_df.empty:
    st.error("No usable records were found.")
    st.stop()


# -------------------- DATASET SUMMARY --------------------

st.caption(f"📁 Active dataset: **{dataset_name}**")

rows_before = len(raw_df)
duplicate_count = int(raw_df.duplicated().sum())
missing_count = int(raw_df.isna().sum().sum())

with st.expander("🔍 Dataset information", expanded=False):
    info1, info2, info3 = st.columns(3)

    info1.metric("Rows", f"{len(raw_df):,}")
    info2.metric("Columns", f"{len(raw_df.columns):,}")
    info3.metric("Duplicate rows", f"{duplicate_count:,}")

    st.write("**Column types**")
    type_table = pd.DataFrame({
        "Column": raw_df.columns,
        "Data type": [str(raw_df[c].dtype) for c in raw_df.columns],
        "Missing values": [int(raw_df[c].isna().sum()) for c in raw_df.columns]
    })
    st.dataframe(type_table, use_container_width=True, hide_index=True)

# Allow filtering based on the uploaded dataset.
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔎 Filters")

filtered = raw_df.copy()

# Categorical filters.
categorical_columns = [
    c for c in raw_df.columns
    if c not in date_columns
    and (
        pd.api.types.is_object_dtype(raw_df[c])
        or isinstance(raw_df[c].dtype, pd.CategoricalDtype)
        or pd.api.types.is_bool_dtype(raw_df[c])
    )
    and 1 < raw_df[c].nunique(dropna=True) <= 100
]

if categorical_columns:
    filter_columns = st.sidebar.multiselect(
        "Choose categorical filters",
        options=categorical_columns,
        default=[
            c for c in categorical_columns
            if any(word in c.lower() for word in
                   ["region", "category", "segment", "department"])
        ][:3]
    )

    for col in filter_columns:
        values = sorted(
            raw_df[col].dropna().unique().tolist(),
            key=lambda x: str(x)
        )

        selected = st.sidebar.multiselect(
            f"Filter: {col}",
            options=values,
            default=values,
            key=f"filter_{col}"
        )

        filtered = filtered[filtered[col].isin(selected)]

# Date filter.
date_col = st.sidebar.selectbox(
    "Date column",
    options=["None"] + date_columns,
    index=1 if date_columns else 0
)

if date_col != "None":
    valid_dates = filtered[date_col].dropna()

    if not valid_dates.empty:
        min_date = valid_dates.min().date()
        max_date = valid_dates.max().date()

        date_range = st.sidebar.date_input(
            "Select date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key="date_filter"
        )

        if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
            start_date, end_date = date_range

            filtered = filtered[
                filtered[date_col].notna()
                & (filtered[date_col].dt.date >= start_date)
                & (filtered[date_col].dt.date <= end_date)
            ]

if filtered.empty:
    st.warning("No rows match the current filters. Change the filters.")
    st.stop()


# -------------------- DYNAMIC COLUMN DETECTION --------------------

numeric_columns = [
    c for c in filtered.columns
    if pd.api.types.is_numeric_dtype(filtered[c])
    and not pd.api.types.is_bool_dtype(filtered[c])
]

text_columns = [
    c for c in filtered.columns
    if c not in date_columns
    and c not in numeric_columns
    and filtered[c].nunique(dropna=True) > 1
]

sales_col = find_column(
    filtered,
    ["Sales", "Revenue", "Total Sales", "Amount", "Income"]
)

profit_col = find_column(
    filtered,
    ["Profit", "Net Profit", "Gross Profit", "Earnings"]
)

quantity_col = find_column(
    filtered,
    ["Quantity", "Qty", "Units Sold", "Units", "Count"]
)

order_col = find_column(
    filtered,
    ["Order ID", "Transaction ID", "Invoice ID", "Order Number"]
)

category_col = find_column(
    filtered,
    ["Category", "Product Category", "Department", "Type"]
)

region_col = find_column(
    filtered,
    ["Region", "Area", "Territory", "Location"]
)

subcategory_col = find_column(
    filtered,
    ["Sub-Category", "Subcategory", "Product", "Product Name", "Item"]
)


# -------------------- DYNAMIC KPI CARDS --------------------

st.markdown(
    '<div class="section-title">📌 Key Performance Indicators</div>',
    unsafe_allow_html=True
)

kpis = [
    ("📋 Total Records", f"{len(filtered):,}")
]

if sales_col and sales_col in numeric_columns:
    kpis.append((
        "💰 Total " + sales_col,
        format_number(filtered[sales_col].sum())
    ))

if profit_col and profit_col in numeric_columns:
    kpis.append((
        "📈 Total " + profit_col,
        format_number(filtered[profit_col].sum())
    ))

if quantity_col and quantity_col in numeric_columns:
    kpis.append((
        "📦 Total " + quantity_col,
        format_number(filtered[quantity_col].sum())
    ))

if order_col:
    kpis.append((
        "🧾 Unique Orders",
        f"{filtered[order_col].nunique():,}"
    ))

if (
    sales_col and profit_col
    and sales_col in numeric_columns
    and profit_col in numeric_columns
):
    total_sales = filtered[sales_col].sum()
    total_profit = filtered[profit_col].sum()

    margin = (
        total_profit / total_sales * 100
        if total_sales != 0 else np.nan
    )

    kpis.append((
        "🎯 Profit Margin",
        f"{margin:.2f}%" if pd.notna(margin) else "N/A"
    ))

# Generic numeric summaries if no recognized sales metrics exist.
if len(kpis) == 1:
    for col in numeric_columns[:4]:
        kpis.append((
            f"∑ {col}",
            format_number(filtered[col].sum())
        ))

for start in range(0, len(kpis), 4):
    group = kpis[start:start + 4]
    columns = st.columns(4)

    for container, (label, value) in zip(columns, group):
        with container:
            st.markdown(
                f'<div class="kpi-card">'
                f'<div class="kpi-label">{label}</div>'
                f'<div class="kpi-value">{value}</div>'
                f'</div>',
                unsafe_allow_html=True
            )


# -------------------- AUTOMATIC VISUALIZATIONS --------------------

st.markdown(
    '<div class="section-title">📊 Data Visualizations</div>',
    unsafe_allow_html=True
)

if not numeric_columns:
    st.info(
        "No numeric columns were detected. Upload data containing "
        "numeric values to generate numeric charts."
    )
else:
    chart1, chart2 = st.columns(2)

    # Numeric distribution.
    with chart1:
        selected_numeric = st.selectbox(
            "Numeric variable distribution",
            numeric_columns,
            key="distribution_column"
        )

        hist_data = filtered[[selected_numeric]].dropna()

        if not hist_data.empty:
            fig = px.histogram(
                hist_data,
                x=selected_numeric,
                nbins=30,
                title=f"Distribution of {selected_numeric}",
                color_discrete_sequence=["#38765b"]
            )
            st.plotly_chart(make_chart(fig), use_container_width=True)

    # Categorical comparison.
    with chart2:
        if text_columns:
            selected_category = st.selectbox(
                "Compare by category",
                text_columns,
                key="category_column"
            )

            selected_measure = st.selectbox(
                "Measure",
                numeric_columns,
                key="category_measure"
            )

            grouped = (
                filtered.groupby(selected_category, dropna=False)[selected_measure]
                .sum()
                .reset_index()
                .sort_values(selected_measure, ascending=False)
                .head(15)
            )

            grouped[selected_category] = (
                grouped[selected_category].astype(str)
            )

            fig = px.bar(
                grouped,
                x=selected_category,
                y=selected_measure,
                title=f"{selected_measure} by {selected_category}",
                color=selected_measure,
                color_continuous_scale=["#c9dfca", "#245640"]
            )
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(make_chart(fig), use_container_width=True)
        else:
            st.info("No categorical columns are available for comparison.")

    # Time trend.
    if date_columns:
        trend_col1, trend_col2 = st.columns(2)

        with trend_col1:
            selected_date = st.selectbox(
                "Trend date column",
                date_columns,
                key="trend_date"
            )

        with trend_col2:
            trend_measure = st.selectbox(
                "Trend measure",
                numeric_columns,
                key="trend_measure"
            )

        trend_data = filtered.dropna(
            subset=[selected_date, trend_measure]
        ).copy()

        if not trend_data.empty:
            trend_data["Period"] = (
                trend_data[selected_date].dt.to_period("M").astype(str)
            )

            trend = (
                trend_data.groupby("Period", as_index=False)[trend_measure]
                .sum()
                .sort_values("Period")
            )

            fig = px.line(
                trend,
                x="Period",
                y=trend_measure,
                markers=True,
                title=f"{trend_measure} Over Time",
                color_discrete_sequence=["#38765b"]
            )
            st.plotly_chart(make_chart(fig), use_container_width=True)

    # Correlation heatmap.
    if len(numeric_columns) >= 2:
        with st.expander("🔗 Numeric Correlation Analysis"):
            correlation = filtered[numeric_columns].corr()

            fig = px.imshow(
                correlation,
                text_auto=".2f",
                aspect="auto",
                color_continuous_scale="RdYlGn",
                zmin=-1,
                zmax=1,
                title="Correlation Between Numeric Variables"
            )
            st.plotly_chart(make_chart(fig), use_container_width=True)


# -------------------- AUTOMATIC INSIGHTS --------------------

st.markdown(
    '<div class="section-title">💡 Automatic Insights</div>',
    unsafe_allow_html=True
)

insights = []

insights.append(
    f"The filtered dataset contains {len(filtered):,} records "
    f"and {len(filtered.columns)} columns."
)

if duplicate_count > 0:
    insights.append(
        f"The original dataset contains {duplicate_count:,} duplicate rows. "
        "Review them before removing any records."
    )

if missing_count > 0:
    insights.append(
        f"The original dataset contains {missing_count:,} missing cell values. "
        "Check the data-quality section below."
    )
else:
    insights.append("No missing values were found in the original dataset.")

if sales_col and sales_col in numeric_columns:
    insights.append(
        f"Total {sales_col.lower()} for the selected data: "
        f"{format_number(filtered[sales_col].sum())}."
    )

if profit_col and profit_col in numeric_columns:
    total_profit = filtered[profit_col].sum()

    if total_profit > 0:
        insights.append(
            f"Total {profit_col.lower()} is positive: "
            f"{format_number(total_profit)}."
        )
    elif total_profit < 0:
        insights.append(
            f"Total {profit_col.lower()} is negative: "
            f"{format_number(total_profit)}. Investigate potential losses."
        )
    else:
        insights.append(f"Total {profit_col.lower()} is zero.")

if category_col and category_col in filtered.columns:
    category_measure = (
        sales_col if sales_col in numeric_columns
        else numeric_columns[0] if numeric_columns
        else None
    )

    if category_measure:
        totals = filtered.groupby(category_col)[category_measure].sum()

        if not totals.empty:
            best = totals.idxmax()
            worst = totals.idxmin()

            insights.append(
                f"Highest {category_measure} by {category_col}: "
                f"{best} ({format_number(totals.max())})."
            )

            if best != worst:
                insights.append(
                    f"Lowest {category_measure} by {category_col}: "
                    f"{worst} ({format_number(totals.min())})."
                )

if numeric_columns:
    for col in numeric_columns[:3]:
        values = filtered[col].dropna()

        if not values.empty:
            insights.append(
                f"{col}: average {format_number(values.mean())}; "
                f"minimum {format_number(values.min())}; "
                f"maximum {format_number(values.max())}."
            )

for insight in insights:
    st.markdown(
        f'<div class="insight-card">💡 {insight}</div>',
        unsafe_allow_html=True
    )


# -------------------- DATA QUALITY --------------------

st.markdown(
    '<div class="section-title">🧹 Data Quality</div>',
    unsafe_allow_html=True
)

quality = pd.DataFrame({
    "Column": raw_df.columns,
    "Missing Values": [int(raw_df[c].isna().sum()) for c in raw_df.columns],
    "Missing (%)": [
        round(raw_df[c].isna().mean() * 100, 2)
        for c in raw_df.columns
    ],
    "Unique Values": [
        int(raw_df[c].nunique(dropna=True)) for c in raw_df.columns
    ],
    "Data Type": [str(raw_df[c].dtype) for c in raw_df.columns]
})

st.dataframe(quality, use_container_width=True, hide_index=True)

# -------------------- DATA TABLE / DOWNLOAD --------------------

st.markdown(
    '<div class="section-title">📋 Explore Your Data</div>',
    unsafe_allow_html=True
)

st.caption(f"Showing {len(filtered):,} filtered records.")

st.dataframe(
    filtered,
    use_container_width=True,
    hide_index=True
)

csv_data = filtered.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    "⬇️ Download Filtered Dataset",
    data=csv_data,
    file_name="salesvision_filtered_data.csv",
    mime="text/csv"
)

st.markdown("---")
st.caption(
    "SalesVision Analytics | Universal CSV Analytics | "
    "Built with Python, Pandas, Plotly and Streamlit"
)
