
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
from io import BytesIO

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="SalesVision | Smart Data Analytics",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_FILE = BASE_DIR / "salesvision_cleaned.csv"

# --------------------------------------------------
# DARK GREEN THEME
# --------------------------------------------------
st.markdown("""
<style>
.stApp {
    background-color: #102820;
    color: #E8F5E9;
}

[data-testid="stHeader"] {
    background-color: #102820;
}

[data-testid="stSidebar"] {
    background-color: #163A2D;
}

.stApp h1, .stApp h2, .stApp h3, .stApp h4 {
    color: #B7E4C7 !important;
}

.stApp p, .stApp label, .stApp small {
    color: #E8F5E9;
}

[data-testid="stMetric"] {
    background-color: #1B4332;
    border: 1px solid #40916C;
    padding: 18px;
    border-radius: 12px;
}

[data-testid="stMetricLabel"] {
    color: #B7E4C7 !important;
}

[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
}

.stTextInput input,
.stNumberInput input,
.stDateInput input,
.stSelectbox div[data-baseweb="select"],
.stMultiSelect div[data-baseweb="select"] {
    background-color: #1B4332 !important;
    color: #FFFFFF !important;
    border-color: #40916C !important;
}

[data-testid="stFileUploader"] {
    background-color: #1B4332;
    border: 1px solid #40916C;
    border-radius: 12px;
    padding: 14px;
}

[data-testid="stFileUploader"] *,
[data-testid="stFileUploaderDropzone"] * {
    color: #FFFFFF !important;
}

[data-testid="stDateInput"] input {
    background-color: #1B4332 !important;
    color: #FFFFFF !important;
    border: 1px solid #40916C !important;
}

.stButton button,
.stDownloadButton button {
    background-color: #2D6A4F;
    color: #FFFFFF;
    border: 1px solid #52B788;
    border-radius: 8px;
}

.stButton button:hover,
.stDownloadButton button:hover {
    background-color: #40916C;
    color: #FFFFFF;
    border-color: #B7E4C7;
}

[data-testid="stDataFrame"],
[data-testid="stTable"] {
    border: 1px solid #40916C;
    border-radius: 8px;
}

hr {
    border-color: #40916C;
}

div[data-testid="stAlert"] {
    background-color: #1B4332;
    color: #FFFFFF;
}

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------
def find_column(columns, keywords):
    """Find a column by checking common names."""
    normalized = {
        str(col).strip().lower().replace("_", " ").replace("-", " "): col
        for col in columns
    }

    for keyword in keywords:
        key = keyword.lower().replace("_", " ").replace("-", " ")
        if key in normalized:
            return normalized[key]

    for col in columns:
        col_name = str(col).lower().replace("_", " ").replace("-", " ")
        for keyword in keywords:
            key = keyword.lower().replace("_", " ").replace("-", " ")
            if key in col_name:
                return col

    return None


def detect_date_columns(df):
    """Detect actual date columns while avoiding numeric columns."""
    date_cols = []

    date_words = [
        "date", "day", "timestamp", "datetime",
        "joined", "joining", "order date", "birth date"
    ]

    for col in df.columns:
        series = df[col]

        # Never treat numeric data as dates
        if pd.api.types.is_numeric_dtype(series):
            continue

        name = str(col).lower().replace("_", " ").replace("-", " ")
        has_date_name = any(word in name for word in date_words)

        if not (
            pd.api.types.is_datetime64_any_dtype(series)
            or has_date_name
        ):
            continue

        parsed = pd.to_datetime(series, errors="coerce")
        non_empty = series.notna().sum()

        if non_empty == 0:
            continue

        success_ratio = parsed.notna().sum() / non_empty

        if success_ratio >= 0.60:
            df[col] = parsed
            date_cols.append(col)

    return date_cols


def detect_numeric_columns(df, date_cols):
    numeric_cols = []

    for col in df.columns:
        if col in date_cols:
            continue

        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_cols.append(col)

    return numeric_cols


def detect_category_columns(df, numeric_cols, date_cols):
    category_cols = []

    for col in df.columns:
        if col in numeric_cols or col in date_cols:
            continue

        if df[col].nunique(dropna=True) <= 100:
            category_cols.append(col)

    return category_cols


def format_number(value):
    if pd.isna(value):
        return "N/A"

    value = float(value)

    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.2f}K"

    return f"{value:,.2f}"


def style_chart(fig):
    fig.update_layout(
        paper_bgcolor="#163A2D",
        plot_bgcolor="#163A2D",
        font=dict(color="#E8F5E9"),
        title_font=dict(color="#B7E4C7"),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#E8F5E9")
        ),
        margin=dict(l=20, r=20, t=60, b=30)
    )
    fig.update_xaxes(
        gridcolor="#315B48",
        zerolinecolor="#40916C"
    )
    fig.update_yaxes(
        gridcolor="#315B48",
        zerolinecolor="#40916C"
    )
    return fig


# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.title("🌿 SalesVision")
st.subheader("Smart Data Analytics")
st.caption(
    "Upload a CSV dataset to automatically explore data, "
    "visualizations and insights."
)

# --------------------------------------------------
# SIDEBAR: UPLOAD
# --------------------------------------------------
st.sidebar.title("📂 Dataset")
uploaded_file = st.sidebar.file_uploader(
    "Upload a CSV dataset",
    type=["csv"],
    help="Upload a CSV file up to the file size limit shown here."
)

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
try:
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        dataset_name = uploaded_file.name
    elif DEFAULT_FILE.exists():
        df = pd.read_csv(DEFAULT_FILE)
        dataset_name = DEFAULT_FILE.name
    else:
        st.warning(
            "No default dataset was found. Please upload a CSV file."
        )
        st.stop()

except Exception as error:
    st.error(f"Unable to read this CSV file: {error}")
    st.info(
        "Please upload a valid CSV file encoded in UTF-8 if possible."
    )
    st.stop()

if df.empty:
    st.error("The selected dataset is empty.")
    st.stop()

# Clean column names and remove completely empty rows/columns
df.columns = [
    str(col).strip() if str(col).strip() else f"Column_{i + 1}"
    for i, col in enumerate(df.columns)
]
df = df.dropna(how="all").dropna(axis=1, how="all")

if df.empty or len(df.columns) == 0:
    st.error("No usable data was found in this CSV file.")
    st.stop()

# --------------------------------------------------
# DETECT DATA TYPES
# --------------------------------------------------
date_cols = detect_date_columns(df)
numeric_cols = detect_numeric_columns(df, date_cols)
category_cols = detect_category_columns(df, numeric_cols, date_cols)

sales_col = find_column(
    numeric_cols,
    ["Sales", "Revenue", "Amount", "Total Sales", "Income", "Salary"]
)

profit_col = find_column(
    numeric_cols,
    ["Profit", "Net Profit", "Earnings", "Net Income"]
)

quantity_col = find_column(
    numeric_cols,
    ["Quantity", "Qty", "Units", "Count"]
)

# --------------------------------------------------
# SIDEBAR: FILTERS
# --------------------------------------------------
st.sidebar.divider()
st.sidebar.header("🔎 Filters")

filtered_df = df.copy()

# Date filter
if date_cols:
    selected_date_col = st.sidebar.selectbox(
        "Date column",
        options=date_cols
    )

    valid_dates = filtered_df[selected_date_col].dropna()

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

            filtered_df = filtered_df[
                filtered_df[selected_date_col].notna()
                & (filtered_df[selected_date_col].dt.date >= start_date)
                & (filtered_df[selected_date_col].dt.date <= end_date)
            ]
else:
    st.sidebar.info("No date column detected in this dataset.")

# Category filters
if category_cols:
    with st.sidebar.expander("Category filters", expanded=False):
        for col in category_cols:
            choices = sorted(
                filtered_df[col].dropna().astype(str).unique().tolist()
            )

            if 0 < len(choices) <= 50:
                selected_values = st.multiselect(
                    f"Filter by {col}",
                    options=choices,
                    default=choices,
                    key=f"filter_{col}"
                )

                if selected_values:
                    filtered_df = filtered_df[
                        filtered_df[col].astype(str).isin(selected_values)
                    ]
                else:
                    filtered_df = filtered_df.iloc[0:0]

# Dataset info
st.sidebar.divider()
st.sidebar.caption(f"📁 Active dataset: {dataset_name}")
st.sidebar.caption(f"Rows: {len(df):,}")
st.sidebar.caption(f"Columns: {len(df.columns):,}")

# --------------------------------------------------
# MAIN DATASET INFORMATION
# --------------------------------------------------
st.markdown("---")
st.subheader("🔍 Dataset Information")

info1, info2, info3 = st.columns(3)
info1.metric("📋 Total Records", f"{len(filtered_df):,}")
info2.metric("📑 Total Columns", f"{len(filtered_df.columns):,}")
info3.metric("🔢 Numeric Columns", f"{len(numeric_cols):,}")

if filtered_df.empty:
    st.warning("No records match the selected filters.")
    st.stop()

with st.expander("View detected column types"):
    st.write("**Date columns:**", date_cols or "None detected")
    st.write("**Numeric columns:**", numeric_cols or "None detected")
    st.write("**Category columns:**", category_cols or "None detected")

# --------------------------------------------------
# KEY PERFORMANCE INDICATORS
# --------------------------------------------------
st.markdown("---")
st.subheader("📌 Key Performance Indicators")

kpi_cols = st.columns(5)

kpi_cols[0].metric(
    "📋 Total Records",
    f"{len(filtered_df):,}"
)

if sales_col and sales_col in filtered_df.columns:
    kpi_cols[1].metric(
        f"💰 Total {sales_col}",
        format_number(filtered_df[sales_col].sum())
    )
elif numeric_cols:
    first_numeric = numeric_cols[0]
    kpi_cols[1].metric(
        f"Σ {first_numeric}",
        format_number(filtered_df[first_numeric].sum())
    )
else:
    kpi_cols[1].metric("💰 Numeric Total", "N/A")

if profit_col and profit_col in filtered_df.columns:
    kpi_cols[2].metric(
        f"📈 Total {profit_col}",
        format_number(filtered_df[profit_col].sum())
    )
elif len(numeric_cols) > 1:
    second_numeric = numeric_cols[1]
    kpi_cols[2].metric(
        f"📊 Avg. {second_numeric}",
        format_number(filtered_df[second_numeric].mean())
    )
else:
    kpi_cols[2].metric("📈 Secondary Metric", "N/A")

if quantity_col and quantity_col in filtered_df.columns:
    kpi_cols[3].metric(
        f"📦 Total {quantity_col}",
        format_number(filtered_df[quantity_col].sum())
    )
elif numeric_cols:
    first_numeric = numeric_cols[0]
    kpi_cols[3].metric(
        f"📊 Avg. {first_numeric}",
        format_number(filtered_df[first_numeric].mean())
    )
else:
    kpi_cols[3].metric("📊 Average", "N/A")

if (
    sales_col and profit_col
    and sales_col in filtered_df.columns
    and profit_col in filtered_df.columns
):
    total_sales = filtered_df[sales_col].sum()
    total_profit = filtered_df[profit_col].sum()

    margin = (
        (total_profit / total_sales) * 100
        if total_sales != 0 else 0
    )
    kpi_cols[4].metric("🎯 Profit Margin", f"{margin:.2f}%")
elif numeric_cols:
    first_numeric = numeric_cols[0]
    kpi_cols[4].metric(
        f"⬆️ Max {first_numeric}",
        format_number(filtered_df[first_numeric].max())
    )
else:
    kpi_cols[4].metric("🎯 Max Value", "N/A")

# --------------------------------------------------
# VISUALIZATIONS
# --------------------------------------------------
st.markdown("---")
st.subheader("📊 Data Visualizations")

chart_left, chart_right = st.columns(2)

# Numeric distribution
with chart_left:
    st.markdown("#### Numeric variable distribution")

    if numeric_cols:
        distribution_col = st.selectbox(
            "Choose numeric variable",
            numeric_cols,
            key="distribution_col"
        )

        values = filtered_df[distribution_col].dropna()

        if not values.empty:
            fig = px.histogram(
                x=values,
                nbins=30,
                title=f"Distribution of {distribution_col}",
                labels={"x": distribution_col, "y": "Frequency"}
            )
            st.plotly_chart(style_chart(fig), use_container_width=True)
        else:
            st.info("No numeric values are available for this chart.")
    else:
        st.info("No numeric columns were detected.")

# Category comparison
with chart_right:
    st.markdown("#### Compare by category")

    if category_cols and numeric_cols:
        comparison_category = st.selectbox(
            "Category",
            category_cols,
            key="comparison_category"
        )

        default_measure = (
            sales_col if sales_col in numeric_cols else numeric_cols[0]
        )

        comparison_measure = st.selectbox(
            "Measure",
            numeric_cols,
            index=numeric_cols.index(default_measure),
            key="comparison_measure"
        )

        comparison_data = filtered_df[
            [comparison_category, comparison_measure]
        ].dropna()

        if not comparison_data.empty:
            comparison_data = (
                comparison_data
                .groupby(comparison_category, as_index=False)[comparison_measure]
                .sum()
                .sort_values(comparison_measure, ascending=False)
                .head(20)
            )

            fig = px.bar(
                comparison_data,
                x=comparison_category,
                y=comparison_measure,
                title=f"{comparison_measure} by {comparison_category}",
                color=comparison_measure
            )
            st.plotly_chart(style_chart(fig), use_container_width=True)
        else:
            st.info("No data is available for this comparison.")
    else:
        st.info("A category column and a numeric column are needed.")

# Date trend
st.markdown("#### 📅 Trend over time")

if date_cols and numeric_cols:
    trend_left, trend_right = st.columns(2)

    with trend_left:
        trend_date_col = st.selectbox(
            "Trend date column",
            date_cols,
            key="trend_date_col"
        )

    with trend_right:
        trend_measure = st.selectbox(
            "Trend measure",
            numeric_cols,
            key="trend_measure"
        )

    trend_data = filtered_df[
        [trend_date_col, trend_measure]
    ].dropna().copy()

    if not trend_data.empty:
        trend_data["_period"] = trend_data[trend_date_col].dt.to_period("M").dt.to_timestamp()

        trend_data = (
            trend_data
            .groupby("_period", as_index=False)[trend_measure]
            .sum()
            .sort_values("_period")
        )

        fig = px.line(
            trend_data,
            x="_period",
            y=trend_measure,
            markers=True,
            title=f"{trend_measure} over time"
        )
        fig.update_xaxes(title="Date")
        fig.update_yaxes(title=trend_measure)
        st.plotly_chart(style_chart(fig), use_container_width=True)
    else:
        st.info("No valid dates or numeric values are available.")
else:
    st.info("A date column and a numeric column are needed for trend analysis.")

# Correlation analysis
st.markdown("---")
st.subheader("🔗 Numeric Correlation Analysis")

if len(numeric_cols) >= 2:
    corr_data = filtered_df[numeric_cols].corr(numeric_only=True)

    if not corr_data.empty:
        fig = px.imshow(
            corr_data,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="RdYlGn",
            zmin=-1,
            zmax=1,
            title="Correlation heatmap"
        )
        st.plotly_chart(style_chart(fig), use_container_width=True)
    else:
        st.info("Unable to calculate correlations for this data.")
else:
    st.info("At least two numeric columns are needed for correlation analysis.")

# --------------------------------------------------
# AUTOMATIC INSIGHTS
# --------------------------------------------------
st.markdown("---")
st.subheader("💡 Automatic Insights")

st.info(
    f"The filtered dataset contains {len(filtered_df):,} records "
    f"and {len(filtered_df.columns):,} columns."
)

missing_original = int(df.isna().sum().sum())
missing_filtered = int(filtered_df.isna().sum().sum())

if missing_original == 0:
    st.success("No missing values were found in the original dataset.")
else:
    st.warning(
        f"The original dataset contains {missing_original:,} missing values."
    )

if missing_filtered > 0:
    st.write(
        f"💡 The filtered data contains {missing_filtered:,} missing cells."
    )

if sales_col and sales_col in filtered_df.columns:
    st.write(
        f"💡 Total {sales_col}: "
        f"{format_number(filtered_df[sales_col].sum())}."
    )

if profit_col and profit_col in filtered_df.columns:
    profit_total = filtered_df[profit_col].sum()
    if profit_total >= 0:
        st.write(
            f"💡 Total {profit_col} is positive: "
            f"{format_number(profit_total)}."
        )
    else:
        st.write(
            f"⚠️ Total {profit_col} is negative: "
            f"{format_number(profit_total)}."
        )

if category_cols and numeric_cols:
    insight_category = (
        find_column(category_cols, ["Category", "Department", "Region", "City"])
        or category_cols[0]
    )
    insight_measure = sales_col if sales_col in numeric_cols else numeric_cols[0]

    insight_data = filtered_df[
        [insight_category, insight_measure]
    ].dropna()

    if not insight_data.empty:
        grouped = (
            insight_data
            .groupby(insight_category)[insight_measure]
            .sum()
            .sort_values(ascending=False)
        )

        if not grouped.empty:
            st.write(
                f"💡 Highest {insight_measure} by {insight_category}: "
                f"{grouped.index[0]} ({format_number(grouped.iloc[0])})."
            )
            st.write(
                f"💡 Lowest {insight_measure} by {insight_category}: "
                f"{grouped.index[-1]} ({format_number(grouped.iloc[-1])})."
            )

for col in numeric_cols[:5]:
    values = filtered_df[col].dropna()

    if not values.empty:
        st.write(
            f"💡 **{col}:** average {format_number(values.mean())}; "
            f"minimum {format_number(values.min())}; "
            f"maximum {format_number(values.max())}."
        )

# --------------------------------------------------
# DATA QUALITY
# --------------------------------------------------
st.markdown("---")
st.subheader("🧹 Data Quality")

quality_data = pd.DataFrame({
    "Column": df.columns,
    "Data Type": [str(df[col].dtype) for col in df.columns],
    "Missing Values": [int(df[col].isna().sum()) for col in df.columns],
    "Missing (%)": [
        round(float(df[col].isna().mean() * 100), 2)
        for col in df.columns
    ],
    "Unique Values": [int(df[col].nunique(dropna=True)) for col in df.columns]
})

st.dataframe(quality_data, use_container_width=True, hide_index=True)

duplicate_count = int(df.duplicated().sum())
st.write(f"🔁 Duplicate rows: **{duplicate_count:,}**")

# --------------------------------------------------
# DATA EXPLORER AND DOWNLOAD
# --------------------------------------------------
st.markdown("---")
st.subheader("📋 Explore Your Data")

st.caption(f"Showing {len(filtered_df):,} filtered records.")

st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)

csv_data = filtered_df.to_csv(index=False).encode("utf-8-sig")

st.download_button(
    label="📥 Download filtered data as CSV",
    data=csv_data,
    file_name="salesvision_filtered_data.csv",
    mime="text/csv"
)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("---")
st.caption(
    "SalesVision Analytics | Universal CSV Analytics | "
    "Built with Python, Pandas, Plotly and Streamlit"
)
