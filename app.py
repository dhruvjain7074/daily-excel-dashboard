import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# =================================================
# IMAGE LOADER (CACHED – PERFORMANCE FIX)
# =================================================
@st.cache_data(show_spinner=False)
def get_sorted_images(folder):
    def extract_datetime(filename):
        try:
            parts = filename.rsplit("_", 2)
            dt_str = parts[-2] + "_" + parts[-1].split(".")[0]
            return datetime.strptime(dt_str, "%Y-%m-%d_%H-%M-%S")
        except Exception:
            return datetime.min

    if not os.path.exists(folder):
        return []

    images = [
        f for f in os.listdir(folder)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]

    return sorted(images, key=extract_datetime)


# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(page_title="Daily Excel Dashboard", layout="wide")

# =================================================
# MINIMAL WHITE DESIGN SYSTEM
# =================================================
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@300;400&display=swap" rel="stylesheet">

<style>
/* ── ROOT TOKENS ── */
:root {
    --white:      #ffffff;
    --off-white:  #f8f8f7;
    --hairline:   #e8e8e5;
    --muted:      #a0a09a;
    --ink-light:  #6b6b64;
    --ink:        #1a1a18;
    --accent:     #0f0f0e;
    --blue:       #1a56db;
    --radius:     4px;
    --font:       'DM Sans', sans-serif;
    --mono:       'DM Mono', monospace;
}

/* ── GLOBAL RESET ── */
html, body, [class*="css"] {
    font-family: var(--font) !important;
    color: var(--ink) !important;
    background: var(--white) !important;
}

/* ── APP SHELL ── */
.stApp {
    background: var(--white) !important;
}

.block-container {
    padding: 2.5rem 3rem 4rem 3rem !important;
    max-width: 1400px !important;
}

/* ── HIDE STREAMLIT CRUFT ── */
#MainMenu, footer, header { visibility: hidden !important; }
.stDeployButton { display: none !important; }

/* ── TYPOGRAPHY ── */
h1, h2, h3, h4, h5, h6,
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    font-family: var(--font) !important;
    font-weight: 500 !important;
    letter-spacing: -0.02em !important;
    color: var(--ink) !important;
}

/* ── PAGE HEADER ── */
.dashboard-header {
    border-bottom: 1px solid var(--hairline);
    padding-bottom: 1.5rem;
    margin-bottom: 2.5rem;
}

.dashboard-header h1 {
    font-size: 1.35rem !important;
    font-weight: 500 !important;
    letter-spacing: -0.01em !important;
    margin: 0 !important;
    padding: 0 !important;
}

.dashboard-header span {
    font-size: 0.78rem;
    color: var(--muted);
    font-family: var(--mono) !important;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* ── SECTION HEADERS (subheader) ── */
.stMarkdown h2,
[data-testid="stMarkdownContainer"] h2 {
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    color: var(--ink-light) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    margin-bottom: 1.5rem !important;
    padding-bottom: 0.65rem !important;
    border-bottom: 1px solid var(--hairline) !important;
}

/* ── SELECT BOX ── */
.stSelectbox > div > div {
    background: var(--white) !important;
    border: 1px solid var(--hairline) !important;
    border-radius: var(--radius) !important;
    box-shadow: none !important;
    font-size: 0.875rem !important;
    color: var(--ink) !important;
    transition: border-color 0.15s ease;
}

.stSelectbox > div > div:hover {
    border-color: var(--ink) !important;
}

.stSelectbox > div > div:focus-within {
    border-color: var(--ink) !important;
    box-shadow: 0 0 0 2px rgba(26,26,24,0.08) !important;
}

.stSelectbox label {
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    color: var(--muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    margin-bottom: 0.4rem !important;
}

/* Dropdown popup */
[data-baseweb="popover"],
[data-baseweb="menu"] {
    background: var(--white) !important;
    border: 1px solid var(--hairline) !important;
    border-radius: var(--radius) !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06) !important;
}

[data-baseweb="menu"] li {
    font-size: 0.875rem !important;
    color: var(--ink) !important;
    padding: 0.5rem 0.9rem !important;
}

[data-baseweb="menu"] li:hover {
    background: var(--off-white) !important;
}

/* ── DATE INPUT ── */
.stDateInput > div > div {
    background: var(--white) !important;
    border: 1px solid var(--hairline) !important;
    border-radius: var(--radius) !important;
    box-shadow: none !important;
    font-size: 0.875rem !important;
}

.stDateInput label {
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    color: var(--muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}

/* ── RADIO BUTTONS ── */
.stRadio label {
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    color: var(--muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}

.stRadio > div {
    gap: 1.5rem !important;
}

.stRadio > div [data-testid="stMarkdownContainer"] p {
    font-size: 0.85rem !important;
    color: var(--ink) !important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--hairline) !important;
    gap: 0 !important;
    padding: 0 !important;
    margin-bottom: 1.5rem !important;
}

.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    color: var(--muted) !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1.1rem !important;
    margin-bottom: -1px !important;
    transition: color 0.15s ease, border-color 0.15s ease !important;
}

.stTabs [data-baseweb="tab"]:hover {
    color: var(--ink) !important;
    background: transparent !important;
}

.stTabs [aria-selected="true"] {
    color: var(--ink) !important;
    border-bottom: 2px solid var(--ink) !important;
    background: transparent !important;
}

.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}

.stTabs [data-baseweb="tab-border"] {
    display: none !important;
}

/* ── DATAFRAME ── */
.stDataFrame {
    border: 1px solid var(--hairline) !important;
    border-radius: var(--radius) !important;
    overflow: hidden !important;
}

.stDataFrame thead th {
    background: var(--off-white) !important;
    color: var(--ink-light) !important;
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    border-bottom: 1px solid var(--hairline) !important;
    padding: 0.6rem 0.8rem !important;
}

.stDataFrame tbody td {
    font-size: 0.82rem !important;
    font-family: var(--mono) !important;
    color: var(--ink) !important;
    border-bottom: 1px solid var(--hairline) !important;
    padding: 0.5rem 0.8rem !important;
}

.stDataFrame tbody tr:hover td {
    background: var(--off-white) !important;
}

/* ── METRIC CARDS ── */
[data-testid="stMetric"] {
    background: var(--off-white) !important;
    border: 1px solid var(--hairline) !important;
    border-radius: var(--radius) !important;
    padding: 1rem 1.2rem !important;
}

[data-testid="stMetricLabel"] {
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    color: var(--muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}

[data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 300 !important;
    color: var(--ink) !important;
    letter-spacing: -0.03em !important;
    font-family: var(--mono) !important;
}

/* ── INFO / WARNING BANNERS ── */
.stAlert {
    border-radius: var(--radius) !important;
    border-width: 1px !important;
    font-size: 0.82rem !important;
}

.stInfo {
    background: #f0f4ff !important;
    border-color: #c7d4f7 !important;
    color: #2d4099 !important;
}

.stWarning {
    background: #fffbf0 !important;
    border-color: #f5e4a0 !important;
    color: #7a5c00 !important;
}

/* ── IMAGES ── */
.stImage img {
    border-radius: var(--radius) !important;
    border: 1px solid var(--hairline) !important;
}

/* ── PLOTLY CHARTS ── */
.js-plotly-plot .plotly {
    background: transparent !important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--off-white); }
::-webkit-scrollbar-thumb { background: var(--hairline); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--muted); }

/* ── DIVIDER ── */
hr { border: none; border-top: 1px solid var(--hairline) !important; margin: 1.5rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── HEADER ──
st.markdown("""
<div class="dashboard-header">
    <span>Market Intelligence</span>
    <h1>Daily Excel Dashboard</h1>
</div>
""", unsafe_allow_html=True)



# =================================================
# PLOT FUNCTION — MINIMAL PLOTLY THEME
# =================================================
PLOT_LAYOUT = dict(
    template="plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    autosize=True,
    font=dict(family="DM Sans, sans-serif", size=12, color="#1a1a18"),
    title_font=dict(family="DM Sans, sans-serif", size=13, color="#6b6b64"),
    title_x=0.5,
    hovermode="x unified",
    margin=dict(l=0, r=0, t=52, b=40),   # zero side margins — no whitespace
    xaxis=dict(
        showgrid=False,
        zeroline=False,
        showline=False,
        tickfont=dict(family="DM Mono, monospace", size=10, color="#a0a09a"),
        tickcolor="#e8e8e5",
        automargin=True,
    ),
    yaxis=dict(
        gridcolor="#f0f0ed",
        gridwidth=1,
        zeroline=False,
        showline=False,
        tickfont=dict(family="DM Mono, monospace", size=10, color="#a0a09a"),
        tickformat=",",
        showexponent="none",
        automargin=True,
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
        font=dict(size=11),
        bgcolor="rgba(255,255,255,0)",
    ),
    hoverlabel=dict(
        bgcolor="white",
        bordercolor="#e8e8e5",
        font=dict(family="DM Mono, monospace", size=11),
    ),
)

LINE_COLOR = "#1a56db"
GREEN = "#16a34a"
RED   = "#dc2626"

CHART_HEIGHT = 520


def plot_single_line(df, x, y, height=CHART_HEIGHT, y_label=None, title=None, color=None, key=None):
    fig = px.line(df, x=x, y=y)
    line_color = color if color else LINE_COLOR
    fig.update_traces(
        line=dict(width=1.8, color=line_color),
        hovertemplate="<b>%{x|%d %b %Y}</b><br>%{y:,.2f}<extra></extra>",
    )
    layout = dict(**PLOT_LAYOUT, height=height, yaxis_title=y_label, title=title)
    fig.update_layout(**layout)
    fig.update_yaxes(tickformat=",", showexponent="none")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)


# =================================================
# LOAD DATA (GOOGLE SHEETS – MULTI SHEET)
# =================================================
def load_data():
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )

    client = gspread.authorize(creds)

    SPREADSHEET_ID = "13UqMshnNj01OTGpsEjw7t1TEYZt6rBNpPWcTxLV2ZzM"
    sheet = client.open_by_key(SPREADSHEET_ID)

    def read_worksheet(sheet_name):
        ws = sheet.worksheet(sheet_name)
        values = ws.get_all_values()

        if not values or len(values) < 2:
            return pd.DataFrame()

        headers = values[0]
        rows = values[1:]

        df = pd.DataFrame(rows, columns=headers)

        df.columns = (
            pd.Series(df.columns)
            .astype(str)
            .str.strip()
            .str.replace("\u00a0", " ", regex=True)
        )

        df = df.loc[:, df.columns != ""]
        df = df.replace("", pd.NA)

        return df

    df_main        = read_worksheet("comparision charts")
    df_rbi         = read_worksheet("Rbi net liquidity")
    df_index_oi    = read_worksheet("Index oi charts")
    df_index_val   = read_worksheet("index (pe/pb/divyld)")
    df_tariff      = read_worksheet("Tariff_Timeline")
    df_global_rates= read_worksheet("Global interest rates")
    df_india_macro = read_worksheet("India macroeconomic indicators")
    df_auto_sales  = read_worksheet("AUTOMOBILE SALES VOLUME")
    df_mtf         = read_worksheet("mtf outstanding")

    return df_main, df_rbi, df_index_oi, df_index_val, df_tariff, df_global_rates, df_auto_sales, df_india_macro, df_mtf


df_main, df_rbi, df_index_oi, df_index_val, df_tariff, df_global_rates, df_auto_sales, df_india_macro, df_mtf = load_data()

# ── CLEAN df_main ──
numeric_cols_main = [
    "HIGH 1", "LOW 1", "H/L 1", "H RATIO 1", "L RATIO 1",
    "HIGH 2", "LOW 2", "H/L 2", "H RATIO 2", "L RATIO 2",
    "HIGH 3", "LOW 3", "H/L 3", "H RATIO 3", "L RATIO 3"
]
for col in numeric_cols_main:
    if col in df_main.columns:
        df_main[col] = pd.to_numeric(df_main[col], errors="coerce")
df_main = df_main.dropna(how="all", subset=numeric_cols_main)

# ── CLEAN df_index_oi ──
numeric_cols_oi = [
    "Index Futures OI", "Nifty Futures oi",
    "Future Index Long", "Future Index Short",
    "total client oi", "Client OI", "FII OI",
]
for col in numeric_cols_oi:
    if col in df_index_oi.columns:
        df_index_oi[col] = pd.to_numeric(df_index_oi[col], errors="coerce")

# ── CLEAN df_rbi ──
for col in ["NET LIQ INC TODAY", "AMOUNT"]:
    if col in df_rbi.columns:
        df_rbi[col] = pd.to_numeric(df_rbi[col], errors="coerce")


# =================================================
# NAV DROPDOWN
# =================================================
VIEWS = [
    "Breadth Data",
    "RBI Net Liquidity Injected",
    "Index Futures OI",
    "Index (PE / PB / DIV YLD)",
    "Asset Class Charts",
    "Metal Charts",
    "Tariff Timeline",
    "Global Interest Rates",
    "India Macroeconomic Indicators",
    "Automobile Sales Volumes",
    "Magazine Cover",
    "Multiasset Chart (One View)",
    "Net MTF Outstanding",
]

view = st.selectbox("View", VIEWS, label_visibility="collapsed")

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)


# =================================================
# DATASET MAPPING
# =================================================
mapping = {
    "52 Week Data":  {"date": "DATE 1", "high": "HIGH 1", "low": "LOW 1", "hl": "H/L 1", "hr": "H RATIO 1", "lr": "L RATIO 1"},
    "EMA 20 Data":   {"date": "DATE 2", "high": "HIGH 2", "low": "LOW 2", "hl": "H/L 2", "hr": "H RATIO 2", "lr": "L RATIO 2"},
    "EMA 200 Data":  {"date": "DATE 3", "high": "HIGH 3", "low": "LOW 3", "hl": "H/L 3", "hr": "H RATIO 3", "lr": "L RATIO 3"},
}


# =================================================
# BREADTH DATA — 52 WEEK / EMA 20 / EMA 200
# =================================================
if view == "Breadth Data":

    st.markdown("#### Breadth Data")

    # Radio instead of tabs — only renders one dataset at a time,
    # which is the only reliable way to avoid Plotly's hidden-tab width=0 bug
    breadth_choice = st.radio(
        "Dataset",
        ["52 Week", "EMA 20", "EMA 200"],
        horizontal=True,
        key="breadth_radio",
        label_visibility="collapsed",
    )

    breadth_key_map = {"52 Week": "52 Week Data", "EMA 20": "EMA 20 Data", "EMA 200": "EMA 200 Data"}
    m = mapping[breadth_key_map[breadth_choice]]

    data = df_main[
        [m["date"], m["high"], m["low"], m["hl"], m["hr"], m["lr"]]
    ].dropna()
    data[m["date"]] = pd.to_datetime(data[m["date"]], format="%d/%m/%Y", errors="coerce")
    data = data.dropna(subset=[m["date"]])

    all_min = data[m["date"]].min().date()
    all_max = data[m["date"]].max().date()
    start_date, end_date = st.date_input(
        "Date range",
        [all_min, all_max],
        key="breadth_dr",
        label_visibility="collapsed",
    )
    filtered = data[
        (data[m["date"]] >= pd.to_datetime(start_date)) &
        (data[m["date"]] <= pd.to_datetime(end_date))
    ]

    # prefix makes every chart key unique per dataset selection
    prefix = breadth_choice.replace(" ", "_").lower()

    plot_df1 = filtered[[m["date"], m["high"], m["low"]]].rename(
        columns={m["date"]: "Date", m["high"]: "HIGH", m["low"]: "LOW"}
    )
    fig1 = px.line(
        plot_df1, x="Date", y=["HIGH", "LOW"],
        color_discrete_map={"HIGH": GREEN, "LOW": RED},
        title="High & Low Count",
    )
    fig1.update_traces(line=dict(width=1.8))
    fig1.update_traces(selector=dict(name="HIGH"),
        hovertemplate="<b>%{x|%d %b %Y}</b><br>High: %{y:,.0f}<extra></extra>")
    fig1.update_traces(selector=dict(name="LOW"),
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Low: %{y:,.0f}<extra></extra>")
    fig1.update_layout(**{**PLOT_LAYOUT, "height": 520})
    st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False}, key=f"{prefix}_hl")

    plot_single_line(filtered.rename(columns={m["date"]: "Date", m["hl"]: "HIGH/LOW RATIO"}),
                     "Date", "HIGH/LOW RATIO", title="High / Low Ratio", key=f"{prefix}_hlr")
    plot_single_line(filtered.rename(columns={m["date"]: "Date", m["hr"]: "HIGH / EMA 200"}),
                     "Date", "HIGH / EMA 200", title="High / EMA 200", color=GREEN, key=f"{prefix}_hr")
    plot_single_line(filtered.rename(columns={m["date"]: "Date", m["lr"]: "LOW / EMA 200"}),
                     "Date", "LOW / EMA 200", title="Low / EMA 200", color=RED, key=f"{prefix}_lr")


# =================================================
# RBI NET LIQUIDITY INJECTED
# =================================================
if view == "RBI Net Liquidity Injected":

    st.markdown("#### RBI Net Liquidity Injected")

    rbi_1 = df_rbi[["DATE-1", "NET LIQ INC TODAY"]].copy()
    rbi_1["DATE-1"] = pd.to_datetime(rbi_1["DATE-1"], format="%d/%m/%Y", errors="coerce")
    rbi_1["NET LIQ INC TODAY"] = pd.to_numeric(
        rbi_1["NET LIQ INC TODAY"].astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    )
    rbi_1 = rbi_1.dropna().sort_values("DATE-1")

    plot_single_line(
        rbi_1.rename(columns={"DATE-1": "Date", "NET LIQ INC TODAY": "Net Liquidity"}),
        x="Date", y="Net Liquidity", title="Net Liquidity Injected",
    )

    rbi_2 = df_rbi[["DATE_2", "AMOUNT"]].copy()
    rbi_2["DATE_2"] = pd.to_datetime(rbi_2["DATE_2"], format="%d/%m/%Y", errors="coerce")
    rbi_2["AMOUNT"] = pd.to_numeric(
        rbi_2["AMOUNT"].astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    )
    rbi_2 = rbi_2.dropna().sort_values("DATE_2")

    plot_single_line(
        rbi_2.rename(columns={"DATE_2": "Date", "AMOUNT": "Amount"}),
        x="Date", y="Amount", title="Durable Liquidity (Amount)",
    )


# =================================================
# INDEX FUTURES OI
# =================================================
if view == "Index Futures OI":

    st.markdown("#### Index Futures OI")

    oi = df_index_oi.copy()
    for dc in ["Date_1", "Date_2", "Date_3", "DATE_4"]:
        oi[dc] = pd.to_datetime(oi[dc], format="%d/%m/%Y", errors="coerce")

    min_date = min(oi[c].dropna().min() for c in ["Date_1", "Date_2", "Date_3", "DATE_4"]).date()
    max_date = max(oi[c].dropna().max() for c in ["Date_1", "Date_2", "Date_3", "DATE_4"]).date()

    start_date, end_date = st.date_input("Date range", [min_date, max_date], label_visibility="collapsed")
    start_dt, end_dt = pd.to_datetime(start_date), pd.to_datetime(end_date)

    def oi_filter(date_col, val_col):
        df_ = oi.loc[(oi[date_col] >= start_dt) & (oi[date_col] <= end_dt), [date_col, val_col]].rename(columns={date_col: "Date"})
        if val_col in df_.columns:
            df_[val_col] = pd.to_numeric(df_[val_col].astype(str).str.replace(",", "", regex=False), errors="coerce")
        return df_.dropna()

    plot_single_line(oi_filter("Date_1", "Index Futures OI"), "Date", "Index Futures OI", title="Index Futures OI")
    plot_single_line(oi_filter("Date_2", "Nifty Futures oi"), "Date", "Nifty Futures oi", title="Nifty Futures OI")
    plot_single_line(oi_filter("Date_3", "total client oi"), "Date", "total client oi", title="Total Client OI")

    client_fii = oi.loc[(oi["DATE_4"] >= start_dt) & (oi["DATE_4"] <= end_dt), ["DATE_4", "Client OI", "FII OI"]].rename(columns={"DATE_4": "Date"})
    for c in ["Client OI", "FII OI"]:
        client_fii[c] = pd.to_numeric(client_fii[c].astype(str).str.replace(",", "", regex=False), errors="coerce")
    client_fii = client_fii.dropna(how="all", subset=["Client OI", "FII OI"])

    fig_cf = px.line(client_fii, x="Date", y=["Client OI", "FII OI"],
                     color_discrete_sequence=[LINE_COLOR, RED],
                     title="Client OI vs FII OI")
    fig_cf.update_traces(line=dict(width=1.8))
    fig_cf.update_layout(**{**PLOT_LAYOUT, "height": 520})
    fig_cf.update_yaxes(tickformat=",", showexponent="none")
    st.plotly_chart(fig_cf, use_container_width=True, config={"displayModeBar": False}, key="oi_client_fii")


# =================================================
# INDEX (PE / PB / DIV YLD)
# =================================================
if view == "Index (PE / PB / DIV YLD)":

    st.markdown("#### Index Valuation Metrics")

    df = df_index_val.copy()
    df = df.loc[:, df.columns != ""]

    for c in ["Date_1", "Date_2", "Date_3"]:
        df[c] = pd.to_datetime(df[c], format="%d/%m/%Y", errors="coerce")
    for c in ["P/E_1", "P/B_1", "Div Yield_1", "P/E_2", "P/B_2", "Div Yield_2", "P/E_3", "P/B_3", "Div Yield_3"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Radio instead of tabs — renders only one index at a time, no hidden-tab width=0 bug
    idx_choice = st.radio(
        "Index",
        ["Nifty 50", "Nifty Midcap 100", "Nifty Smallcap 250"],
        horizontal=True,
        key="idx_radio",
        label_visibility="collapsed",
    )

    if idx_choice == "Nifty 50":
        d = df[["Date_1", "P/E_1", "P/B_1", "Div Yield_1"]].dropna().rename(
            columns={"Date_1": "Date", "P/E_1": "P/E", "P/B_1": "P/B", "Div Yield_1": "Dividend Yield"})
        pfx = "n50"
        label = "Nifty 50"
    elif idx_choice == "Nifty Midcap 100":
        d = df[["Date_2", "P/E_2", "P/B_2", "Div Yield_2"]].dropna().rename(
            columns={"Date_2": "Date", "P/E_2": "P/E", "P/B_2": "P/B", "Div Yield_2": "Dividend Yield"})
        pfx = "mid"
        label = "Midcap 100"
    else:
        d = df[["Date_3", "P/E_3", "P/B_3", "Div Yield_3"]].dropna().rename(
            columns={"Date_3": "Date", "P/E_3": "P/E", "P/B_3": "P/B", "Div Yield_3": "Dividend Yield"})
        pfx = "sc"
        label = "Smallcap 250"

    plot_single_line(d, "Date", "P/E",            title=f"{label} — P/E",            key=f"idx_{pfx}_pe")
    plot_single_line(d, "Date", "P/B",            title=f"{label} — P/B",            key=f"idx_{pfx}_pb")
    plot_single_line(d, "Date", "Dividend Yield", title=f"{label} — Dividend Yield", key=f"idx_{pfx}_div")


# =================================================
# ASSET CLASS CHARTS
# =================================================
if view == "Asset Class Charts":

    st.markdown("#### Asset Class Charts")

    freq = st.radio("Frequency", ["Daily", "Weekly", "Monthly"], horizontal=True)

    base_folder_map = {
        "Daily":   "asset_class_charts/daily",
        "Weekly":  "asset_class_charts/weekly",
        "Monthly": "asset_class_charts/monthly",
    }

    assets = ["DXY", "USDINR", "NIFTYGS10YR", "IN10Y", "GOLD", "SILVER", "UKOIL", "SPX", "EURINR", "AW1", "EEM"]
    tabs = st.tabs(assets)

    for tab, asset in zip(tabs, assets):
        with tab:
            folder = os.path.join(base_folder_map[freq], asset)
            images = get_sorted_images(folder)
            if not images:
                st.info("No charts available.")
            else:
                for img in images:
                    st.image(os.path.join(folder, img))


# =================================================
# METAL CHARTS
# =================================================
if view == "Metal Charts":

    st.markdown("#### Metal Charts")

    freq = st.radio("Frequency", ["Daily", "Weekly", "Monthly"], horizontal=True, key="metal_freq")

    base_folder_map = {
        "Daily":   "metal_charts/daily",
        "Weekly":  "metal_charts/weekly",
        "Monthly": "metal_charts/monthly",
    }

    metals = ["Hindustan Copper", "SAIL", "NMDC", "NMDC Steel", "NALCO", "Coal India",
              "Hindustan Zinc", "Vedanta", "DXY", "stock-dxy"]
    tabs = st.tabs(metals)

    for tab, metal in zip(tabs, metals):
        with tab:
            folder = os.path.join(base_folder_map[freq], metal)
            images = get_sorted_images(folder)
            if not images:
                st.info("No charts available.")
            else:
                for img in images:
                    st.image(os.path.join(folder, img))


# =================================================
# TARIFF TIMELINE
# =================================================
if view == "Tariff Timeline":
    st.markdown("#### Tariff Timeline")
    st.dataframe(df_tariff)


# =================================================
# GLOBAL INTEREST RATES
# =================================================
if view == "Global Interest Rates":

    st.markdown("#### Global Interest Rates")

    rates = df_global_rates.copy()
    date_cols = ["Date_1", "Date_2", "Date_3", "Date_4", "Date_5"]
    int_cols  = ["Int_1",  "Int_2",  "Int_3",  "Int_4",  "Int_5"]

    for c in date_cols:
        if c in rates.columns:
            rates[c] = pd.to_datetime(rates[c], format="%d/%m/%Y", errors="coerce")
    for c in int_cols:
        if c in rates.columns:
            rates[c] = pd.to_numeric(rates[c], errors="coerce")

    tabs = st.tabs(["US", "India", "UK", "China", "Japan"])
    pairs = [("Date_1","Int_1","US"),("Date_2","Int_2","India"),("Date_3","Int_3","UK"),("Date_4","Int_4","China"),("Date_5","Int_5","Japan")]

    for tab, (dc, ic, label) in zip(tabs, pairs):
        with tab:
            df_ = rates[[dc, ic]].dropna().rename(columns={dc: "Date", ic: "Interest Rate"})
            plot_single_line(df_, "Date", "Interest Rate", title=f"{label} Interest Rate")


# =================================================
# INDIA MACROECONOMIC INDICATORS
# =================================================
if view == "India Macroeconomic Indicators":

    st.markdown("#### India Macroeconomic Indicators")

    macro = df_india_macro.copy()
    macro = macro.loc[:, macro.columns != ""]

    def macro_plot(date_col, val_col, title):
        df_ = macro[[date_col, val_col]].copy()
        df_[date_col] = pd.to_datetime(df_[date_col], format="%d/%m/%Y", errors="coerce")
        df_[val_col]  = pd.to_numeric(df_[val_col].astype(str).str.replace(",", "", regex=False).str.strip(), errors="coerce")
        df_ = df_.dropna(subset=[date_col])
        plot_single_line(df_.rename(columns={date_col: "Date", val_col: "Value"}), "Date", "Value", title=title)

    macro_plot("Date_1", "GDP %",         "GDP Growth %")
    macro_plot("Date_2", "INFLATION %",   "Inflation %")
    macro_plot("Date_3", "LOAN Growth %", "Loan Growth %")


# =================================================
# AUTOMOBILE SALES VOLUMES
# =================================================
if view == "Automobile Sales Volumes":

    st.markdown("#### Automobile Sales Volumes")

    auto = df_auto_sales.copy()

    def plot_auto_chart(df, date_col, value_col, title):
        if date_col not in df.columns or value_col not in df.columns:
            st.warning(f"Missing column: {value_col}")
            return
        plot_df = df[[date_col, value_col]].copy()
        plot_df[date_col]  = pd.to_datetime(plot_df[date_col], format="%d/%m/%Y", errors="coerce")
        plot_df[value_col] = pd.to_numeric(plot_df[value_col], errors="coerce")
        plot_df = plot_df.dropna()
        if plot_df.empty:
            st.info(f"No data for {title}")
            return
        plot_single_line(plot_df.rename(columns={date_col: "Date", value_col: "Value"}), "Date", "Value", title=title)

        company_tabs = st.tabs([
        "TMPV",
        "TMCV",
        "M&M",
        "HYUNDAI",
        "FORCE MOTORS",
        "SML MAHINDRA",
        "MARUTI",
        "Atul auto",
        "Ashok Leyland",
        "Bajaj",
        "Hero Motocorp",
        "OLA Electric",
        "Eicher Motors PV",
        "Eicher Motors CV"
        ])

    # Tab 0 — Maruti
    with company_tabs[0]:
        plot_auto_chart(auto, "DATE_1", "TMPV TOTAL", "TMPV – Total Sales")
        plot_auto_chart(auto, "DATE_1", "TMPV DOMESTIC SALES", "TMPV – Domestic Sales")
        plot_auto_chart(auto, "DATE_1", "TMPV INTL SALES", "TMPV – Export Sales")
        plot_auto_chart(auto, "DATE_1", "TMPV EV SALES", "TMPV – EV Sales")
        plot_auto_chart(auto, "DATE_1", "TMPV ICE SALES", "TMPV – ICE Sales")


    # Tab 1 — Hyundai
    with company_tabs[1]:
        plot_auto_chart(auto, "DATE_2", "TMCV TOTAL SALES", "TMCV – Total Sales")
        plot_auto_chart(auto, "DATE_2", "TMCV HCV TRUCKS", "TMCV – HCV Trucks")
        plot_auto_chart(auto, "DATE_2", "TMCV SCV CARGO & PICKUP", "TMCV – SCV Cargo & Pickup")
        plot_auto_chart(auto, "DATE_2", "TMCV ILMCV TRUCKS", "TMCV – LMCV")
        plot_auto_chart(auto, "DATE_2", "TMCV PASSENGER CARRIERS", "TMCV – PASSANGER CARRIERS")
        plot_auto_chart(auto, "DATE_2", "TMCV TOTAL DOMESTIC SALES", "TMCV – TOTAL DOMESTIC SALES")
        plot_auto_chart(auto, "DATE_2", "TMCV INTL BUSINESS", "TMCV – INTL BUSINESS")

    # Tab 2 — Tata Motors
    with company_tabs[2]:
        plot_auto_chart(auto, "DATE_3", "M&M UTILITY VEHICLES", "M&M – UTILITY VEHICLES")
        plot_auto_chart(auto, "DATE_3", "M&M CARS+VANS", "M&M – CARS+VANS")
        plot_auto_chart(auto, "DATE_3", "M&M TOTAL PV", "M&M – TOTAL PV")
        plot_auto_chart(auto, "DATE_3", "M&M LCV < 2T", "M&M – LCV < 2T")
        plot_auto_chart(auto, "DATE_3", "M&M LCV 2-3.5T", "M&M – M&M LCV 2-3.5T")
        plot_auto_chart(auto, "DATE_3", "M&M LCV 3.5 + MHCV", "M&M – LCV 3.5 + MHCV")
        plot_auto_chart(auto, "DATE_3", "M&M 3 W INC EV", "M&M – 3 W INC EV")
        plot_auto_chart(auto, "DATE_3", "M&M DOMESTIC CV", "M&M – DOMESTIC CV")
        plot_auto_chart(auto, "DATE_3", "M&M TOTAL EXPORT", "M&M – TOTAL EXPORT")
        plot_auto_chart(auto, "DATE_3", "M&M TOTAL SALES", "M&M – TOTAL SALES")
        plot_auto_chart(auto, "DATE_3", "M&M TRACTOR DOMESTIC", "M&M – TRACTOR DOMESTIC")
        plot_auto_chart(auto, "DATE_3", "M&M TOTAL EXPORT", "M&M – TRACTOR EXPORT")
        plot_auto_chart(auto, "DATE_3", "M&M TRACTOR TOTAL", "M&M – TRACTOR TOTAL")



    # Tab 3 — M&M
    with company_tabs[3]:
        plot_auto_chart(auto, "DATE_4", "HYUNDAI TOTAL SALES", "Hyundai – Total Sales")
        plot_auto_chart(auto, "DATE_4", "HYUNDAI DOMESTIC SALES", "Hyundai – Domestic Sales")
        plot_auto_chart(auto, "DATE_4", "HYUNDAI EXPORT SALES", "Hyundai – Export Sales")

    # Tab 4 — Kia
    with company_tabs[4]:
        plot_auto_chart(auto, "DATE_5", "FORCE TOTAL SALES", "Force Motors – Total Sales")
        plot_auto_chart(auto, "DATE_5", "FORCE DOMESTIC SALES", "Force – Domestic Sales")
        plot_auto_chart(auto, "DATE_5", "FORCE EXPORTSALES", "Force – Export Sales")


    # Tab 5 — Toyota
    with company_tabs[5]:
        plot_auto_chart(auto, "DATE_6", "SML MAHINDRA TOTAL SALES", "SML Mahindra – Total Sales")
        plot_auto_chart(auto, "DATE_6", "SML MAHINDRA CV", "SML Mahindra – CV")
        plot_auto_chart(auto, "DATE_6", "SML MAHINDRA PV", "SML Mahindra – PV")
        
    # Tab 6 — MSIL
    with company_tabs[6]:
        plot_auto_chart(auto, "DATE_7", "MARUTI PV", "Maruti – PV")
        plot_auto_chart(auto, "DATE_7", "MARUTI LCV", "Maruti – LCV")
        plot_auto_chart(auto, "DATE_7", "MARUTI OEM", "Maruti – OEM")
        plot_auto_chart(auto, "DATE_7", "MARUTI EXPORT", "Maruti – Export")
        plot_auto_chart(auto, "DATE_7", "MARUTI TOTAL SALES", "Maruti – TOTAL SALES")


    # Tab 7 — Atul Auto
    with company_tabs[7]:
        plot_auto_chart(auto, "DATE_8", "ATUL Domestic 3w - IC Engine", "ATUL Domestic 3w - IC Engine")
        plot_auto_chart(auto, "DATE_8", "ATUL Domestic EV L3", "ATUL Domestic EV L3")
        plot_auto_chart(auto, "DATE_8", "ATUL Domestic EV L5", "ATUL Domestic EV L5")
        plot_auto_chart(auto, "DATE_8", "ATUL Total Domestic sales", "ATUL Total Domestic sales")
        plot_auto_chart(auto, "DATE_8", "ATUL Export 3w - IC Engine", "ATUL Export 3w - IC Engine")
        plot_auto_chart(auto, "DATE_8", "ATUL Export EV L5", "ATUL Export EV L5")
        plot_auto_chart(auto, "DATE_8", "ATUL Total 3w - IC Engine", "ATUL Total 3w - IC Engine")
        plot_auto_chart(auto, "DATE_8", "ATUL Total EV L3", "ATUL Total EV L3")
        plot_auto_chart(auto, "DATE_8", "ATUL Total EV L5", "ATUL Total EV L5")
        plot_auto_chart(auto, "DATE_8", "ATUL Total sales D+E", "ATUL Total sales D+E")

    # Tab 8 — Ashok Leyland
    with company_tabs[8]:
        plot_auto_chart(auto, "DATE_9", "AL DOMESTIC M&HCV TRUCKS", "AL DOMESTIC M&HCV TRUCKS")
        plot_auto_chart(auto, "DATE_9", "AL DOMESTIC M&HCV BUS", "AL DOMESTIC M&HCV BUS")
        plot_auto_chart(auto, "DATE_9", "AL Total DOMESTIC M&HCV", "AL Total DOMESTIC M&HCV")
        plot_auto_chart(auto, "DATE_9", "AL DOMESTIC LCV", "AL DOMESTIC LCV")
        plot_auto_chart(auto, "DATE_9", "AL TOTAL DOMESTIC VEHICLES", "AL TOTAL DOMESTIC VEHICLES")
        plot_auto_chart(auto, "DATE_9", "AL EXPORT M&HCV TRUCKS", "AL EXPORT M&HCV TRUCKS")
        plot_auto_chart(auto, "DATE_9", "AL EXPORT M&HCV BUS", "AL EXPORT M&HCV BUS")
        plot_auto_chart(auto, "DATE_9", "AL TOTAL M&HCV EXPORT", "AL TOTAL M&HCV EXPORT")
        plot_auto_chart(auto, "DATE_9", "AL EXPORT LCV", "AL EXPORT LCV")
        plot_auto_chart(auto, "DATE_9", "AL M&HCV TRUCKS D+E", "AL M&HCV TRUCKS D+E")
        plot_auto_chart(auto, "DATE_9", "AL M&HCV BUS D+E", "AL M&HCV BUS D+E")
        plot_auto_chart(auto, "DATE_9", "AL TOTAL D+E", "AL TOTAL D+E")
        plot_auto_chart(auto, "DATE_9", "AL LCV D+E", "AL LCV D+E")
        plot_auto_chart(auto, "DATE_9", "AL TOTAL VEHICLES D+E", "AL TOTAL VEHICLES D+E")

    # Tab 9 — Bajaj Auto
    with company_tabs[9]:
        plot_auto_chart(auto, "DATE_10", "Bajaj 2W Domestic", "Bajaj 2W Domestic")
        plot_auto_chart(auto, "DATE_10", "Bajaj 2W Export", "Bajaj 2W Export")
        plot_auto_chart(auto, "DATE_10", "Bajaj Total 2W D+E", "Bajaj Total 2W D+E")
        plot_auto_chart(auto, "DATE_10", "Bajaj CV Domestic", "Bajaj CV Domestic")
        plot_auto_chart(auto, "DATE_10", "Bajaj CV Export", "Bajaj CV Export")
        plot_auto_chart(auto, "DATE_10", "Bajaj Total CV D+E", "Bajaj Total CV D+E")
        plot_auto_chart(auto, "DATE_10", "Bajaj Total Domestic Sales", "Bajaj Total Domestic Sales")
        plot_auto_chart(auto, "DATE_10", "Bajaj Total Export Sales", "Bajaj Total Export Sales")
        plot_auto_chart(auto, "DATE_10", "Bajaj Total Sales D+E", "Bajaj Total Sales D+E")

    # Tab 10 — Hero MotoCorp
    with company_tabs[10]:
        plot_auto_chart(auto, "DATE_11", "Hero Motorcycles Total", "Hero Motorcycles Total")
        plot_auto_chart(auto, "DATE_11", "Hero Scooters Total", "Hero Scooters Total")
        plot_auto_chart(auto, "DATE_11", "Hero Total Sales D+E", "Hero Total Sales D+E")
        plot_auto_chart(auto, "DATE_11", "Hero Domestic Sales", "Hero Domestic Sales")
        plot_auto_chart(auto, "DATE_11", "Hero Export Sales", "Hero Export Sales")
        
    # Tab 11 — OLA Electric
    with company_tabs[11]:
        plot_auto_chart(auto, "DATE_12", "OLA Total Sales", "OLA Total Sales")
        
    # Tab 12 — Eicher PV
    with company_tabs[12]:
        plot_auto_chart(auto, "DATE_13", "Eicher Less than 350 cc", "Eicher Less than 350 cc")
        plot_auto_chart(auto, "DATE_13", "Eicher greater than 350 cc", "Eicher greater than 350 cc")
        plot_auto_chart(auto, "DATE_13", "Eicher Total Sales", "Eicher Total Sales")
        plot_auto_chart(auto, "DATE_13", "Eicher Total Export", "Eicher Total Export")

    # Tab 13 — Eicher CV
    with company_tabs[13]:
        plot_auto_chart(auto, "DATE_14", "Eicher CV Domestic sales", "Eicher CV Domestic sales")
        plot_auto_chart(auto, "DATE_14", "Eicher CV Export Sales", "Eicher CV Export Sales")
        plot_auto_chart(auto, "DATE_14", "Eicher CV Volvo Sales", "Eicher CV Volvo Sales")
        plot_auto_chart(auto, "DATE_14", "Eicher CV Total Sales D+E", "Eicher CV Total Sales D+E")


# =================================================
# MAGAZINE COVER
# =================================================
if view == "Magazine Cover":

    st.markdown("#### Magazine Cover")

    tab1, tab2 = st.tabs(["India", "Others"])

    with tab1:
        folder = "magazine_cover/india"
        images = get_sorted_images(folder)
        if not images:
            st.info("No India covers available.")
        else:
            cols = st.columns(3)
            for i, img in enumerate(images):
                with cols[i % 3]:
                    st.image(os.path.join(folder, img))

    with tab2:
        folder = "magazine_cover/others"
        images = get_sorted_images(folder)
        if not images:
            st.info("No other covers available.")
        else:
            cols = st.columns(3)
            for i, img in enumerate(images):
                with cols[i % 3]:
                    st.image(os.path.join(folder, img))


# =================================================
# MULTIASSET CHART (ONE VIEW)
# =================================================
if view == "Multiasset Chart (One View)":

    st.markdown("#### Multiasset Chart — One View")

    def show_images_grid(folder):
        images = get_sorted_images(folder)
        if not images:
            st.info("No images available.")
            return
        cols = st.columns(3)
        for i, img in enumerate(images):
            with cols[i % 3]:
                st.image(os.path.join(folder, img))

    tab1, tab2, tab3 = st.tabs(["Main", "Broad Indices", "Sectoral Indices"])

    with tab1:
        show_images_grid("multiasset_charts/main")
    with tab2:
        show_images_grid("multiasset_charts/broad_indices")
    with tab3:
        show_images_grid("multiasset_charts/sectoral_indices")


# =================================================
# NET MTF OUTSTANDING
# =================================================
if view == "Net MTF Outstanding":

    st.markdown("#### Net MTF Outstanding")

    mtf = df_mtf.copy()
    mtf = mtf.loc[:, mtf.columns != ""]

    DATE_COL  = mtf.columns[0]
    VALUE_COL = mtf.columns[1]

    df_plot = mtf[[DATE_COL, VALUE_COL]].copy()
    df_plot[DATE_COL]  = pd.to_datetime(df_plot[DATE_COL], format="%d/%m/%Y", errors="coerce")
    df_plot[VALUE_COL] = pd.to_numeric(
        df_plot[VALUE_COL].astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce"
    )
    df_plot = df_plot.dropna(subset=[DATE_COL])

    plot_single_line(
        df_plot.rename(columns={DATE_COL: "Date", VALUE_COL: "Net MTF Outstanding"}),
        "Date", "Net MTF Outstanding", title="Net MTF Outstanding",
    )
