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
    padding: 2.5rem 0.3rem 4rem 0.3rem !important;
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


def plot_single_line(df, x, y, height=CHART_HEIGHT, y_label=None, title=None,
                     color=None, key=None, date_range=None):
    # Apply date range filter if provided
    if date_range is not None and x in df.columns:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        df = df[(df[x] >= start) & (df[x] <= end)]

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


# Load all data once per session — stored in session_state so switching
# views never triggers a re-fetch and never hits the Google Sheets API again.
if "data_loaded" not in st.session_state:
    with st.spinner("Loading data from Google Sheets…"):
        (
            st.session_state.df_main,
            st.session_state.df_rbi,
            st.session_state.df_index_oi,
            st.session_state.df_index_val,
            st.session_state.df_tariff,
            st.session_state.df_global_rates,
            st.session_state.df_auto_sales,
            st.session_state.df_india_macro,
            st.session_state.df_mtf,
        ) = load_data()
        st.session_state.data_loaded = True

df_main        = st.session_state.df_main
df_rbi         = st.session_state.df_rbi
df_index_oi    = st.session_state.df_index_oi
df_index_val   = st.session_state.df_index_val
df_tariff      = st.session_state.df_tariff
df_global_rates= st.session_state.df_global_rates
df_auto_sales  = st.session_state.df_auto_sales
df_india_macro = st.session_state.df_india_macro
df_mtf         = st.session_state.df_mtf

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
    "Auto Dashboard",
    "Magazine Cover",
    "Multiasset Chart (One View)",
    "Net MTF Outstanding",
]

col1, col2 = st.columns([6, 1])
with col1:
    view = st.selectbox("View", VIEWS, label_visibility="collapsed")


def date_filter_widget(df_dates, key):
    """Render a date range + timeframe selector. Returns (start, end, resample_freq)."""
    d_min = df_dates.min().date() if not df_dates.empty else pd.Timestamp("2010-01-01").date()
    d_max = df_dates.max().date() if not df_dates.empty else pd.Timestamp.today().date()
    c1, c2 = st.columns([4, 1])
    with c1:
        dr = st.date_input("Date range", [d_min, d_max],
                           min_value=d_min, max_value=d_max,
                           key=f"dr_{key}", label_visibility="collapsed")
    with c2:
        tf = st.selectbox("TF", ["D", "W", "M", "Q", "Y"],
                          key=f"tf_{key}", label_visibility="collapsed")
    start = pd.to_datetime(dr[0]) if len(dr) == 2 else pd.to_datetime(d_min)
    end   = pd.to_datetime(dr[1]) if len(dr) == 2 else pd.to_datetime(d_max)
    tf_map = {"D": None, "W": "W", "M": "ME", "Q": "QE", "Y": "YE"}
    return start, end, tf_map[tf]


def apply_tf(df, date_col, freq):
    """Resample a dataframe by frequency using last value of each period."""
    if freq is None or df.empty:
        return df
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    df = df.set_index(date_col).sort_index()
    df = df[numeric_cols].resample(freq).last().dropna(how="all").reset_index()
    return df


with col2:
    if st.button("↺ Refresh", help="Reload data from Google Sheets"):
        del st.session_state.data_loaded
        st.rerun()

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

    # prefix makes every chart key unique per dataset selection
    prefix = breadth_choice.replace(" ", "_").lower()

    start_br, end_br, tf_br = date_filter_widget(data[m["date"]].dropna(), f"br_{prefix}")

    filtered = data[
        (data[m["date"]] >= start_br) &
        (data[m["date"]] <= end_br)
    ].copy()

    filtered_r = apply_tf(filtered, m["date"], tf_br)

    plot_df1 = filtered_r[[m["date"], m["high"], m["low"]]].rename(
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

    plot_single_line(filtered_r.rename(columns={m["date"]: "Date", m["hl"]: "HIGH/LOW RATIO"}),
                     "Date", "HIGH/LOW RATIO", title="High / Low Ratio", key=f"{prefix}_hlr")
    plot_single_line(filtered_r.rename(columns={m["date"]: "Date", m["hr"]: "HIGH / EMA 200"}),
                     "Date", "HIGH / EMA 200", title="High / EMA 200", color=GREEN, key=f"{prefix}_hr")
    plot_single_line(filtered_r.rename(columns={m["date"]: "Date", m["lr"]: "LOW / EMA 200"}),
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
    rbi_1 = rbi_1.dropna().sort_values("DATE-1").rename(columns={"DATE-1": "Date", "NET LIQ INC TODAY": "Net Liquidity"})

    rbi_2 = df_rbi[["DATE_2", "AMOUNT"]].copy()
    rbi_2["DATE_2"] = pd.to_datetime(rbi_2["DATE_2"], format="%d/%m/%Y", errors="coerce")
    rbi_2["AMOUNT"] = pd.to_numeric(rbi_2["AMOUNT"].astype(str).str.replace(",", "", regex=False), errors="coerce")
    rbi_2 = rbi_2.dropna().sort_values("DATE_2").rename(columns={"DATE_2": "Date", "AMOUNT": "Amount"})

    start_rbi, end_rbi, tf_rbi = date_filter_widget(pd.concat([rbi_1["Date"], rbi_2["Date"]]).dropna(), "rbi")
    plot_single_line(apply_tf(rbi_1, "Date", tf_rbi), x="Date", y="Net Liquidity", title="Net Liquidity Injected", date_range=(start_rbi, end_rbi), key="rbi_netliq")
    plot_single_line(apply_tf(rbi_2, "Date", tf_rbi), x="Date", y="Amount", title="Durable Liquidity (Amount)", date_range=(start_rbi, end_rbi), key="rbi_amount")


# =================================================
# INDEX FUTURES OI
# =================================================
if view == "Index Futures OI":

    st.markdown("#### Index Futures OI")

    oi = df_index_oi.copy()
    for dc in ["Date_1", "Date_2", "Date_3", "DATE_4"]:
        oi[dc] = pd.to_datetime(oi[dc], format="%d/%m/%Y", errors="coerce")

    all_oi_dates = pd.concat([oi[c].dropna() for c in ["Date_1","Date_2","Date_3","DATE_4"]])
    start_dt, end_dt, tf_oi = date_filter_widget(all_oi_dates, "oi")

    def oi_filter(date_col, val_col):
        df_ = oi.loc[(oi[date_col] >= start_dt) & (oi[date_col] <= end_dt), [date_col, val_col]].rename(columns={date_col: "Date"})
        if val_col in df_.columns:
            df_[val_col] = pd.to_numeric(df_[val_col].astype(str).str.replace(",", "", regex=False), errors="coerce")
        return df_.dropna()

    plot_single_line(apply_tf(oi_filter("Date_1", "Index Futures OI"), "Date", tf_oi), "Date", "Index Futures OI", title="Index Futures OI", key="oi1")
    plot_single_line(apply_tf(oi_filter("Date_2", "Nifty Futures oi"), "Date", tf_oi), "Date", "Nifty Futures oi", title="Nifty Futures OI", key="oi2")
    plot_single_line(apply_tf(oi_filter("Date_3", "total client oi"), "Date", tf_oi), "Date", "total client oi", title="Total Client OI", key="oi3")

    client_fii = oi.loc[(oi["DATE_4"] >= start_dt) & (oi["DATE_4"] <= end_dt), ["DATE_4", "Client OI", "FII OI"]].rename(columns={"DATE_4": "Date"})
    for c in ["Client OI", "FII OI"]:
        client_fii[c] = pd.to_numeric(client_fii[c].astype(str).str.replace(",", "", regex=False), errors="coerce")
    client_fii = apply_tf(client_fii.dropna(how="all", subset=["Client OI", "FII OI"]), "Date", tf_oi)

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
        df[c] = pd.to_datetime(df[c], format="%d-%m-%Y", errors="coerce")
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
        d = df[["Date_1", "P/E_1", "P/B_1", "Div Yield_1"]].dropna(subset=["Date_1"]).rename(
            columns={"Date_1": "Date", "P/E_1": "P/E", "P/B_1": "P/B", "Div Yield_1": "Dividend Yield"})
        pfx = "n50"
        label = "Nifty 50"
    elif idx_choice == "Nifty Midcap 100":
        d = df[["Date_2", "P/E_2", "P/B_2", "Div Yield_2"]].dropna(subset=["Date_2"]).rename(
            columns={"Date_2": "Date", "P/E_2": "P/E", "P/B_2": "P/B", "Div Yield_2": "Dividend Yield"})
        pfx = "mid"
        label = "Midcap 100"
    else:
        d = df[["Date_3", "P/E_3", "P/B_3", "Div Yield_3"]].dropna(subset=["Date_3"]).rename(
            columns={"Date_3": "Date", "P/E_3": "P/E", "P/B_3": "P/B", "Div Yield_3": "Dividend Yield"})
        pfx = "sc"
        label = "Smallcap 250"

    start_idx, end_idx, tf_idx = date_filter_widget(d["Date"].dropna(), f"idx_{pfx}")
    d_tf = apply_tf(d, "Date", tf_idx)
    plot_single_line(d_tf, "Date", "P/E",            title=f"{label} — P/E",            key=f"idx_{pfx}_pe",  date_range=(start_idx, end_idx))
    plot_single_line(d_tf, "Date", "P/B",            title=f"{label} — P/B",            key=f"idx_{pfx}_pb",  date_range=(start_idx, end_idx))
    plot_single_line(d_tf, "Date", "Dividend Yield", title=f"{label} — Dividend Yield", key=f"idx_{pfx}_div", date_range=(start_idx, end_idx))


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
              "Hindustan Zinc", "Vedanta", "DXY"]
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
            # Format is "1-1-1972" = day-month-year with no zero padding
            rates[c] = pd.to_datetime(rates[c], format="%d-%m-%Y", errors="coerce")
    for c in int_cols:
        if c in rates.columns:
            rates[c] = pd.to_numeric(rates[c], errors="coerce")

    country_map = {
        "US":    ("Date_1", "Int_1"),
        "India": ("Date_2", "Int_2"),
        "UK":    ("Date_3", "Int_3"),
        "China": ("Date_4", "Int_4"),
        "Japan": ("Date_5", "Int_5"),
    }

    country = st.radio("Country", list(country_map.keys()), horizontal=True,
                       key="rates_radio", label_visibility="collapsed")
    dc, ic = country_map[country]
    if dc in rates.columns and ic in rates.columns:
        df_ = rates[[dc, ic]].dropna().rename(columns={dc: "Date", ic: "Interest Rate"})
        plot_single_line(df_, "Date", "Interest Rate",
                         title=f"{country} Interest Rate", key=f"rates_{country}")
    else:
        st.info("No data available.")


# =================================================
# INDIA MACROECONOMIC INDICATORS
# =================================================
if view == "India Macroeconomic Indicators":

    st.markdown("#### India Macroeconomic Indicators")

    macro = df_india_macro.copy()
    macro = macro.loc[:, macro.columns != ""]

    def macro_prep(date_col, val_col):
        df_ = macro[[date_col, val_col]].copy()
        df_[date_col] = pd.to_datetime(df_[date_col], format="%d/%m/%Y", errors="coerce")
        df_[val_col]  = pd.to_numeric(df_[val_col].astype(str).str.replace(",", "", regex=False).str.strip(), errors="coerce")
        return df_.dropna(subset=[date_col]).rename(columns={date_col: "Date", val_col: "Value"})

    gdp  = macro_prep("Date_1", "GDP %")
    infl = macro_prep("Date_2", "INFLATION %")
    loan = macro_prep("Date_3", "LOAN Growth %")

    all_macro = pd.concat([gdp["Date"], infl["Date"], loan["Date"]]).dropna()
    start_m, end_m, tf_m = date_filter_widget(all_macro, "macro")

    plot_single_line(gdp,  "Date", "Value", title="GDP Growth %",  date_range=(start_m, end_m), key="macro_gdp")
    plot_single_line(infl, "Date", "Value", title="Inflation %",   date_range=(start_m, end_m), key="macro_infl")
    plot_single_line(loan, "Date", "Value", title="Loan Growth %", date_range=(start_m, end_m), key="macro_loan")



def compute_fy_raw(raw_dict):
    """Group monthly RAW series into Indian financial year (Apr-Mar) totals."""
    fy_raw = {}
    for co, series in raw_dict.items():
        dates, values = series["dates"], series["values"]
        fy_map = {}
        for d, v in zip(dates, values):
            yr, mo = int(d[:4]), int(d[5:7])
            fy_start = yr if mo >= 4 else yr - 1
            label = f"FY{str(fy_start)[2:]}-{str(fy_start+1)[2:]}"
            fy_map[label] = fy_map.get(label, 0) + v
        sorted_fy = sorted(fy_map.items())
        fy_raw[co] = {"years": [x[0] for x in sorted_fy], "values": [x[1] for x in sorted_fy]}
    return fy_raw

def compute_cy_total(raw_dict, latest_month):
    """Sum Apr of current FY up to latest_month for each company."""
    yr, mo = int(latest_month[:4]), int(latest_month[5:7])
    fy_start = yr if mo >= 4 else yr - 1
    fy_apr = f"{fy_start}-04"
    cy = {}
    for co, series in raw_dict.items():
        cy[co] = sum(v for d, v in zip(series["dates"], series["values"]) if fy_apr <= d <= latest_month)
    return cy

# =================================================
# AUTO DASHBOARD
# =================================================
if view == "Auto Dashboard":
    import json
    import streamlit.components.v1 as _components

    auto = df_auto_sales.copy()

    # ── helper: parse a column into {dates: ["YYYY-MM",...], values: [...]} ──
    def to_series(df, date_col, val_col):
        if date_col not in df.columns or val_col not in df.columns:
            return {"dates": [], "values": []}
        tmp = df[[date_col, val_col]].copy()
        # Try 4-digit year first (01-Jan-2014), then 2-digit (01-Jan-26)
        parsed = pd.to_datetime(tmp[date_col], format="%d-%b-%Y", errors="coerce")
        mask = parsed.isna()
        if mask.any():
            parsed[mask] = pd.to_datetime(tmp[date_col][mask], format="%d-%b-%y", errors="coerce")
        tmp[date_col] = parsed
        tmp[val_col]  = pd.to_numeric(
            tmp[val_col].astype(str).str.replace(",", "", regex=False).str.strip(),
            errors="coerce"
        )
        tmp = tmp.dropna()
        tmp = tmp.sort_values(date_col)
        return {
            "dates":  tmp[date_col].dt.strftime("%Y-%m").tolist(),
            "values": tmp[val_col].astype(int).tolist(),
        }

    # ── Build RAW — one "Total" series per company used by the dashboard ──
    RAW = {
        "Tata Motors PV": to_series(auto, "DATE_1", "TMPV TOTAL"),
        "Tata Motors CV": to_series(auto, "DATE_2", "TMCV TOTAL SALES"),
        "Mahindra":       to_series(auto, "DATE_3", "M&M TOTAL PV"),
        "Hyundai":        to_series(auto, "DATE_4", "HYUNDAI TOTAL SALES"),
        "Force Motors":   to_series(auto, "DATE_5", "FORCE TOTAL SALES"),
        "SML Mahindra":   to_series(auto, "DATE_6", "SML MAHINDRA TOTAL SALES"),
        "Maruti":         to_series(auto, "DATE_7", "MARUTI TOTAL SALES"),
        "Atul Auto":      to_series(auto, "DATE_8", "ATUL Total sales D+E"),
        "Ashok Leyland":  to_series(auto, "DATE_9", "AL total vehicles"),
        "Bajaj":          to_series(auto, "DATE_10", "Bajaj Total Sales D+E"),
        "Hero":           to_series(auto, "DATE_11", "Hero Total Sales D+E"),
        "OLA":            to_series(auto, "DATE_12", "OLA Total Sales"),
        "Eicher 2W":      to_series(auto, "DATE_13", "Eicher Total Sales"),
        "Eicher CV":      to_series(auto, "DATE_14", "Eicher CV Total Sales D+E"),
        "TVS":            to_series(auto, "DATE_15", "TVS TOTAL SALES"),
        "TVS 3W":         to_series(auto, "DATE_15", "TVS 3W (TOTAL)"),
    }

    # ── DETAIL — sub-series for drill-down modals ──
    DETAIL = {
        "Tata Motors PV": {
            "Total":    to_series(auto, "DATE_1", "TMPV TOTAL"),
            "Domestic": to_series(auto, "DATE_1", "TMPV DOMESTIC SALES"),
            "Export":   to_series(auto, "DATE_1", "TMPV INTL SALES"),
            "EV Sales": to_series(auto, "DATE_1", "TMPV EV SALES"),
            "ICE Sales":to_series(auto, "DATE_1", "TMPV ICE SALES"),
        },
        "Tata Motors CV": {
            "Total":              to_series(auto, "DATE_2", "TMCV TOTAL SALES"),
            "Domestic":           to_series(auto, "DATE_2", "TMCV TOTAL DOMESTIC SALES"),
            "Intl Business":      to_series(auto, "DATE_2", "TMCV INTL BUSINESS"),
            "HCV Trucks":         to_series(auto, "DATE_2", "TMCV HCV TRUCKS"),
            "ILMCV Trucks":       to_series(auto, "DATE_2", "TMCV ILMCV TRUCKS"),
            "Passenger Carriers": to_series(auto, "DATE_2", "TMCV PASSENGER CARRIERS"),
            "SCV/Pickup":         to_series(auto, "DATE_2", "TMCV SCV CARGO & PICKUP"),
        },
        "Mahindra": {
            "Total":          to_series(auto, "DATE_3", "M&M TOTAL SALES"),
            "Utility Vehicles": to_series(auto, "DATE_3", "M&M UTILITY VEHICLES"),
            "Total PV":       to_series(auto, "DATE_3", "M&M TOTAL PV"),
            "Domestic CV":    to_series(auto, "DATE_3", "M&M DOMESTIC CV"),
            "Export":         to_series(auto, "DATE_3", "M&M TOTAL EXPORT"),
            "LCV <2T":        to_series(auto, "DATE_3", "M&M LCV < 2T"),
            "LCV 2-3.5T":     to_series(auto, "DATE_3", "M&M LCV 2-3.5T"),
            "3W EV":          to_series(auto, "DATE_3", "M&M 3 W INC EV"),
            "Tractor Domestic": to_series(auto, "DATE_3", "M&M TRACTOR DOMESTIC"),
            "Tractor Export": to_series(auto, "DATE_3", "M&M TRACTOR EXPORT"),
            "Tractor Total":  to_series(auto, "DATE_3", "M&M TRACTOR TOTAL"),
        },
        "Hyundai": {
            "Total":    to_series(auto, "DATE_4", "HYUNDAI TOTAL SALES"),
            "Domestic": to_series(auto, "DATE_4", "HYUNDAI DOMESTIC SALES"),
            "Export":   to_series(auto, "DATE_4", "HYUNDAI EXPORT SALES"),
        },
        "Force Motors": {
            "Total":    to_series(auto, "DATE_5", "FORCE TOTAL SALES"),
            "Domestic": to_series(auto, "DATE_5", "FORCE DOMESTIC SALES"),
            "Export":   to_series(auto, "DATE_5", "FORCE EXPORTSALES"),
        },
        "SML Mahindra": {
            "Total": to_series(auto, "DATE_6", "SML MAHINDRA TOTAL SALES"),
            "CV":    to_series(auto, "DATE_6", "SML MAHINDRA CV"),
            "PV":    to_series(auto, "DATE_6", "SML MAHINDRA PV"),
        },
        "Maruti": {
            "Total":  to_series(auto, "DATE_7", "MARUTI TOTAL SALES"),
            "PV":     to_series(auto, "DATE_7", "MARUTI PV"),
            "LCV":    to_series(auto, "DATE_7", "MARUTI LCV"),
            "OEM":    to_series(auto, "DATE_7", "MARUTI OEM"),
            "Export": to_series(auto, "DATE_7", "MARUTI EXPORT"),
        },
        "Atul Auto": {
            "Total":    to_series(auto, "DATE_8", "ATUL Total sales D+E"),
            "Domestic": to_series(auto, "DATE_8", "ATUL Total Domestic sales"),
            "IC Engine":to_series(auto, "DATE_8", "ATUL Total 3w - IC Engine"),
            "EV L3":    to_series(auto, "DATE_8", "ATUL Total EV L3"),
            "EV L5":    to_series(auto, "DATE_8", "ATUL Total EV L5"),
            "Export":   to_series(auto, "DATE_8", "ATUL Export 3w - IC Engine"),
        },
        "Ashok Leyland": {
            "Total":          to_series(auto, "DATE_9", "AL total vehicles"),
            "Domestic":       to_series(auto, "DATE_9", "AL TOTAL DOMESTIC VEHICLES"),
            "M&HCV Trucks":   to_series(auto, "DATE_9", "AL DOMESTIC M&HCV TRUCKS"),
            "M&HCV Bus":      to_series(auto, "DATE_9", "AL DOMESTIC M&HCV BUS"),
            "LCV":            to_series(auto, "DATE_9", "AL DOMESTIC LCV"),
            "Export M&HCV":   to_series(auto, "DATE_9", "AL TOTAL M&HCV EXPORT"),
        },
        "Bajaj": {
            "Total":          to_series(auto, "DATE_10", "Bajaj Total Sales D+E"),
            "2W Domestic":    to_series(auto, "DATE_10", "Bajaj 2W Domestic"),
            "2W Export":      to_series(auto, "DATE_10", "Bajaj 2W Export"),
            "Total 2W":       to_series(auto, "DATE_10", "Bajaj Total 2W D+E"),
            "CV Domestic":    to_series(auto, "DATE_10", "Bajaj CV Domestic"),
            "CV Export":      to_series(auto, "DATE_10", "Bajaj CV Export"),
            "Total CV":       to_series(auto, "DATE_10", "Bajaj Total CV D+E"),
        },
        "Hero": {
            "Total":       to_series(auto, "DATE_11", "Hero Total Sales D+E"),
            "Domestic":    to_series(auto, "DATE_11", "Hero Domestic Sales"),
            "Export":      to_series(auto, "DATE_11", "Hero Export Sales"),
            "Motorcycles": to_series(auto, "DATE_11", "Hero Motorcycles Total"),
            "Scooters":    to_series(auto, "DATE_11", "Hero Scooters Total"),
        },
        "OLA": {
            "Total": to_series(auto, "DATE_12", "OLA Total Sales"),
        },
        "Eicher 2W": {
            "Total":   to_series(auto, "DATE_13", "Eicher Total Sales"),
            "<350cc":  to_series(auto, "DATE_13", "Eicher Less than 350 cc"),
            ">350cc":  to_series(auto, "DATE_13", "Eicher greater than 350 cc"),
            "Export":  to_series(auto, "DATE_13", "Eicher Total Export"),
        },
        "Eicher PV": {
            "Total":   to_series(auto, "DATE_13", "Eicher Total Sales"),
            "<350cc":  to_series(auto, "DATE_13", "Eicher Less than 350 cc"),
            ">350cc":  to_series(auto, "DATE_13", "Eicher greater than 350 cc"),
            "Export":  to_series(auto, "DATE_13", "Eicher Total Export"),
        },
        "Eicher CV": {
            "Total":    to_series(auto, "DATE_14", "Eicher CV Total Sales D+E"),
            "Domestic": to_series(auto, "DATE_14", "Eicher CV Domestic sales"),
            "Export":   to_series(auto, "DATE_14", "Eicher CV Export Sales"),
            "Volvo":    to_series(auto, "DATE_14", "Eicher CV Volvo Sales"),
        },
        "TVS 3W": {
            "Total":    to_series(auto, "DATE_15", "TVS 3W (TOTAL)"),
            "Domestic": to_series(auto, "DATE_15", "TVS 3W DOMESTIC"),
            "Export":   to_series(auto, "DATE_15", "TVS 3W EXPORT"),
        },
        "TVS": {
            "Total":          to_series(auto, "DATE_15", "TVS TOTAL SALES"),
            "2W Total":       to_series(auto, "DATE_15", "TVS 2W (TOTAL)"),
            "3W Total":       to_series(auto, "DATE_15", "TVS 3W (TOTAL)"),
            "Motorcycle":     to_series(auto, "DATE_15", "TVS MOTORCYCLE (TOTAL)"),
            "Scooter":        to_series(auto, "DATE_15", "TVS SCOOTER (TOTAL)"),
            "EV":             to_series(auto, "DATE_15", "TVS EV (TOTAL)"),
            "Domestic":       to_series(auto, "DATE_15", "TVS TOTAL DOMESTIC"),
            "Export":         to_series(auto, "DATE_15", "TVS TOTAL EXPORT"),
            "2W Domestic":    to_series(auto, "DATE_15", "TVS 2W DOMESTIC"),
            "3W Domestic":    to_series(auto, "DATE_15", "TVS 3W DOMESTIC"),
            "2W Export":      to_series(auto, "DATE_15", "TVS 2W EXPORT"),
            "3W Export":      to_series(auto, "DATE_15", "TVS 3W EXPORT"),
        },
    }

    # ── EV_RAW ──
    EV_RAW = {
        "Tata EV":       to_series(auto, "DATE_1",  "TMPV EV SALES"),
        "Mahindra 3W EV":to_series(auto, "DATE_3",  "M&M 3 W INC EV"),
        "OLA Electric":  to_series(auto, "DATE_12", "OLA Total Sales"),
        "Atul EV":       to_series(auto, "DATE_8",  "ATUL Total EV L3"),
        "Tata ICE":      to_series(auto, "DATE_1",  "TMPV ICE SALES"),
        "TVS EV":        to_series(auto, "DATE_15", "TVS EV (TOTAL)"),
    }

    # ── TR_RAW ──
    TR_RAW = {
        "M&M Tractor":          to_series(auto, "DATE_3", "M&M TRACTOR TOTAL"),
        "M&M Tractor Domestic": to_series(auto, "DATE_3", "M&M TRACTOR DOMESTIC"),
        "M&M Tractor Export":   to_series(auto, "DATE_3", "M&M TRACTOR EXPORT"),
    }

    # ── Inject data into the HTML template and render ──
    raw_json    = json.dumps(RAW,    ensure_ascii=False)
    detail_json = json.dumps(DETAIL, ensure_ascii=False)
    ev_json     = json.dumps(EV_RAW, ensure_ascii=False)
    tr_json     = json.dumps(TR_RAW, ensure_ascii=False)

    # Read the HTML template
    template_path = "auto_dashboard_preview.html"
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_template = f.read()

        # Replace the hardcoded data blocks with live data
        import re
        # Replace RAW = {...};
        html_template = re.sub(
            r'const RAW = \{.*?\};',
            f'const RAW = {raw_json};',
            html_template, flags=re.DOTALL, count=1
        )
        # Replace DETAIL = {...};
        html_template = re.sub(
            r'const DETAIL = \{.*?\};',
            f'const DETAIL = {detail_json};',
            html_template, flags=re.DOTALL, count=1
        )
        # Replace EV_RAW = {...};
        html_template = re.sub(
            r'const EV_RAW = \{.*?\};',
            f'const EV_RAW = {ev_json};',
            html_template, flags=re.DOTALL, count=1
        )
        # Replace TR_RAW = {...};
        html_template = re.sub(
            r'const TR_RAW = \{.*?\};',
            f'const TR_RAW = {tr_json};',
            html_template, flags=re.DOTALL, count=1
        )

        # Patch SEGMENTS and SEG_FILTER in JS to match our actual company names
        js_patch = """
const SEGMENTS = {
  'Maruti':'PV','Hyundai':'PV','Tata Motors PV':'PV','Mahindra':'PV','Force Motors':'PV','SML Mahindra':'PV',
  'Tata Motors CV':'CV','Ashok Leyland':'CV','Eicher CV':'CV',
  'Bajaj':'2W','Hero':'2W','Eicher 2W':'2W','OLA':'2W','TVS':'2W',
  'Atul Auto':'3W','TVS 3W':'3W',
};
const SEG_FILTER = {
  'all': null,
  '2W': ['Bajaj','Hero','Eicher 2W','OLA','TVS'],
  '3W': ['Atul Auto','TVS 3W'],
  'PV': ['Maruti','Hyundai','Tata Motors PV','Mahindra','Force Motors','SML Mahindra'],
  'CV': ['Tata Motors CV','Ashok Leyland','Eicher CV'],
  'EV': ['Tata EV','Mahindra 3W EV','OLA Electric','Atul EV','TVS EV'],
  'TR': ['M\u0026M Tractor'],
};
"""
        # Replace the SEGMENTS and SEG_FILTER blocks in the HTML
        import re as _re
        html_template = _re.sub(
            r'const SEGMENTS = \{.*?\};',
            js_patch.split("const SEG_FILTER")[0].strip(),
            html_template, flags=_re.DOTALL, count=1
        )
        html_template = _re.sub(
            r'const SEG_FILTER = \{.*?\};',
            "const SEG_FILTER = " + js_patch.split("const SEG_FILTER = ")[1].strip(),
            html_template, flags=_re.DOTALL, count=1
        )

        # Compute dynamic labels from actual data
        from datetime import datetime
        from dateutil.relativedelta import relativedelta

        all_dates = []
        for s in RAW.values():
            if s["dates"]:
                all_dates.extend(s["dates"])

        if all_dates:
            latest_month  = sorted(all_dates)[-1]   # "YYYY-MM"
            latest_dt     = datetime.strptime(latest_month, "%Y-%m")
            prev_month_dt = latest_dt - relativedelta(months=1)
            yoy_month_dt  = latest_dt - relativedelta(years=1)
            ttm_start_dt  = latest_dt - relativedelta(months=11)

            latest_label   = latest_dt.strftime("%b %Y")       # e.g. Apr 2026
            prev_label     = prev_month_dt.strftime("%b %Y")   # e.g. Mar 2026
            yoy_label      = yoy_month_dt.strftime("%b %Y")    # e.g. Apr 2025
            ttm_start_label= ttm_start_dt.strftime("%b %Y")    # e.g. May 2025
        else:
            latest_label    = datetime.now().strftime("%b %Y")
            prev_label      = latest_label
            yoy_label       = latest_label
            ttm_start_label = latest_label

        # Enable legend on the market share doughnut chart
        html_template = html_template.replace(
            "type:'doughnut',data:{labels:cos,datasets:[{data:vals,backgroundColor:cos.map(c=>getColor(c)),borderColor:'#fff',borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,cutout:'60%',plugins:{legend:{display:false}",
            "type:'doughnut',data:{labels:cos,datasets:[{data:vals,backgroundColor:cos.map(c=>getColor(c)),borderColor:'#fff',borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,cutout:'60%',plugins:{legend:{display:true,position:'bottom',labels:{color:'#4a5568',font:{size:10},boxWidth:10,padding:8}}"
        )

        # Add TVS EV to EV_COS and EV_COLORS (hardcoded in HTML)
        html_template = html_template.replace(
            "const EV_COS = ['Tata EV','Mahindra 3W EV','OLA Electric','Atul EV'];",
            "const EV_COS = ['Tata EV','Mahindra 3W EV','OLA Electric','Atul EV','TVS EV'];"
        )
        html_template = html_template.replace(
            "const EV_COLORS = {'Tata EV':'#0d9e6a','Mahindra 3W EV':'#1d6af5','OLA Electric':'#e05c2a','Atul EV':'#7c3aed'};",
            "const EV_COLORS = {'Tata EV':'#0d9e6a','Mahindra 3W EV':'#1d6af5','OLA Electric':'#e05c2a','Atul EV':'#7c3aed','TVS EV':'#0891b2'};"
        )

        # Fix hardcoded segment counts to match our SEG_FILTER
        # PV: Maruti, Hyundai, Tata Motors PV, Mahindra, Force Motors, SML Mahindra = 6
        # CV: Tata Motors CV, Ashok Leyland, Eicher CV = 3
        html_template = html_template.replace(
            '>3 Wheeler<span class="seg-cnt">1</span>',
            '>3 Wheeler<span class="seg-cnt">2</span>'
        )
        html_template = html_template.replace(
            '>Passenger Vehicle<span class="seg-cnt">3</span>',
            '>Passenger Vehicle<span class="seg-cnt">6</span>'
        )
        html_template = html_template.replace(
            '>Commercial Vehicle<span class="seg-cnt">5</span>',
            '>Commercial Vehicle<span class="seg-cnt">3</span>'
        )
        html_template = html_template.replace(
            '>2 Wheeler<span class="seg-cnt">4</span>',
            '>2 Wheeler<span class="seg-cnt">5</span>'
        )
        # Update total company count (All Segments)
        html_template = html_template.replace(
            '>All Segments<span class="seg-cnt">14</span>',
            '>All Segments<span class="seg-cnt">15</span>'
        )

        # ── COMPUTE FY_RAW (April–March financial year totals) ──
        from collections import defaultdict
        fy_raw = {}
        for co, series in RAW.items():
            fy_totals = defaultdict(int)
            fy_counts = defaultdict(int)
            for ym, val in zip(series["dates"], series["values"]):
                year, month = int(ym[:4]), int(ym[5:7])
                fy = year if month >= 4 else year - 1
                fy_totals[fy] += val
                fy_counts[fy] += 1
            fy_raw[co] = {
                "years":  [f"FY{str(fy)[2:]}-{str(fy+1)[2:]}" for fy, cnt in sorted(fy_totals.items()) if cnt >= 9],
                "values": [fy_totals[fy] for fy, cnt in sorted(fy_totals.items()) if cnt >= 9],
            }

        # ── COMPUTE SHARE_HISTORY (monthly market share % per company) ──
        all_months_set = set()
        for s in RAW.values():
            all_months_set.update(s["dates"])
        all_months_sorted = sorted(all_months_set)
        co_month_val = {co: dict(zip(s["dates"], s["values"])) for co, s in RAW.items()}
        share_history = {co: {"dates": [], "values": []} for co in RAW}
        for ym in all_months_sorted:
            month_total = sum(co_month_val[co].get(ym, 0) for co in RAW)
            if month_total == 0:
                continue
            for co in RAW:
                val = co_month_val[co].get(ym, 0)
                if val > 0:
                    share_history[co]["dates"].append(ym)
                    share_history[co]["values"].append(round(val * 100 / month_total, 2))

        # ── COMPUTE CY_TOTALS (current FY April to latest month) ──
        latest_ym_set = sorted(all_months_set)[-1]
        lyr, lmo = int(latest_ym_set[:4]), int(latest_ym_set[5:7])
        fy_start_year = lyr if lmo >= 4 else lyr - 1
        fy_start = f"{fy_start_year}-04"
        cy_totals = {}
        for co, series in RAW.items():
            cy_totals[co] = sum(v for d, v in zip(series["dates"], series["values"]) if d >= fy_start)
        fy_label = f"FY{str(fy_start_year)[2:]}-{str(fy_start_year+1)[2:]}"
        html_template = html_template.replace('<th>FY Total</th>', f'<th>{fy_label}</th>')

        # ── INJECT DATA OBJECTS ──
        fy_json = json.dumps(fy_raw, ensure_ascii=False)
        sh_json = json.dumps(share_history, ensure_ascii=False)
        cy_json = json.dumps(cy_totals, ensure_ascii=False)

        # Inject FY_RAW — after fy_json is computed, inject before EV_RAW
        fy_inject = f"const FY_RAW = {fy_json};\nconst SHARE_HISTORY = {sh_json};\nconst CY_TOTALS = {cy_json};\nconst CY_LABEL = '{fy_label}';"
        html_template = html_template.replace(
            "// EV data\nconst EV_RAW",
            fy_inject + "\n// EV data\nconst EV_RAW"
        )


        # ── PATCH buildShare to support historical mode ──
        history_patch = (
            "function buildShare(cos){\n"
            "  if(shareMode==='history'){\n"
            "    const allD=[...new Set(cos.flatMap(c=>(SHARE_HISTORY[c]||{dates:[]}).dates))].sort();\n"
            "    const sl=selPeriod>=9999?allD:allD.slice(-selPeriod);\n"
            "    const ds=cos.map(c=>({label:c,data:sl.map(d=>{const sh=SHARE_HISTORY[c]||{dates:[],values:[]};const i=sh.dates.indexOf(d);return i>=0?sh.values[i]:null;}),borderColor:getColor(c),backgroundColor:getColor(c)+'22',borderWidth:1.5,fill:false,tension:.3,pointRadius:0}));\n"
            "    return {type:'line',data:{labels:sl,datasets:ds}};\n"
            "  }"
        )
        html_template = html_template.replace("function buildShare(cos){", history_patch)

        # ── PATCH table row to add CY YTD ──
        html_template = html_template.replace(
            "const ttm=sum(vals.slice(-12));",
            "const ttm=sum(vals.slice(-12));const cytd=CY_TOTALS[c]||0;"
        )
        html_template = html_template.replace(
            "`<td>${fmt(ttm)}</td>",
            "`<td>${fmt(cytd)}</td><td>${fmt(ttm)}</td>"
        )

        # Replace hardcoded month labels throughout the HTML
        # Latest month (was "Feb 2026")
        html_template = html_template.replace("Feb 2026", latest_label)
        html_template = html_template.replace("february 2026", latest_label.lower())
        html_template = html_template.replace("February 2026", latest_label)

        # Previous month column header (was "Jan 2026")
        html_template = html_template.replace("Jan 2026", prev_label)

        # YoY comparison label (was "Feb 2025")
        html_template = html_template.replace("Feb 2025", yoy_label)

        # TTM range label (was "Mar 2025–Feb 2026")
        html_template = html_template.replace(
            "Mar 2025–Feb 2026",
            f"{ttm_start_label}–{latest_label}"
        )
        html_template = html_template.replace(
            "Mar 2025–Feb 2026",
            f"{ttm_start_label}–{latest_label}"
        )

        # Patch the topMeta JS line
        html_template = html_template.replace(
            "document.getElementById('topMeta').textContent=`${segLabel} · ${selPeriod>=9999?'All Time':selPeriod+' months'} · ${count} companies · Feb 2026`",
            f"document.getElementById('topMeta').textContent=`${{segLabel}} · ${{selPeriod>=9999?'All Time':selPeriod+' months'}} · ${{count}} companies · {latest_label}`"
        )

        # Patch the YoY chart subtitle dynamically via JS injection
        html_template = html_template.replace(
            '<div class="card-sub">Feb 2026 vs Feb 2025</div>',
            f'<div class="card-sub">{latest_label} vs {yoy_label}</div>'
        )
        html_template = html_template.replace(
            f'<div class="card-sub">{latest_label} vs Feb 2025</div>',
            f'<div class="card-sub">{latest_label} vs {yoy_label}</div>'
        )
        html_template = html_template.replace(
            '<div class="card-sub">12-month cumulative Mar 2025–Feb 2026</div>',
            f'<div class="card-sub">12-month cumulative {ttm_start_label}–{latest_label}</div>'
        )

        # Inject CSS to collapse Streamlit's own padding/header when showing the dashboard
        st.markdown("""
<style>
/* Hide the dashboard header and collapse all padding when Auto Dashboard is active */
.dashboard-header { display: none !important; }
.block-container {
    padding-top: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
    padding-bottom: 0 !important;
    max-width: 100% !important;
}
section[data-testid="stVerticalBlock"] > div:first-child { display: none !important; }
</style>
""", unsafe_allow_html=True)

        _components.html(html_template, height=900, scrolling=True)

    except FileNotFoundError:
        st.error(f"Dashboard template not found: {template_path}. Please upload auto_dashboard_preview.html to the app root directory.")


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
            path = os.path.join(folder, img)
            if not os.path.exists(path):
                continue
            with cols[i % 3]:
                try:
                    st.image(path)
                except Exception:
                    pass

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

    df_plot = mtf[["DATE", "NET MTF OUTSTANDING"]].copy()
    df_plot["DATE"] = pd.to_datetime(df_plot["DATE"], format="%d-%b-%Y", errors="coerce")
    df_plot["NET MTF OUTSTANDING"] = pd.to_numeric(
        df_plot["NET MTF OUTSTANDING"].astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce"
    )
    df_plot = df_plot.dropna(subset=["DATE"]).rename(columns={"DATE": "Date", "NET MTF OUTSTANDING": "Net MTF Outstanding"})

    start_mtf, end_mtf, tf_mtf = date_filter_widget(df_plot["Date"].dropna(), "mtf")
    plot_single_line(apply_tf(df_plot, "Date", tf_mtf), "Date", "Net MTF Outstanding",
                     title="Net MTF Outstanding", date_range=(start_mtf, end_mtf))
