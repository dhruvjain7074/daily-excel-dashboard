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
from datetime import datetime

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

st.markdown(
    """
    <style>
    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown(
    """
    <style>
    .asset-chart img {
        width: 100%;
        height: 200px;
        object-fit: contain;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📊 Daily Excel Dashboard")
# =================================================
# STABLE PLOT FUNCTION (INDEX PE / PB / DIV ONLY)
# =================================================
def plot_single_line(df, x, y, height=600, y_label=None, title=None, color=None, key=None):
    fig = px.line(
    df,
    x=x,
    y=y,
    connectgaps=False  # 🔴 IMPORTANT: do NOT connect missing data
)


    if color:
        fig.update_traces(line=dict(color=color, width=2.6))
    else:
        fig.update_traces(line=dict(width=2.6))

    fig.update_traces(
        hovertemplate="Date: %{x|%d-%m-%y}<br>"
                      "Value: %{y}<extra></extra>"
    )

    fig.update_layout(
        hovermode="x unified",
        height=height,
        yaxis_title=y_label,
        title=title,
        title_x=0.5,
        template="plotly_white"
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=key   # 🔴 THIS IS THE FIX
    )

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

        # ---- CLEAN COLUMN NAMES ----
        df.columns = (
            pd.Series(df.columns)
            .astype(str)
            .str.strip()
            .str.replace("\u00a0", " ", regex=True)
        )

        # 🔴 REMOVE EMPTY COLUMN NAMES (CRITICAL FIX)
        df = df.loc[:, df.columns != ""]

        # ---- REPLACE EMPTY CELLS WITH NA ----
        df = df.replace("", pd.NA)

        return df

    # ---- READ ALL REQUIRED SHEETS ----
    df_main = read_worksheet("comparision charts")
    df_rbi = read_worksheet("Rbi net liquidity")
    df_index_oi = read_worksheet("Index oi charts")
    df_index_val = read_worksheet("index (pe/pb/divyld)")
    df_tariff = read_worksheet("Tariff_Timeline")
    df_global_rates = read_worksheet("Global interest rates")
    df_india_macro = read_worksheet("India macroeconomic indicators")
    df_auto_sales = read_worksheet("AUTOMOBILE SALES VOLUME")
    df_mtf_outstanding = read_worksheet("MTF OUTSTANDING")


    return df_main, df_rbi, df_index_oi, df_index_val, df_tariff, df_global_rates, df_auto_sales, df_india_macro, df_mtf_outstanding

# ---- CALL ONCE ----
df_main, df_rbi, df_index_oi, df_index_val, df_tariff, df_global_rates, df_auto_sales,df_india_macro,df_mtf_outstanding = load_data()

# ===============================
# CLEAN df_main (CRITICAL)
# ===============================
numeric_cols_main = [
    "HIGH 1", "LOW 1", "H/L 1", "H RATIO 1", "L RATIO 1",
    "HIGH 2", "LOW 2", "H/L 2", "H RATIO 2", "L RATIO 2",
    "HIGH 3", "LOW 3", "H/L 3", "H RATIO 3", "L RATIO 3"
]

for col in numeric_cols_main:
    if col in df_main.columns:
        df_main[col] = pd.to_numeric(df_main[col], errors="coerce")

# Drop rows where ALL numeric values are NaN
df_main = df_main.dropna(how="all", subset=numeric_cols_main)

# ===============================
# CLEAN df_index_oi
# ===============================
numeric_cols_oi = [
    "Index Futures OI",
    "Nifty Futures oi",
    "Future Index Long",
    "Future Index Short",
    "total client oi",
    "Client OI",
    "FII OI",
]

for col in numeric_cols_oi:
    if col in df_index_oi.columns:
        df_index_oi[col] = pd.to_numeric(df_index_oi[col], errors="coerce")
        
# ===============================
# CLEAN df_rbi
# ===============================
for col in ["NET LIQ INC TODAY", "AMOUNT"]:
    if col in df_rbi.columns:
        df_rbi[col] = pd.to_numeric(df_rbi[col], errors="coerce")

# =================================================
# MAIN DROPDOWN
# =================================================
view = st.selectbox(
    "Select View",
    [
        "52 Week Data",
        "EMA 20 Data",
        "EMA 200 Data",
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
        "NET MTF OUTSTANDING"
    ]
)
# =================================================
# DATASET MAPPING (DATASET 1 / 2 / 3)
# =================================================
mapping = {
    "52 Week Data": {
        "date": "DATE 1",
        "high": "HIGH 1",
        "low": "LOW 1",
        "hl": "H/L 1",
        "hr": "H RATIO 1",
        "lr": "L RATIO 1"
    },
    "EMA 20 Data": {
        "date": "DATE 2",
        "high": "HIGH 2",
        "low": "LOW 2",
        "hl": "H/L 2",
        "hr": "H RATIO 2",
        "lr": "L RATIO 2"
    },
    "EMA 200 Data": {
        "date": "DATE 3",
        "high": "HIGH 3",
        "low": "LOW 3",
        "hl": "H/L 3",
        "hr": "H RATIO 3",
        "lr": "L RATIO 3"
    }
}

# =================================================
# COMMON PLOT FUNCTION (FINAL – BUG-FREE)
# =================================================
def plot_single_line(
    df,
    x,
    y,
    height=600,
    y_label=None,
    title=None,
    color=None,
    key=None,
):
    fig = px.line(df, x=x, y=y)

    fig.update_traces(
        line=dict(width=2.6, color=color) if color else dict(width=2.6),
        hovertemplate="Date: %{x|%d-%m-%y}<br>Value: %{y}<extra></extra>"
    )

    # 🔴 LOCK SIZE — THIS FIXES FLICKER
    fig.update_layout(
        autosize=False,
        height=height,
        width=1200,   # ✅ FIXED WIDTH
        hovermode="x unified",
        yaxis_title=y_label,
        title=title,
        title_x=0.5,
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40)
    )

    fig.update_yaxes(tickformat=",", showexponent="none")

    st.plotly_chart(fig, key=key)


# =================================================
# DATASET 1 / 2 / 3 VIEW
# =================================================
if view in ["52 Week Data", "EMA 20 Data", "EMA 200 Data"]:

    m = mapping[view]

    data = df_main[
        [m["date"], m["high"], m["low"], m["hl"], m["hr"], m["lr"]]
    ].dropna()

    data[m["date"]] = pd.to_datetime(
    data[m["date"]],
    errors="coerce",
    dayfirst=True
)

    data = data.dropna(subset=[m["date"]])

    st.subheader("📅 Date Filter")

    start_date, end_date = st.date_input(
        "Select date range",
        [data[m["date"]].min().date(), data[m["date"]].max().date()]
    )

    filtered = data[
        (data[m["date"]] >= pd.to_datetime(start_date)) &
        (data[m["date"]] <= pd.to_datetime(end_date))
    ]

    # -------- Chart 1: HIGH & LOW COUNT --------
    plot_df1 = filtered[[m["date"], m["high"], m["low"]]].rename(
        columns={m["date"]: "Date", m["high"]: "HIGH", m["low"]: "LOW"}
    )

    fig1 = px.line(
        plot_df1,
        x="Date",
        y=["HIGH", "LOW"],
        color_discrete_map={"HIGH": "green", "LOW": "red"},
        title="HIGH & LOW COUNT"
    )

    fig1.update_layout(
        hovermode="x unified",
        height=600,
        title_x=0.5,
        template="plotly_white"
    )

    st.plotly_chart(fig1, use_container_width=True)

    # -------- Chart 2: HIGH/LOW RATIO --------
    plot_single_line(
        filtered.rename(columns={m["date"]: "Date", m["hl"]: "HIGH/LOW RATIO"}),
        "Date",
        "HIGH/LOW RATIO",
        title="HIGH/LOW RATIO",
        height=600
    )

    # -------- Chart 3: HIGH / EMA 200 --------
    plot_single_line(
        filtered.rename(columns={m["date"]: "Date", m["hr"]: "HIGH / EMA 200"}),
        "Date",
        "HIGH / EMA 200",
        title="HIGH / EMA 200",
        color="green",
        height=600
    )

    # -------- Chart 4: LOW / EMA 200 --------
    plot_single_line(
        filtered.rename(columns={m["date"]: "Date", m["lr"]: "LOW / EMA 200"}),
        "Date",
        "LOW / EMA 200",
        title="LOW / EMA 200",
        color="red",
        height=600
    )

# =================================================
# RBI NET LIQUIDITY INJECTED
# =================================================
if view == "RBI Net Liquidity Injected":

    st.subheader("🏦 RBI Net Liquidity Injected")

    # ===============================
    # CHART 1: NET LIQUIDITY
    # ===============================
    rbi_1 = df_rbi[["DATE-1", "NET LIQ INC TODAY"]].copy()

    rbi_1["DATE-1"] = pd.to_datetime(
        rbi_1["DATE-1"],
        errors="coerce",
        dayfirst=True
    )

    rbi_1["NET LIQ INC TODAY"] = (
        rbi_1["NET LIQ INC TODAY"]
        .astype(str)
        .str.replace(",", "", regex=False)
    )

    rbi_1["NET LIQ INC TODAY"] = pd.to_numeric(
        rbi_1["NET LIQ INC TODAY"],
        errors="coerce"
    )

    rbi_1 = rbi_1.dropna().sort_values("DATE-1")

    plot_single_line(
        rbi_1.rename(
            columns={
                "DATE-1": "Date",
                "NET LIQ INC TODAY": "Net Liquidity"
            }
        ),
        x="Date",
        y="Net Liquidity",
        title="RBI Net Liquidity Injected",
        height=600
    )

    # ===============================
    # CHART 2: AMOUNT
    # ===============================
    rbi_2 = df_rbi[["DATE_2", "AMOUNT"]].copy()

    rbi_2["DATE_2"] = pd.to_datetime(
        rbi_2["DATE_2"],
        errors="coerce",
        dayfirst=True
    )

    rbi_2["AMOUNT"] = (
        rbi_2["AMOUNT"]
        .astype(str)
        .str.replace(",", "", regex=False)
    )

    rbi_2["AMOUNT"] = pd.to_numeric(
        rbi_2["AMOUNT"],
        errors="coerce"
    )

    rbi_2 = rbi_2.dropna().sort_values("DATE_2")

    plot_single_line(
        rbi_2.rename(
            columns={
                "DATE_2": "Date",
                "AMOUNT": "Amount"
            }
        ),
        x="Date",
        y="Amount",
        title="RBI Durable Liquidity (Amount)",
        height=600
    )

# =================================================
# INDEX FUTURES OI
# =================================================
if view == "Index Futures OI":

    st.subheader("📊 Index Futures OI")

    oi = df_index_oi.copy()

    # =================================================
    # DATE CONVERSION (ROBUST)
    # =================================================
    oi["Date_1"] = pd.to_datetime(oi["Date_1"], errors="coerce", dayfirst=True)
    oi["Date_2"] = pd.to_datetime(oi["Date_2"], errors="coerce", dayfirst=True)
    oi["Date_3"] = pd.to_datetime(oi["Date_3"], errors="coerce", dayfirst=True)
    oi["DATE_4"] = pd.to_datetime(oi["DATE_4"], errors="coerce", dayfirst=True)

    # =================================================
    # DATE FILTER
    # =================================================
    min_date = min(
        oi["Date_1"].dropna().min(),
        oi["Date_2"].dropna().min(),
        oi["Date_3"].dropna().min(),
        oi["DATE_4"].dropna().min()
    ).date()

    max_date = max(
        oi["Date_1"].dropna().max(),
        oi["Date_2"].dropna().max(),
        oi["Date_3"].dropna().max(),
        oi["DATE_4"].dropna().max()
    ).date()

    start_date, end_date = st.date_input(
        "Select date range",
        [min_date, max_date]
    )

    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)

    # =================================================
    # CHART 1: INDEX FUTURES OI
    # =================================================
    plot_df_1 = oi.loc[
        (oi["Date_1"] >= start_dt) & (oi["Date_1"] <= end_dt),
        ["Date_1", "Index Futures OI"]
    ].rename(columns={"Date_1": "Date"})

    plot_single_line(
        plot_df_1,
        "Date",
        "Index Futures OI",
        title="Index Futures OI",
        height=600
    )

    # =================================================
    # CHART 2: NIFTY FUTURES OI
    # =================================================
    plot_df_2 = oi.loc[
        (oi["Date_2"] >= start_dt) & (oi["Date_2"] <= end_dt),
        ["Date_2", "Nifty Futures oi"]
    ].rename(columns={"Date_2": "Date"})

    plot_single_line(
        plot_df_2,
        "Date",
        "Nifty Futures oi",
        title="Nifty Futures OI",
        height=600
    )

    # =================================================
    # CHART 3: TOTAL CLIENT OI
    # =================================================
    plot_df_3 = oi.loc[
        (oi["Date_3"] >= start_dt) & (oi["Date_3"] <= end_dt),
        ["Date_3", "total client oi"]
    ].rename(columns={"Date_3": "Date"})

    plot_df_3["total client oi"] = (
        plot_df_3["total client oi"]
        .astype(str)
        .str.replace(",", "", regex=False)
    )

    plot_df_3["total client oi"] = pd.to_numeric(
        plot_df_3["total client oi"], errors="coerce"
    )

    plot_df_3 = plot_df_3.dropna()

    plot_single_line(
        plot_df_3,
        "Date",
        "total client oi",
        title="Total Client OI",
        height=600
    )

    # =================================================
    # CHART 4: CLIENT OI vs FII OI
    # =================================================
    client_fii = oi.loc[
        (oi["DATE_4"] >= start_dt) & (oi["DATE_4"] <= end_dt),
        ["DATE_4", "Client OI", "FII OI"]
    ].rename(columns={"DATE_4": "Date"})

    client_fii["Client OI"] = (
        client_fii["Client OI"]
        .astype(str)
        .str.replace(",", "", regex=False)
    )

    client_fii["FII OI"] = (
        client_fii["FII OI"]
        .astype(str)
        .str.replace(",", "", regex=False)
    )

    client_fii["Client OI"] = pd.to_numeric(client_fii["Client OI"], errors="coerce")
    client_fii["FII OI"] = pd.to_numeric(client_fii["FII OI"], errors="coerce")

    client_fii = client_fii.dropna(how="all", subset=["Client OI", "FII OI"])

    fig_cf = px.line(
        client_fii,
        x="Date",
        y=["Client OI", "FII OI"],
        title="Client OI vs FII OI"
    )

    fig_cf.update_layout(
        hovermode="x unified",
        height=600,
        title_x=0.5,
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=0.98,
            xanchor="right",
            x=0.98,
            bgcolor="rgba(255,255,255,0.6)"
        ),
        margin=dict(l=40, r=40, t=60, b=40)
    )

    fig_cf.update_yaxes(
        tickformat=",",
        showexponent="none"
    )

    st.plotly_chart(fig_cf, use_container_width=True)

# =================================================
# INDEX (PE / PB / DIV YLD) — TABS, NO DATE FILTER
# =================================================
if view == "Index (PE / PB / DIV YLD)":

    st.subheader("📈 Index Valuation Metrics")

    df = df_index_val.copy()

    # ---- remove empty columns ----
    df = df.loc[:, df.columns != ""]

    # ---- convert dates ----
    for c in ["Date_1", "Date_2", "Date_3"]:
        df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=True)

    # ---- convert numeric values ----
    for c in [
        "P/E_1", "P/B_1", "Div Yield_1",
        "P/E_2", "P/B_2", "Div Yield_2",
        "P/E_3", "P/B_3", "Div Yield_3"
    ]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # =================================================
    # TABS
    # =================================================
    tab1, tab2, tab3 = st.tabs([
        "NIFTY 50",
        "NIFTY MIDCAP 100",
        "NIFTY SMALLCAP 250"
    ])

    # ===============================
    # TAB 1 — NIFTY 50
    # ===============================
    with tab1:
        data = df[["Date_1", "P/E_1", "P/B_1", "Div Yield_1"]].dropna()
        data = data.rename(columns={
            "Date_1": "Date",
            "P/E_1": "P/E",
            "P/B_1": "P/B",
            "Div Yield_1": "Dividend Yield"
        })

        plot_single_line(data, "Date", "P/E", title="NIFTY 50 – P/E", key="n50_pe")
        plot_single_line(data, "Date", "P/B", title="NIFTY 50 – P/B", key="n50_pb")
        plot_single_line(data, "Date", "Dividend Yield", title="NIFTY 50 – Dividend Yield", key="n50_div")

    # ===============================
    # TAB 2 — MIDCAP 100
    # ===============================
    with tab2:
        data = df[["Date_2", "P/E_2", "P/B_2", "Div Yield_2"]].dropna()
        data = data.rename(columns={
            "Date_2": "Date",
            "P/E_2": "P/E",
            "P/B_2": "P/B",
            "Div Yield_2": "Dividend Yield"
        })

        plot_single_line(data, "Date", "P/E", title="MIDCAP 100 – P/E", key="mid_pe")
        plot_single_line(data, "Date", "P/B", title="MIDCAP 100 – P/B", key="mid_pb")
        plot_single_line(data, "Date", "Dividend Yield", title="MIDCAP 100 – Dividend Yield", key="mid_div")

    # ===============================
    # TAB 3 — SMALLCAP 250
    # ===============================
    with tab3:
        data = df[["Date_3", "P/E_3", "P/B_3", "Div Yield_3"]].dropna()
        data = data.rename(columns={
            "Date_3": "Date",
            "P/E_3": "P/E",
            "P/B_3": "P/B",
            "Div Yield_3": "Dividend Yield"
        })

        plot_single_line(data, "Date", "P/E", title="SMALLCAP 250 – P/E", key="sc_pe")
        plot_single_line(data, "Date", "P/B", title="SMALLCAP 250 – P/B", key="sc_pb")
        plot_single_line(data, "Date", "Dividend Yield", title="SMALLCAP 250 – Dividend Yield", key="sc_div")


# =================================================
# ASSET CLASS CHARTS (DAILY / WEEKLY / MONTHLY)
# =================================================
if view == "Asset Class Charts":

    st.subheader("📷 Asset Class Charts")

    freq = st.radio(
        "Select Frequency",
        ["Daily", "Weekly", "Monthly"],
        horizontal=True
    )

    base_folder_map = {
        "Daily": "asset_class_charts/daily",
        "Weekly": "asset_class_charts/weekly",
        "Monthly": "asset_class_charts/monthly"
    }

    base_folder = base_folder_map[freq]

    assets = [
        "DXY",
        "USDINR",
        "NIFTYGS10YR",
        "IN10Y",
        "GOLD",
        "SILVER",
        "UKOIL",
        "SPX",
        "EURINR",
        "AW1",
        "EEM"
    ]

    tabs = st.tabs(assets)

    for tab, asset in zip(tabs, assets):
        with tab:
            folder = os.path.join(base_folder, asset)

            images = get_sorted_images(folder)

            if not images:
                st.info("No charts available.")
            else:
                for img in images:
                    st.image(
                        os.path.join(folder, img),
                        use_container_width=True
                    )


# =================================================
# METAL CHARTS (DAILY / WEEKLY / MONTHLY)
# =================================================
if view == "Metal Charts":

    st.subheader("⛏️ Metal Charts")

    freq = st.radio(
        "Select Frequency",
        ["Daily", "Weekly", "Monthly"],
        horizontal=True,
        key="metal_freq"
    )

    base_folder_map = {
        "Daily": "metal_charts/daily",
        "Weekly": "metal_charts/weekly",
        "Monthly": "metal_charts/monthly"
    }

    base_folder = base_folder_map[freq]

    metals = [
        "Hindustan Copper",
        "SAIL",
        "NMDC",
        "NMDC Steel",
        "NALCO",
        "Coal India",
        "Hindustan Zinc",
        "Vedanta",
        "DXY",
        "stock-dxy"
    ]

    tabs = st.tabs(metals)

    for tab, metal in zip(tabs, metals):
        with tab:
            folder = os.path.join(base_folder, metal)

            images = get_sorted_images(folder)

            if not images:
                st.info("No charts available.")
            else:
                for img in images:
                    st.image(
                        os.path.join(folder, img),
                        use_container_width=True
                    )

# =================================================
# TARIFF TIMELINE
# =================================================
if view == "Tariff Timeline":

    st.subheader("📜 Tariff Timeline")

    st.dataframe(df_tariff, use_container_width=True)

# =================================================
# GLOBAL INTEREST RATES
# =================================================
if view == "Global Interest Rates":

    st.subheader("🌍 Global Interest Rates")

    rates = df_global_rates.copy()

    # ---- Convert date columns safely ----
    date_cols = ["Date_1", "Date_2", "Date_3", "Date_4", "Date_5"]
    int_cols  = ["Int_1", "Int_2", "Int_3", "Int_4", "Int_5"]

    for c in date_cols:
        if c in rates.columns:
            rates[c] = pd.to_datetime(rates[c], errors="coerce", dayfirst=True)

    for c in int_cols:
        if c in rates.columns:
            rates[c] = pd.to_numeric(rates[c], errors="coerce")

    tabs = st.tabs(["US", "India", "UK", "China", "Japan"])

    # ---------------- US ----------------
    with tabs[0]:
        df_us = rates[["Date_1", "Int_1"]].dropna()
        df_us = df_us.rename(columns={"Date_1": "Date", "Int_1": "Interest Rate"})
        plot_single_line(df_us, "Date", "Interest Rate", title="US Interest Rates")

    # ---------------- INDIA ----------------
    with tabs[1]:
        df_in = rates[["Date_2", "Int_2"]].dropna()
        df_in = df_in.rename(columns={"Date_2": "Date", "Int_2": "Interest Rate"})
        plot_single_line(df_in, "Date", "Interest Rate", title="India Interest Rates")

    # ---------------- UK ----------------
    with tabs[2]:
        df_uk = rates[["Date_3", "Int_3"]].dropna()
        df_uk = df_uk.rename(columns={"Date_3": "Date", "Int_3": "Interest Rate"})
        plot_single_line(df_uk, "Date", "Interest Rate", title="UK Interest Rates")

    # ---------------- CHINA ----------------
    with tabs[3]:
        df_cn = rates[["Date_4", "Int_4"]].dropna()
        df_cn = df_cn.rename(columns={"Date_4": "Date", "Int_4": "Interest Rate"})
        plot_single_line(df_cn, "Date", "Interest Rate", title="China Interest Rates")

    # ---------------- JAPAN ----------------
    with tabs[4]:
        df_jp = rates[["Date_5", "Int_5"]].dropna()
        df_jp = df_jp.rename(columns={"Date_5": "Date", "Int_5": "Interest Rate"})
        plot_single_line(df_jp, "Date", "Interest Rate", title="Japan Interest Rates")

# =================================================
# INDIA MACROECONOMIC INDICATORS (FINAL FIXED)
# =================================================
if view == "India Macroeconomic Indicators":

    st.subheader("🇮🇳 India Macroeconomic Indicators")

    macro = df_india_macro.copy()

    # remove empty columns
    macro = macro.loc[:, macro.columns != ""]

    # ===============================
    # GDP
    # ===============================
    gdp = macro[["Date_1", "GDP %"]].copy()

    gdp["Date_1"] = pd.to_datetime(gdp["Date_1"], errors="coerce", dayfirst=True)

    gdp["GDP %"] = (
        gdp["GDP %"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    gdp["GDP %"] = pd.to_numeric(gdp["GDP %"], errors="coerce")

    gdp = gdp.dropna(subset=["Date_1"])

    plot_single_line(
        gdp.rename(columns={"Date_1": "Date", "GDP %": "Value"}),
        "Date",
        "Value",
        title="GDP %",
        height=600
    )

    # ===============================
    # INFLATION
    # ===============================
    inflation = macro[["Date_2", "INFLATION %"]].copy()

    inflation["Date_2"] = pd.to_datetime(inflation["Date_2"], errors="coerce", dayfirst=True)

    inflation["INFLATION %"] = (
        inflation["INFLATION %"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    inflation["INFLATION %"] = pd.to_numeric(inflation["INFLATION %"], errors="coerce")

    inflation = inflation.dropna(subset=["Date_2"])

    plot_single_line(
        inflation.rename(columns={"Date_2": "Date", "INFLATION %": "Value"}),
        "Date",
        "Value",
        title="Inflation %",
        height=600
    )

    # ===============================
    # LOAN GROWTH
    # ===============================
    credit = macro[["Date_3", "LOAN Growth %"]].copy()

    credit["Date_3"] = pd.to_datetime(credit["Date_3"], errors="coerce", dayfirst=True)

    credit["LOAN Growth %"] = (
        credit["LOAN Growth %"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    credit["LOAN Growth %"] = pd.to_numeric(credit["LOAN Growth %"], errors="coerce")

    credit = credit.dropna(subset=["Date_3"])

    plot_single_line(
        credit.rename(columns={"Date_3": "Date", "LOAN Growth %": "Value"}),
        "Date",
        "Value",
        title="Loan Growth %",
        height=600
    )
# =================================================
# AUTOMOBILE SALES VOLUMES
# =================================================
if view == "Automobile Sales Volumes":

    st.subheader("🚗 Automobile Sales Volumes")

    auto = df_auto_sales.copy()  # this comes from load_data()

    # -----------------------------
    # Helper: clean & plot safely
    # -----------------------------
    def plot_auto_chart(df, date_col, value_col, title):
        if date_col not in df.columns or value_col not in df.columns:
            st.warning(f"Missing column: {value_col}")
            return

        plot_df = df[[date_col, value_col]].copy()

        plot_df[date_col] = pd.to_datetime(
            plot_df[date_col],
            errors="coerce",
            dayfirst=True
        )

        plot_df[value_col] = pd.to_numeric(
            plot_df[value_col],
            errors="coerce"
        )

        plot_df = plot_df.dropna()

        if plot_df.empty:
            st.info(f"No data for {title}")
            return

        plot_df = plot_df.rename(columns={
            date_col: "Date",
            value_col: "Value"
        })

        plot_single_line(
    plot_df,
    x="Date",
    y="Value",
    title=title,
    height=600,
    )


    # -----------------------------
    # TABS (OEM-wise)
    # -----------------------------
    tabs = st.tabs([
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

    # =============================
    # TMPV
    # =============================
    with tabs[0]:
        plot_auto_chart(auto, "DATE_1", "TMPV TOTAL", "TMPV – Total Sales")
        plot_auto_chart(auto, "DATE_1", "TMPV DOMESTIC SALES", "TMPV – Domestic Sales")
        plot_auto_chart(auto, "DATE_1", "TMPV INTL SALES", "TMPV – Export Sales")
        plot_auto_chart(auto, "DATE_1", "TMPV EV SALES", "TMPV – EV Sales")
        plot_auto_chart(auto, "DATE_1", "TMPV ICE SALES", "TMPV – ICE Sales")

    # =============================
    # TMCV
    # =============================
    with tabs[1]:
        plot_auto_chart(auto, "DATE_2", "TMCV TOTAL SALES", "TMCV – Total Sales")
        plot_auto_chart(auto, "DATE_2", "TMCV HCV TRUCKS", "TMCV – HCV Trucks")
        plot_auto_chart(auto, "DATE_2", "TMCV SCV CARGO & PICKUP", "TMCV – SCV Cargo & Pickup")
        plot_auto_chart(auto, "DATE_2", "TMCV ILMCV TRUCKS", "TMCV – LMCV")
        plot_auto_chart(auto, "DATE_2", "TMCV PASSENGER CARRIERS", "TMCV – PASSANGER CARRIERS")
        plot_auto_chart(auto, "DATE_2", "TMCV TOTAL DOMESTIC SALES", "TMCV – TOTAL DOMESTIC SALES")
        plot_auto_chart(auto, "DATE_2", "TMCV INTL BUSINESS", "TMCV – INTL BUSINESS")

    # =============================
    # M&M
    # =============================
    with tabs[2]:
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

    # =============================
    # HYUNDAI
    # =============================
    with tabs[3]:
        plot_auto_chart(auto, "DATE_4", "HYUNDAI TOTAL SALES", "Hyundai – Total Sales")
        plot_auto_chart(auto, "DATE_4", "HYUNDAI DOMESTIC SALES", "Hyundai – Domestic Sales")
        plot_auto_chart(auto, "DATE_4", "HYUNDAI EXPORT SALES", "Hyundai – Export Sales")

    # =============================
    # FORCE MOTORS
    # =============================
    with tabs[4]:
        plot_auto_chart(auto, "DATE_5", "FORCE TOTAL SALES", "Force Motors – Total Sales")
        plot_auto_chart(auto, "DATE_5", "FORCE DOMESTIC SALES", "Force – Domestic Sales")
        plot_auto_chart(auto, "DATE_5", "FORCE EXPORTSALES", "Force – Export Sales")

    # =============================
    # SML MAHINDRA
    # =============================
    with tabs[5]:
        plot_auto_chart(auto, "DATE_6", "SML MAHINDRA TOTAL SALES", "SML Mahindra – Total Sales")
        plot_auto_chart(auto, "DATE_6", "SML MAHINDRA CV", "SML Mahindra – CV")
        plot_auto_chart(auto, "DATE_6", "SML MAHINDRA PV", "SML Mahindra – PV")

    # =============================
    # MARUTI
    # =============================
    with tabs[6]:
        plot_auto_chart(auto, "DATE_7", "MARUTI PV", "Maruti – PV")
        plot_auto_chart(auto, "DATE_7", "MARUTI LCV", "Maruti – LCV")
        plot_auto_chart(auto, "DATE_7", "MARUTI OEM", "Maruti – OEM")
        plot_auto_chart(auto, "DATE_7", "MARUTI EXPORT", "Maruti – Export")
        plot_auto_chart(auto, "DATE_7", "MARUTI TOTAL SALES", "Maruti – TOTAL SALES")

    # =============================
    # Atul Auto
    # =============================
    with tabs[7]:
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

    # =============================
    # Atul Auto
    # =============================
    with tabs[8]:
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
    # =============================
    # Atul Auto
    # =============================
    with tabs[9]:
        plot_auto_chart(auto, "DATE_10", "Bajaj 2W Domestic", "Bajaj 2W Domestic")
        plot_auto_chart(auto, "DATE_10", "Bajaj 2W Export", "Bajaj 2W Export")
        plot_auto_chart(auto, "DATE_10", "Bajaj Total 2W D+E", "Bajaj Total 2W D+E")
        plot_auto_chart(auto, "DATE_10", "Bajaj CV Domestic", "Bajaj CV Domestic")
        plot_auto_chart(auto, "DATE_10", "Bajaj CV Export", "Bajaj CV Export")
        plot_auto_chart(auto, "DATE_10", "Bajaj Total CV D+E", "Bajaj Total CV D+E")
        plot_auto_chart(auto, "DATE_10", "Bajaj Total Domestic Sales", "Bajaj Total Domestic Sales")
        plot_auto_chart(auto, "DATE_10", "Bajaj Total Export Sales", "Bajaj Total Export Sales")
        plot_auto_chart(auto, "DATE_10", "Bajaj Total Sales D+E", "Bajaj Total Sales D+E")
    # =============================
    # Hero Motocorp
    # =============================
    with tabs[10]:
        plot_auto_chart(auto, "DATE_11", "Hero Motorcycles Total", "Hero Motorcycles Total")
        plot_auto_chart(auto, "DATE_11", "Hero Scooters Total", "Hero Scooters Total")
        plot_auto_chart(auto, "DATE_11", "Hero Total Sales D+E", "Hero Total Sales D+E")
        plot_auto_chart(auto, "DATE_11", "Hero Domestic Sales", "Hero Domestic Sales")
        plot_auto_chart(auto, "DATE_11", "Hero Export Sales", "Hero Export Sales")
    # =============================
    # OLA Electric
    # =============================
    with tabs[11]:
        plot_auto_chart(auto, "DATE_12", "OLA Total Sales", "OLA Total Sales")
    # =============================
    # Eicher Motors PV
    # =============================
    with tabs[12]:
        plot_auto_chart(auto, "DATE_13", "Eicher Less than 350 cc", "Eicher Less than 350 cc")
        plot_auto_chart(auto, "DATE_13", "Eicher greater than 350 cc", "Eicher greater than 350 cc")
        plot_auto_chart(auto, "DATE_13", "Eicher Total Sales", "Eicher Total Sales")
        plot_auto_chart(auto, "DATE_13", "Eicher Total Export", "Eicher Total Export")
    # =============================
    # Eicher Motors CV
    # =============================
    with tabs[13]:
        plot_auto_chart(auto, "DATE_14", "Eicher CV Domestic sales", "Eicher CV Domestic sales")
        plot_auto_chart(auto, "DATE_14", "Eicher CV Export Sales", "Eicher CV Export Sales")
        plot_auto_chart(auto, "DATE_14", "Eicher CV Volvo Sales", "Eicher CV Volvo Sales")
        plot_auto_chart(auto, "DATE_14", "Eicher CV Total Sales D+E", "Eicher CV Total Sales D+E")

    # =================================================
# MAGAZINE COVER (INDIA / OTHERS)
# =================================================
if view == "Magazine Cover":

    st.subheader("📰 Magazine Cover")

    tab1, tab2 = st.tabs(["India", "Others"])

    # =============================
    # INDIA TAB
    # =============================
    with tab1:
        folder = "magazine_cover/india"

        images = get_sorted_images(folder)

        if not images:
            st.info("No India covers available.")
        else:
            cols = st.columns(3)

            for i, img in enumerate(images):
                with cols[i % 3]:
                    st.image(
                    os.path.join(folder, img),
                    use_container_width=True
                    )

    # =============================
    # OTHERS TAB
    # =============================
    with tab2:
        folder = "magazine_cover/others"

        images = get_sorted_images(folder)

        if not images:
            st.info("No Other covers available.")
        else:
            cols = st.columns(3)

            for i, img in enumerate(images):
                with cols[i % 3]:
                    st.image(
                    os.path.join(folder, img),
                    use_container_width=True
                    )
# =================================================
# MULTIASSET CHART (ONE VIEW)
# =================================================
if view == "Multiasset Chart (One View)":

    st.subheader("📊 Multiasset Chart (One View)")

    tab1, tab2, tab3 = st.tabs([
        "MAIN",
        "BROAD INDICES",
        "SECTORAL INDICES"
    ])

    # =============================
    # FUNCTION: 3 IMAGES PER ROW
    # =============================
    def show_images_grid(folder):
        images = get_sorted_images(folder)

        if not images:
            st.info("No images available.")
            return

        cols = st.columns(3)

        for i, img in enumerate(images):
            with cols[i % 3]:
                st.image(
                    os.path.join(folder, img),
                    use_container_width=True
                )

    # =============================
    # TAB 1: MAIN
    # =============================
    with tab1:
        folder = "multiasset_charts/main"
        show_images_grid(folder)

    # =============================
    # TAB 2: BROAD INDICES
    # =============================
    with tab2:
        folder = "multiasset_charts/broad_indices"
        show_images_grid(folder)

    # =============================
    # TAB 3: SECTORAL INDICES
    # =============================
    with tab3:
        folder = "multiasset_charts/sectoral_indices"
        show_images_grid(folder)
plot_single_line(
        credit.rename(columns={"Date_3": "Date", "LOAN Growth %": "Value"}),
        "Date",
        "Value",
        title="Loan Growth %",
        height=600
    )
# =================================================
# NET MTF OUTSTANDING
# =================================================
if view == "MTF OUTSTANDING":

    st.subheader("📊 Net MTF Outstanding")

    mtf = df_mtf.copy()

    # 🔴 remove empty columns
    mtf = mtf.loc[:, mtf.columns != ""]

    # ===============================
    # 🔥 CHECK YOUR COLUMN NAMES
    # ===============================
    # Replace these if needed
    DATE_COL = mtf.columns[0]
    VALUE_COL = mtf.columns[1]

    df_plot = mtf[[DATE_COL, VALUE_COL]].copy()

    # ---- CLEAN DATE ----
    df_plot[DATE_COL] = pd.to_datetime(
        df_plot[DATE_COL],
        errors="coerce",
        dayfirst=True
    )

    # ---- CLEAN VALUE ----
    df_plot[VALUE_COL] = (
        df_plot[VALUE_COL]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
    )

    df_plot[VALUE_COL] = pd.to_numeric(
        df_plot[VALUE_COL],
        errors="coerce"
    )

    # 🔴 drop only invalid dates
    df_plot = df_plot.dropna(subset=[DATE_COL])

    # ===============================
    # PLOT
    # ===============================
    plot_single_line(
        df_plot.rename(columns={
            DATE_COL: "Date",
            VALUE_COL: "Net MTF Outstanding"
        }),
        "Date",
        "Net MTF Outstanding",
        title="Net MTF Outstanding",
        height=600
    )
