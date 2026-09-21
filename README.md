# 🛒 Supermarket Sales Analysis

An end-to-end data analytics project that loads, cleans, analyses, and visualises a retail transaction dataset through an interactive **Streamlit** dashboard.

---

## 📁 Project Structure

```
supermarket_analysis/
├── app.py                  ← Streamlit frontend (8 interactive tabs)
├── requirements.txt        ← Python dependencies
├── README.md               ← This file
└── utils/
    ├── __init__.py
    ├── data_loader.py      ← Data loading, cleaning & Sales calculation
    └── analytics.py        ← All KPI, grouping & aggregation functions
```

The dataset (`data.csv`) must be placed in the **parent directory** (one level above `supermarket_analysis/`).

---

## 📥 Dataset Source & Download

The dataset used in this project is the **E-Commerce Data** dataset publicly available on **Kaggle**.

| Detail | Info |
|--------|------|
| **Name** | E-Commerce Data |
| **Source** | Kaggle |
| **Dataset Link** | https://www.kaggle.com/datasets/carrie1/ecommerce-data |
| **Format** | `.csv` |
| **Size** | ~541,909 rows × 8 columns |
| **Period** | December 2010 – December 2011 |
| **Origin** | UK-based online retail store |

> 💡 **Download Steps:**
> 1. Go to https://www.kaggle.com/datasets/carrie1/ecommerce-data
> 2. Click the **"Download"** button (requires a free Kaggle account)
> 3. Extract the ZIP file — you will find `data.csv` inside
> 4. Place `data.csv` in the project root (next to the `supermarket_analysis/` folder)

---

## 📊 Dataset

| Column | Description |
|--------|-------------|
| `InvoiceNo` | Unique transaction identifier (prefix `C` = cancellation) |
| `StockCode` | Product identifier |
| `Description` | Product name |
| `Quantity` | Units purchased per line item |
| `InvoiceDate` | Date and time of transaction |
| `UnitPrice` | Price per unit in GBP (£) |
| `CustomerID` | Unique customer identifier |
| `Country` | Customer's country |

- **Raw rows:** 541,909  
- **Clean rows retained:** 524,878  
- **Date range:** December 2010 – December 2011

---

## ⚙️ Setup & Installation

### 1. Clone / download the project

Place `data.csv` and the `supermarket_analysis/` folder together:

```
your-project/
├── data.csv
└── supermarket_analysis/
    ├── app.py
    ├── requirements.txt
    └── utils/
```

### 2. Install dependencies

```bash
pip install -r supermarket_analysis/requirements.txt
```

Required packages:

| Package | Version |
|---------|---------|
| `streamlit` | ≥ 1.32.0 |
| `pandas` | ≥ 2.0.0 |
| `plotly` | ≥ 5.18.0 |

### 3. Run the dashboard

```bash
streamlit run supermarket_analysis/app.py
```

Open your browser at `http://localhost:8501`.

---

## 🔬 Analytics Pipeline

### Step 1 — Load CSV
`data_loader.load_and_clean()` reads the CSV using `latin-1` encoding to handle Windows-1252 characters (e.g. `£`).

### Step 2 — Data Quality Check
A quality report is generated **before** cleaning, capturing:
- Missing values per column (count + %)
- Duplicate rows
- Negative quantity / zero-price rows
- Cancelled transactions (C-prefix invoices)

### Step 3 — Calculate Sales
```python
df["Sales"] = df["Quantity"] * df["UnitPrice"]
```

### Step 4 — Grouping & Summaries
`analytics.py` provides 9 pure functions:

| Function | Output |
|----------|--------|
| `overall_kpis()` | Total revenue, orders, customers, AOV |
| `sales_by_month()` | Monthly revenue, orders, items sold |
| `sales_by_day_of_week()` | Revenue per weekday |
| `sales_by_hour()` | Revenue per hour of day |
| `top_products_by_sales()` | Top N products by revenue |
| `top_products_by_quantity()` | Top N products by units sold |
| `sales_by_country()` | Revenue & orders per country |
| `top_customers()` | Top N customers by spend |
| `customer_order_frequency()` | How many orders each customer placed |
| `sales_by_price_band()` | Revenue segmented by unit-price tier |

### Step 5 — Charts
All charts use **Plotly** (interactive, hover-enabled):
- Line chart — monthly revenue trend
- Bar charts — weekday, hourly, country, product comparisons
- Horizontal bar charts — top products & customers
- Pie / donut charts — country share & price-band revenue
- Area chart — hourly sales pattern
- Histogram — unit price distribution

### Step 6 — Business Decisions
Each dashboard tab ends with a `💡 Insight` box summarising the key business recommendation from that analysis.

---

## 🖥️ Dashboard Tabs

| Tab | What you see |
|-----|-------------|
| 📋 Data Quality | Missing-value chart, cleaning summary |
| 📊 KPIs Overview | Revenue, orders, customers, avg order value, country pie |
| 📅 Time Trends | Monthly line, weekday bars, hourly area chart |
| 🏆 Products | Top products by revenue and quantity |
| 🌍 Geography | Revenue, orders, customers per country |
| 👥 Customers | Top spenders, order frequency distribution |
| 💰 Price Analysis | Price-band revenue share, unit-price histogram |
| 🔍 Raw Data | Searchable, filterable, downloadable dataset |

---

## 📌 Key Results (Full Dataset)

| KPI | Value |
|-----|-------|
| Total Revenue | £10,642,110 |
| Total Orders | 19,960 |
| Unique Customers | 4,338 |
| Unique Products | 3,922 |
| Avg Order Value | £533.17 |
| Top Country | United Kingdom (£9,001,744) |
| Peak Month | November 2011 |
| Busiest Day | Thursday |

---

## 📄 Files Submitted

| File | Description |
|------|-------------|
| `data.csv` | Raw retail transaction dataset |
| `supermarket_analysis/app.py` | Streamlit dashboard |
| `supermarket_analysis/utils/data_loader.py` | Data loading & cleaning module |
| `supermarket_analysis/utils/analytics.py` | Analytics & KPI module |
| `supermarket_analysis/requirements.txt` | Python dependencies |
| `supermarket_analysis/README.md` | This file |
| `Project_Report.docx` | Full project report with code & UI output |

---

## 👤 Author

**Supermarket Sales Analysis Project**  
Data Analytics · Python · Streamlit · Pandas · Plotly
