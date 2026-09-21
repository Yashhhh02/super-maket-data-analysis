"""
app_combined.py  –  Supermarket Sales Analysis Dashboard
=========================================================
Single-file version — frontend + backend all in one.
Run:  streamlit run supermarket_analysis/app_combined.py
"""

import os
import tempfile
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# ██████╗  █████╗  ██████╗██╗  ██╗███████╗███╗   ██╗██████╗
# ██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔════╝████╗  ██║██╔══██╗
# ██████╔╝███████║██║     █████╔╝ █████╗  ██╔██╗ ██║██║  ██║
# ██╔══██╗██╔══██║██║     ██╔═██╗ ██╔══╝  ██║╚██╗██║██║  ██║
# ██████╔╝██║  ██║╚██████╗██║  ██╗███████╗██║ ╚████║██████╔╝
# BACKEND — Data Loading, Cleaning & Analytics
# ============================================================

REQUIRED_COLUMNS = {
    "InvoiceNo", "StockCode", "Description",
    "Quantity", "InvoiceDate", "UnitPrice",
    "CustomerID", "Country",
}


# ------------------------------------------------------------------
# Step 1 & 2 — Load CSV and build quality report
# ------------------------------------------------------------------
def load_and_clean(filepath: str) -> tuple[pd.DataFrame, dict]:
    """Load the CSV, generate a quality report, clean it, compute Sales."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found: {filepath}")

    raw_df = pd.read_csv(
        filepath,
        dtype={"CustomerID": str},
        low_memory=False,
        encoding="latin-1",   # handles £ and other Windows-1252 chars
    )

    quality_report = _build_quality_report(raw_df)
    cleaned_df = _clean(raw_df)
    return cleaned_df, quality_report


def _build_quality_report(df: pd.DataFrame) -> dict:
    """Inspect the raw dataframe and collect quality metrics."""
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    duplicates = int(df.duplicated().sum())
    neg_qty = int((pd.to_numeric(df["Quantity"], errors="coerce") < 0).sum())
    neg_price = int((pd.to_numeric(df["UnitPrice"], errors="coerce") < 0).sum())
    zero_price = int((pd.to_numeric(df["UnitPrice"], errors="coerce") == 0).sum())
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    return {
        "total_raw_rows": len(df),
        "total_columns": len(df.columns),
        "missing_values": missing.to_dict(),
        "missing_pct": missing_pct.to_dict(),
        "duplicate_rows": duplicates,
        "negative_quantity_rows": neg_qty,
        "negative_price_rows": neg_price,
        "zero_price_rows": zero_price,
        "missing_required_columns": missing_cols,
    }


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the raw dataframe — remove bad rows and derive new columns."""
    df = df.copy()

    # Coerce numeric columns
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")

    # Drop rows with missing key fields
    df.dropna(subset=["Description", "Quantity", "UnitPrice"], inplace=True)

    # Remove cancellations (InvoiceNo starts with 'C')
    df = df[~df["InvoiceNo"].astype(str).str.startswith("C")]

    # Remove returns and zero-price rows
    df = df[df["Quantity"] > 0]
    df = df[df["UnitPrice"] > 0]

    # Drop exact duplicates
    df.drop_duplicates(inplace=True)

    # Parse dates
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    df.dropna(subset=["InvoiceDate"], inplace=True)

    # Derive time columns
    df["Year"]      = df["InvoiceDate"].dt.year
    df["Month"]     = df["InvoiceDate"].dt.month
    df["MonthName"] = df["InvoiceDate"].dt.strftime("%b %Y")
    df["DayOfWeek"] = df["InvoiceDate"].dt.day_name()
    df["Hour"]      = df["InvoiceDate"].dt.hour

    # Step 3 — Calculate Sales
    df["Sales"] = (df["Quantity"] * df["UnitPrice"]).round(2)

    df.reset_index(drop=True, inplace=True)
    return df


# ------------------------------------------------------------------
# Step 4 — Group & Summarise (Analytics Functions)
# ------------------------------------------------------------------

def overall_kpis(df: pd.DataFrame) -> dict:
    """Top-level business KPIs."""
    return {
        "total_sales":         round(df["Sales"].sum(), 2),
        "total_orders":        df["InvoiceNo"].nunique(),
        "total_customers":     df["CustomerID"].nunique(),
        "total_products":      df["StockCode"].nunique(),
        "avg_order_value":     round(df.groupby("InvoiceNo")["Sales"].sum().mean(), 2),
        "avg_unit_price":      round(df["UnitPrice"].mean(), 2),
        "total_quantity_sold": int(df["Quantity"].sum()),
        "clean_rows":          len(df),
    }


def sales_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """Total sales and order count per calendar month."""
    grp = (
        df.groupby(["Year", "Month", "MonthName"])
        .agg(Total_Sales=("Sales", "sum"), Orders=("InvoiceNo", "nunique"), Items_Sold=("Quantity", "sum"))
        .reset_index().sort_values(["Year", "Month"])
    )
    grp["Total_Sales"] = grp["Total_Sales"].round(2)
    return grp


def sales_by_day_of_week(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue per weekday."""
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    grp = (
        df.groupby("DayOfWeek")
        .agg(Total_Sales=("Sales", "sum"), Orders=("InvoiceNo", "nunique"))
        .reindex(order).reset_index()
    )
    grp["Total_Sales"] = grp["Total_Sales"].round(2)
    return grp


def sales_by_hour(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue per hour of day."""
    grp = (
        df.groupby("Hour")
        .agg(Total_Sales=("Sales", "sum"), Orders=("InvoiceNo", "nunique"))
        .reset_index()
    )
    grp["Total_Sales"] = grp["Total_Sales"].round(2)
    return grp


def top_products_by_sales(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N products by revenue."""
    grp = (
        df.groupby(["StockCode", "Description"])
        .agg(Total_Sales=("Sales", "sum"), Quantity_Sold=("Quantity", "sum"), Avg_Unit_Price=("UnitPrice", "mean"))
        .reset_index().sort_values("Total_Sales", ascending=False).head(n)
    )
    grp["Total_Sales"]    = grp["Total_Sales"].round(2)
    grp["Avg_Unit_Price"] = grp["Avg_Unit_Price"].round(2)
    return grp


def top_products_by_quantity(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N products by units sold."""
    grp = (
        df.groupby(["StockCode", "Description"])
        .agg(Quantity_Sold=("Quantity", "sum"), Total_Sales=("Sales", "sum"))
        .reset_index().sort_values("Quantity_Sold", ascending=False).head(n)
    )
    grp["Total_Sales"] = grp["Total_Sales"].round(2)
    return grp


def sales_by_country(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """Revenue and orders by country."""
    grp = (
        df.groupby("Country")
        .agg(Total_Sales=("Sales", "sum"), Orders=("InvoiceNo", "nunique"), Customers=("CustomerID", "nunique"))
        .reset_index().sort_values("Total_Sales", ascending=False).head(top_n)
    )
    grp["Total_Sales"] = grp["Total_Sales"].round(2)
    return grp


def top_customers(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N customers by spend."""
    grp = (
        df.dropna(subset=["CustomerID"])
        .groupby("CustomerID")
        .agg(Total_Spent=("Sales", "sum"), Orders=("InvoiceNo", "nunique"), Items_Bought=("Quantity", "sum"))
        .reset_index().sort_values("Total_Spent", ascending=False).head(n)
    )
    grp["Total_Spent"] = grp["Total_Spent"].round(2)
    return grp


def customer_order_frequency(df: pd.DataFrame) -> pd.DataFrame:
    """How many orders each customer placed."""
    order_counts = (
        df.dropna(subset=["CustomerID"])
        .groupby("CustomerID")["InvoiceNo"].nunique()
        .reset_index(name="Order_Count")
    )
    freq = (
        order_counts.groupby("Order_Count").size()
        .reset_index(name="Customers")
        .rename(columns={"Order_Count": "Orders_Placed"})
    )
    return freq


def sales_by_price_band(df: pd.DataFrame) -> pd.DataFrame:
    """Revenue segmented by unit-price tier."""
    bins   = [0, 1, 5, 10, 20, 50, float("inf")]
    labels = ["< £1", "£1–£5", "£5–£10", "£10–£20", "£20–£50", "£50+"]
    df = df.copy()
    df["PriceBand"] = pd.cut(df["UnitPrice"], bins=bins, labels=labels)
    grp = (
        df.groupby("PriceBand", observed=True)
        .agg(Total_Sales=("Sales", "sum"), Transactions=("InvoiceNo", "count"))
        .reset_index()
    )
    grp["Total_Sales"] = grp["Total_Sales"].round(2)
    return grp


# ============================================================
# ███████╗██████╗  ██████╗ ███╗   ██╗████████╗███████╗███╗   ██╗██████╗
# ██╔════╝██╔══██╗██╔═══██╗████╗  ██║╚══██╔══╝██╔════╝████╗  ██║██╔══██╗
# █████╗  ██████╔╝██║   ██║██╔██╗ ██║   ██║   █████╗  ██╔██╗ ██║██║  ██║
# ██╔══╝  ██╔══██╗██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██║╚██╗██║██║  ██║
# ██║     ██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║ ╚████║██████╔╝
# FRONTEND — Streamlit Dashboard
# ============================================================

# ------------------------------------------------------------------
# Page config
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Supermarket Sales Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------
# Custom CSS
# ------------------------------------------------------------------
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
    .kpi-card {
        background: #f7f8fa; border: 1px solid #e5e7eb;
        border-radius: 10px; padding: 18px 20px; text-align: center;
    }
    .kpi-label  { font-size: 13px; color: #57606a; margin-bottom: 6px; font-weight: 500; }
    .kpi-value  { font-size: 26px; font-weight: 700; color: #1f2328; }
    .kpi-sub    { font-size: 12px; color: #8b949e; margin-top: 4px; }
    .section-header {
        font-size: 19px; font-weight: 700; color: #1f2328;
        border-left: 4px solid #3b82d4; padding-left: 10px; margin: 28px 0 12px 0;
    }
    .insight-box {
        background: #eef4ff; border: 1px solid #c4d9f8; border-radius: 8px;
        padding: 14px 18px; font-size: 14px; color: #1f2328; line-height: 1.65;
    }
    .sidebar-note { font-size: 12px; color: #57606a; }
    #MainMenu { visibility: hidden; } footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------
PALETTE = px.colors.qualitative.Set2
BLUE    = "#3b82d4"
HERE    = os.path.dirname(os.path.abspath(__file__))
ROOT    = os.path.dirname(HERE)

# ------------------------------------------------------------------
# UI Helper functions
# ------------------------------------------------------------------

def fmt_currency(val: float) -> str:
    if val >= 1_000_000: return f"£{val/1_000_000:.2f}M"
    if val >= 1_000:     return f"£{val/1_000:.1f}K"
    return f"£{val:,.2f}"


def kpi_card(label: str, value: str, sub: str = "") -> str:
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>{sub_html}</div>')


def section(title: str):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


def insight(text: str):
    st.markdown(f'<div class="insight-box">💡 {text}</div>', unsafe_allow_html=True)


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/shopping-cart.png", width=64)
    st.markdown("## 🛒 Supermarket Analytics")
    st.markdown("---")

    default_csv = os.path.join(ROOT, "data.csv")
    uploaded = st.file_uploader("Upload a CSV dataset", type=["csv"])

    if uploaded:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        tmp.write(uploaded.read())
        tmp.flush()
        DATA_PATH = tmp.name
    else:
        DATA_PATH = default_csv

    st.markdown("---")
    st.markdown("### Filters")


# ------------------------------------------------------------------
# Data loading (cached)
# ------------------------------------------------------------------
@st.cache_data(show_spinner="Loading & cleaning dataset …")
def get_data(path: str):
    return load_and_clean(path)


try:
    df, quality = get_data(DATA_PATH)
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

# Sidebar filters (depend on loaded data)
with st.sidebar:
    all_countries     = sorted(df["Country"].dropna().unique().tolist())
    selected_countries = st.multiselect(
        "Countries", options=all_countries,
        default=all_countries[:5] if len(all_countries) >= 5 else all_countries,
    )
    year_min, year_max = int(df["Year"].min()), int(df["Year"].max())
    if year_min == year_max:
        selected_years = [year_min]
    else:
        selected_years = st.slider("Year range", min_value=year_min, max_value=year_max, value=(year_min, year_max))
    st.markdown("---")
    st.markdown('<span class="sidebar-note">Data cleaned · Sales = Qty × Unit Price</span>', unsafe_allow_html=True)

# Apply filters
dff = df[df["Country"].isin(selected_countries)] if selected_countries else df.copy()
if year_min != year_max and selected_years:
    dff = dff[(dff["Year"] >= selected_years[0]) & (dff["Year"] <= selected_years[1])]

# ------------------------------------------------------------------
# Page Header
# ------------------------------------------------------------------
st.markdown("<h1 style='font-size:32px;font-weight:800;color:#1f2328;margin-bottom:4px;'>"
            "🛒 Supermarket Sales Analysis Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#57606a;font-size:14px;margin-top:0;'>"
            "Retail transaction analytics · Dataset: <code>data.csv</code></p>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Tabs
# ------------------------------------------------------------------
tabs = st.tabs([
    "📋 Data Quality", "📊 KPIs Overview", "📅 Time Trends",
    "🏆 Products", "🌍 Geography", "👥 Customers",
    "💰 Price Analysis", "🔍 Raw Data",
])

# ══════════════════════════════════════════════════════════════════
# TAB 0 — Data Quality
# ══════════════════════════════════════════════════════════════════
with tabs[0]:
    section("Dataset Quality Report")
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(kpi_card("Raw Rows",          f"{quality['total_raw_rows']:,}"),           unsafe_allow_html=True)
    c2.markdown(kpi_card("Duplicate Rows",    f"{quality['duplicate_rows']:,}"),           unsafe_allow_html=True)
    c3.markdown(kpi_card("Negative Qty Rows", f"{quality['negative_quantity_rows']:,}", "Returns/cancellations"), unsafe_allow_html=True)
    c4.markdown(kpi_card("Zero-Price Rows",   f"{quality['zero_price_rows']:,}", "Removed"), unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    section("Missing Values per Column")
    mv = pd.DataFrame({
        "Column":        list(quality["missing_values"].keys()),
        "Missing Count": list(quality["missing_values"].values()),
        "Missing %":     list(quality["missing_pct"].values()),
    })
    mv = mv[mv["Missing Count"] > 0].reset_index(drop=True)
    if mv.empty:
        st.success("✅ No missing values found in any column.")
    else:
        fig_mv = px.bar(mv, x="Column", y="Missing %", text="Missing Count",
                        color="Missing %", color_continuous_scale="Reds",
                        title="Missing Values (%) per Column")
        fig_mv.update_traces(textposition="outside")
        fig_mv.update_layout(showlegend=False, height=380, coloraxis_showscale=False)
        st.plotly_chart(fig_mv, use_container_width=True)

    section("After Cleaning")
    a1, a2 = st.columns(2)
    a1.markdown(kpi_card("Clean Rows Retained", f"{len(df):,}"), unsafe_allow_html=True)
    a2.markdown(kpi_card("Rows Removed", f"{quality['total_raw_rows'] - len(df):,}", "Returns, nulls, duplicates"), unsafe_allow_html=True)
    insight(f"Out of <b>{quality['total_raw_rows']:,}</b> raw records, <b>{len(df):,}</b> clean transactions remain "
            "after removing cancellations, negative quantities, zero prices, duplicates, and missing descriptions.")

# ══════════════════════════════════════════════════════════════════
# TAB 1 — KPIs Overview
# ══════════════════════════════════════════════════════════════════
with tabs[1]:
    section("Key Performance Indicators")
    kpis = overall_kpis(dff)
    r1 = st.columns(4)
    r1[0].markdown(kpi_card("💷 Total Revenue",    fmt_currency(kpis["total_sales"])),    unsafe_allow_html=True)
    r1[1].markdown(kpi_card("📦 Total Orders",     f"{kpis['total_orders']:,}"),          unsafe_allow_html=True)
    r1[2].markdown(kpi_card("👤 Unique Customers", f"{kpis['total_customers']:,}"),       unsafe_allow_html=True)
    r1[3].markdown(kpi_card("🏷️ Unique Products",  f"{kpis['total_products']:,}"),       unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    r2 = st.columns(3)
    r2[0].markdown(kpi_card("🛍️ Avg Order Value", fmt_currency(kpis["avg_order_value"])), unsafe_allow_html=True)
    r2[1].markdown(kpi_card("💲 Avg Unit Price",   f"£{kpis['avg_unit_price']:.2f}"),     unsafe_allow_html=True)
    r2[2].markdown(kpi_card("📊 Total Qty Sold",   f"{kpis['total_quantity_sold']:,}"),   unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    section("Revenue Distribution – Top 10 Countries")
    ctry = sales_by_country(dff, top_n=10)
    fig_pie = px.pie(ctry, names="Country", values="Total_Sales",
                     color_discrete_sequence=PALETTE, hole=0.4)
    fig_pie.update_traces(textposition="outside", textinfo="percent+label")
    fig_pie.update_layout(height=430)
    st.plotly_chart(fig_pie, use_container_width=True)
    insight(f"Total revenue: <b>{fmt_currency(kpis['total_sales'])}</b> from <b>{kpis['total_orders']:,}</b> orders "
            f"by <b>{kpis['total_customers']:,}</b> customers. Avg basket: <b>{fmt_currency(kpis['avg_order_value'])}</b>.")

# ══════════════════════════════════════════════════════════════════
# TAB 2 — Time Trends
# ══════════════════════════════════════════════════════════════════
with tabs[2]:
    section("Monthly Sales Trend")
    monthly = sales_by_month(dff)
    fig_line = px.line(monthly, x="MonthName", y="Total_Sales", markers=True, line_shape="spline",
                       labels={"MonthName": "Month", "Total_Sales": "Revenue (£)"}, color_discrete_sequence=[BLUE])
    fig_line.update_traces(line_width=2.5, marker_size=7)
    fig_line.update_layout(height=380, xaxis_tickangle=-40)
    st.plotly_chart(fig_line, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        section("Orders per Month")
        fig_ord = px.bar(monthly, x="MonthName", y="Orders", color_discrete_sequence=[PALETTE[1]],
                         labels={"MonthName": "Month", "Orders": "Unique Orders"})
        fig_ord.update_layout(height=330, xaxis_tickangle=-40)
        st.plotly_chart(fig_ord, use_container_width=True)
    with col_b:
        section("Items Sold per Month")
        fig_itm = px.bar(monthly, x="MonthName", y="Items_Sold", color_discrete_sequence=[PALETTE[2]],
                         labels={"MonthName": "Month", "Items_Sold": "Quantity Sold"})
        fig_itm.update_layout(height=330, xaxis_tickangle=-40)
        st.plotly_chart(fig_itm, use_container_width=True)

    section("Sales by Day of Week")
    dow = sales_by_day_of_week(dff)
    fig_dow = px.bar(dow, x="DayOfWeek", y="Total_Sales", text_auto=".2s",
                     color="Total_Sales", color_continuous_scale="Blues",
                     labels={"DayOfWeek": "Day", "Total_Sales": "Revenue (£)"})
    fig_dow.update_layout(height=360, coloraxis_showscale=False)
    st.plotly_chart(fig_dow, use_container_width=True)

    section("Sales by Hour of Day")
    hourly = sales_by_hour(dff)
    fig_hour = px.area(hourly, x="Hour", y="Total_Sales",
                       labels={"Hour": "Hour of Day (24h)", "Total_Sales": "Revenue (£)"},
                       color_discrete_sequence=[BLUE], line_shape="spline")
    fig_hour.update_layout(height=320)
    st.plotly_chart(fig_hour, use_container_width=True)

    peak_month = monthly.loc[monthly["Total_Sales"].idxmax(), "MonthName"]
    peak_day   = dow.loc[dow["Total_Sales"].idxmax(), "DayOfWeek"]
    peak_hour  = int(hourly.loc[hourly["Total_Sales"].idxmax(), "Hour"])
    insight(f"Peak month: <b>{peak_month}</b>. Best day: <b>{peak_day}</b>. "
            f"Busiest hour: <b>{peak_hour}:00</b>. Use these to plan promotions and staffing.")

# ══════════════════════════════════════════════════════════════════
# TAB 3 — Products
# ══════════════════════════════════════════════════════════════════
with tabs[3]:
    n_products = st.slider("Number of top products to show", 5, 20, 10, key="prod_slider")

    section(f"Top {n_products} Products by Revenue")
    top_rev = top_products_by_sales(dff, n=n_products)
    fig_rev = px.bar(top_rev.sort_values("Total_Sales"), x="Total_Sales", y="Description",
                     orientation="h", text="Total_Sales", color="Total_Sales",
                     color_continuous_scale="Teal", labels={"Total_Sales": "Revenue (£)", "Description": "Product"})
    fig_rev.update_traces(texttemplate="£%{text:,.0f}", textposition="outside")
    fig_rev.update_layout(height=420, coloraxis_showscale=False, yaxis_tickfont_size=11)
    st.plotly_chart(fig_rev, use_container_width=True)

    section(f"Top {n_products} Products by Quantity Sold")
    top_qty = top_products_by_quantity(dff, n=n_products)
    fig_qty = px.bar(top_qty.sort_values("Quantity_Sold"), x="Quantity_Sold", y="Description",
                     orientation="h", text="Quantity_Sold", color="Quantity_Sold",
                     color_continuous_scale="Oranges", labels={"Quantity_Sold": "Units Sold", "Description": "Product"})
    fig_qty.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig_qty.update_layout(height=420, coloraxis_showscale=False, yaxis_tickfont_size=11)
    st.plotly_chart(fig_qty, use_container_width=True)

    section("Top Products – Detail Table")
    st.dataframe(
        top_rev.rename(columns={"StockCode": "Stock Code", "Description": "Product",
                                 "Total_Sales": "Revenue (£)", "Quantity_Sold": "Qty Sold",
                                 "Avg_Unit_Price": "Avg Price (£)"})
        .style.format({"Revenue (£)": "£{:,.2f}", "Avg Price (£)": "£{:.2f}", "Qty Sold": "{:,}"}),
        use_container_width=True, height=360,
    )
    insight(f"<b>{top_rev.iloc[0]['Description']}</b> is the top product at "
            f"<b>{fmt_currency(top_rev.iloc[0]['Total_Sales'])}</b>. Bundle it with related items in promotions.")

# ══════════════════════════════════════════════════════════════════
# TAB 4 — Geography
# ══════════════════════════════════════════════════════════════════
with tabs[4]:
    section("Revenue by Country")
    top_n_ctry = st.slider("Top N countries", 5, 20, 15, key="ctry_slider")
    ctry_df = sales_by_country(dff, top_n=top_n_ctry)

    fig_ctry = px.bar(ctry_df.sort_values("Total_Sales"), x="Total_Sales", y="Country",
                      orientation="h", text="Total_Sales", color="Total_Sales",
                      color_continuous_scale="Purples", labels={"Total_Sales": "Revenue (£)", "Country": "Country"})
    fig_ctry.update_traces(texttemplate="£%{text:,.0f}", textposition="outside")
    fig_ctry.update_layout(height=460, coloraxis_showscale=False)
    st.plotly_chart(fig_ctry, use_container_width=True)

    cx, cy = st.columns(2)
    with cx:
        section("Orders by Country")
        fig_oc = px.bar(ctry_df.sort_values("Orders"), x="Orders", y="Country",
                        orientation="h", color_discrete_sequence=[PALETTE[3]], text="Orders")
        fig_oc.update_traces(textposition="outside")
        fig_oc.update_layout(height=400)
        st.plotly_chart(fig_oc, use_container_width=True)
    with cy:
        section("Customers by Country")
        fig_cc = px.bar(ctry_df.sort_values("Customers"), x="Customers", y="Country",
                        orientation="h", color_discrete_sequence=[PALETTE[4]], text="Customers")
        fig_cc.update_traces(textposition="outside")
        fig_cc.update_layout(height=400)
        st.plotly_chart(fig_cc, use_container_width=True)

    section("Country Summary Table")
    st.dataframe(
        ctry_df.rename(columns={"Total_Sales": "Revenue (£)"})
        .style.format({"Revenue (£)": "£{:,.2f}", "Orders": "{:,}", "Customers": "{:,}"}),
        use_container_width=True, height=350,
    )
    top_c = ctry_df.iloc[0]
    insight(f"<b>{top_c['Country']}</b> leads with <b>{fmt_currency(top_c['Total_Sales'])}</b> "
            f"across <b>{int(top_c['Orders']):,}</b> orders from <b>{int(top_c['Customers']):,}</b> customers.")

# ══════════════════════════════════════════════════════════════════
# TAB 5 — Customers
# ══════════════════════════════════════════════════════════════════
with tabs[5]:
    section("Top 10 Customers by Spend")
    tc = top_customers(dff, n=10)
    fig_tc = px.bar(tc.sort_values("Total_Spent"), x="Total_Spent", y="CustomerID",
                    orientation="h", text="Total_Spent", color="Total_Spent",
                    color_continuous_scale="Greens", labels={"Total_Spent": "Total Spent (£)", "CustomerID": "Customer ID"})
    fig_tc.update_traces(texttemplate="£%{text:,.0f}", textposition="outside")
    fig_tc.update_layout(height=420, coloraxis_showscale=False)
    st.plotly_chart(fig_tc, use_container_width=True)

    section("Top Customers – Detail Table")
    st.dataframe(
        tc.rename(columns={"CustomerID": "Customer ID", "Total_Spent": "Total Spent (£)",
                             "Orders": "Orders", "Items_Bought": "Items Bought"})
        .style.format({"Total Spent (£)": "£{:,.2f}", "Orders": "{:,}", "Items Bought": "{:,}"}),
        use_container_width=True, height=340,
    )

    section("Customer Order Frequency Distribution")
    freq = customer_order_frequency(dff)
    fig_freq = px.bar(freq[freq["Orders_Placed"] <= 20], x="Orders_Placed", y="Customers",
                      labels={"Orders_Placed": "Number of Orders Placed", "Customers": "Number of Customers"},
                      color_discrete_sequence=[PALETTE[0]], text="Customers")
    fig_freq.update_traces(textposition="outside")
    fig_freq.update_layout(height=350, xaxis=dict(dtick=1))
    st.plotly_chart(fig_freq, use_container_width=True)

    single = int(freq[freq["Orders_Placed"] == 1]["Customers"].sum()) if 1 in freq["Orders_Placed"].values else 0
    insight(f"Top customer spent <b>{fmt_currency(tc.iloc[0]['Total_Spent'])}</b>. "
            f"<b>{single:,}</b> customers placed only 1 order — strong target for re-engagement campaigns.")

# ══════════════════════════════════════════════════════════════════
# TAB 6 — Price Analysis
# ══════════════════════════════════════════════════════════════════
with tabs[6]:
    section("Sales by Unit-Price Band")
    pb = sales_by_price_band(dff)
    p1, p2 = st.columns(2)
    with p1:
        fig_pb_rev = px.pie(pb, names="PriceBand", values="Total_Sales",
                            color_discrete_sequence=PALETTE, title="Revenue Share by Price Band", hole=0.35)
        fig_pb_rev.update_traces(textposition="outside", textinfo="percent+label")
        fig_pb_rev.update_layout(height=400)
        st.plotly_chart(fig_pb_rev, use_container_width=True)
    with p2:
        fig_pb_txn = px.bar(pb, x="PriceBand", y="Transactions",
                            color_discrete_sequence=[PALETTE[1]], text="Transactions",
                            title="Transaction Count by Price Band",
                            labels={"PriceBand": "Price Band", "Transactions": "Transaction Count"})
        fig_pb_txn.update_traces(textposition="outside")
        fig_pb_txn.update_layout(height=400)
        st.plotly_chart(fig_pb_txn, use_container_width=True)

    section("Unit Price Distribution")
    fig_hist = px.histogram(dff["UnitPrice"].clip(upper=dff["UnitPrice"].quantile(0.99)),
                            nbins=50, labels={"value": "Unit Price (£)", "count": "Frequency"},
                            color_discrete_sequence=[BLUE], title="Unit Price Histogram (99th pct capped)")
    fig_hist.update_layout(height=340, showlegend=False)
    st.plotly_chart(fig_hist, use_container_width=True)

    top_band = pb.loc[pb["Total_Sales"].idxmax(), "PriceBand"]
    insight(f"The <b>{top_band}</b> price band drives the most revenue. "
            "Consider adding a premium range to lift average order value.")

# ══════════════════════════════════════════════════════════════════
# TAB 7 — Raw Data
# ══════════════════════════════════════════════════════════════════
with tabs[7]:
    section("Cleaned Transaction Data")
    st.markdown(f"<p style='color:#57606a;font-size:13px;'>Showing <b>{len(dff):,}</b> rows × "
                f"<b>{len(dff.columns)}</b> columns</p>", unsafe_allow_html=True)

    search = st.text_input("🔍 Filter by product description", "")
    disp   = dff[dff["Description"].str.contains(search, case=False, na=False)] if search else dff

    st.dataframe(
        disp[["InvoiceNo", "StockCode", "Description", "Quantity",
              "UnitPrice", "Sales", "InvoiceDate", "CustomerID", "Country"]]
        .rename(columns={"InvoiceNo": "Invoice No", "StockCode": "Stock Code",
                          "UnitPrice": "Unit Price (£)", "Sales": "Sales (£)",
                          "InvoiceDate": "Invoice Date", "CustomerID": "Customer ID"})
        .style.format({"Unit Price (£)": "£{:.2f}", "Sales (£)": "£{:.2f}"}),
        use_container_width=True, height=500,
    )
    st.download_button(
        label="⬇️ Download filtered data as CSV",
        data=disp.to_csv(index=False).encode("utf-8"),
        file_name="filtered_sales_data.csv",
        mime="text/csv",
    )
