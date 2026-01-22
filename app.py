import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

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

       # clean column names
    df.columns = (
    pd.Series(df.columns)
    .astype(str)
    .str.strip()
    .str.replace("\u00a0", " ", regex=True)
)

    # 🔴 REMOVE EMPTY COLUMN NAMES (CRITICAL FIX)
    df = df.loc[:, df.columns != ""]

    # replace empty cell values with NA
    df = df.replace("", pd.NA)

    return df

    # ---- READ ALL REQUIRED SHEETS ----
    df_main = read_worksheet("comparision charts")
    df_rbi = read_worksheet("Rbi net liquidity")
    df_index_oi = read_worksheet("Index oi charts")
    df_index_val = read_worksheet("index (pe/pb/divyld)")

    return df_main, df_rbi, df_index_oi, df_index_val


# ---- CALL ONCE ----
df_main, df_rbi, df_index_oi, df_index_val = load_data()
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
    "FII OI"
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
        "Asset Class Charts Weekly",
        "Metal Charts"
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
    color="#1f77b4",
    key=None
):
    fig = px.line(
        df,
        x=x,
        y=y,
        render_mode="svg"   # 🔴 THIS FIXES THE INVISIBLE LINE
    )

    fig.update_traces(
        line=dict(color=color, width=2.8),
        hovertemplate="Date: %{x|%d-%m-%y}<br>"
                      "Value: %{y}<extra></extra>"
    )

    fig.update_layout(
        height=height,
        hovermode="x unified",
        yaxis_title=y_label,
        title=title,
        title_x=0.5,
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40)
    )

    fig.update_yaxes(
        tickformat=",",
        showexponent="none"
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=key
    )

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
# INDEX (PE / PB / DIV YIELD)
# =================================================
st.write("DEBUG df_index_val rows:", df_index_val.shape)
st.write("DEBUG df_index_val columns:", list(df_index_val.columns))

if view == "Index (PE/PB/DIVYLD)":

    st.subheader("📈 Index Valuation Metrics")

    df = df_index_val.copy()

    # ===============================
    # DATE CONVERSION
    # ===============================
    for c in ["Date_1", "Date_2", "Date_3"]:
        df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=True)

    df = df.dropna(subset=["Date_1", "Date_2", "Date_3"], how="all")

    # ===============================
    # GLOBAL DATE FILTER
    # ===============================
    min_date = min(df["Date_1"].min(), df["Date_2"].min(), df["Date_3"].min()).date()
    max_date = max(df["Date_1"].max(), df["Date_2"].max(), df["Date_3"].max()).date()

    start_date, end_date = st.date_input(
        "📅 Select date range",
        [min_date, max_date]
    )

    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date)

    # ===============================
    # TABS
    # ===============================
    tab1, tab2, tab3 = st.tabs(
        ["NIFTY 50", "NIFTY MIDCAP 100", "NIFTY SMALLCAP 250"]
    )

    # ===============================
    # NIFTY 50
    # ===============================
    with tab1:
        nifty = df[
            (df["Date_1"] >= start_dt) &
            (df["Date_1"] <= end_dt)
        ][["Date_1", "P/E_1", "P/B_1", "Div Yield_1"]].rename(
            columns={
                "Date_1": "Date",
                "P/E_1": "P/E",
                "P/B_1": "P/B",
                "Div Yield_1": "Dividend Yield"
            }
        )

        nifty = nifty.apply(pd.to_numeric, errors="ignore").dropna(subset=["Date"])

        plot_single_line(nifty, "Date", "P/E", title="NIFTY 50 – P/E", key="n50_pe")
        plot_single_line(nifty, "Date", "P/B", title="NIFTY 50 – P/B", key="n50_pb")
        plot_single_line(nifty, "Date", "Dividend Yield", title="NIFTY 50 – Dividend Yield", key="n50_div")

    # ===============================
    # MIDCAP 100
    # ===============================
    with tab2:
        mid = df[
            (df["Date_2"] >= start_dt) &
            (df["Date_2"] <= end_dt)
        ][["Date_2", "P/E_2", "P/B_2", "Div Yield_2"]].rename(
            columns={
                "Date_2": "Date",
                "P/E_2": "P/E",
                "P/B_2": "P/B",
                "Div Yield_2": "Dividend Yield"
            }
        )

        mid = mid.apply(pd.to_numeric, errors="ignore").dropna(subset=["Date"])

        plot_single_line(mid, "Date", "P/E", title="MIDCAP 100 – P/E", key="mid_pe")
        plot_single_line(mid, "Date", "P/B", title="MIDCAP 100 – P/B", key="mid_pb")
        plot_single_line(mid, "Date", "Dividend Yield", title="MIDCAP 100 – Dividend Yield", key="mid_div")

    # ===============================
    # SMALLCAP 250
    # ===============================
    with tab3:
        small = df[
            (df["Date_3"] >= start_dt) &
            (df["Date_3"] <= end_dt)
        ][["Date_3", "P/E_3", "P/B_3", "Div Yield_3"]].rename(
            columns={
                "Date_3": "Date",
                "P/E_3": "P/E",
                "P/B_3": "P/B",
                "Div Yield_3": "Dividend Yield"
            }
        )

        small = small.apply(pd.to_numeric, errors="ignore").dropna(subset=["Date"])

        plot_single_line(small, "Date", "P/E", title="SMALLCAP 250 – P/E", key="sc_pe")
        plot_single_line(small, "Date", "P/B", title="SMALLCAP 250 – P/B", key="sc_pb")
        plot_single_line(small, "Date", "Dividend Yield", title="SMALLCAP 250 – Dividend Yield", key="sc_div")


# =================================================
# ASSET CLASS CHARTS (TABS)
# =================================================
if view == "Asset Class Charts":

    st.subheader("📊 Asset Class Charts")

    base_folder = "asset_class_charts"

    asset_tabs = {
        "DXY": "dxy",
        "USDINR": "usdinr",
        "NIFTYGS10YR": "niftygs10yr",
        "IN10Y": "in10y",
        "GOLD": "gold",
        "SILVER": "silver",
        "UKOIL": "ukoil",
        "SPX": "spx",
    }

    if not os.path.exists(base_folder):
        st.warning("Folder 'asset_class_charts' not found.")
    else:
        tab_labels = list(asset_tabs.keys())
        tabs = st.tabs(tab_labels)

        for tab, (display_name, folder_name) in zip(tabs, asset_tabs.items()):
            with tab:
                folder_path = os.path.join(base_folder, folder_name)

                if not os.path.exists(folder_path):
                    st.info("No charts available.")
                    continue

                images = [
                    f for f in os.listdir(folder_path)
                    if f.lower().endswith((".png", ".jpg", ".jpeg"))
                ]

                if not images:
                    st.info("No charts available.")
                    continue

                # ---- SORT BY DATE & TIME FROM FILENAME ----
                def extract_datetime(filename):
                    try:
                        parts = filename.rsplit("_", 2)
                        dt_str = parts[-2] + "_" + parts[-1].split(".")[0]
                        return datetime.strptime(dt_str, "%Y-%m-%d_%H-%M-%S")
                    except Exception:
                        return datetime.min

                images = sorted(images, key=extract_datetime)

                for img in images:
                    st.image(
                        os.path.join(folder_path, img),
                        use_container_width=True
                    )

# =================================================
# ASSET CLASS CHARTS WEEKLY (TABS)
# =================================================
if view == "Asset Class Charts Weekly":

    st.subheader("📊 Asset Class Charts Weekly")

    base_folder = "asset_class_charts_weekly"

    weekly_tabs = {
        "DXY": "dxy",
        "USDINR": "usdinr",
        "NIFTYGS10YR": "niftygs10yr",
        "GOLD": "gold",
        "SILVER": "silver",
        "UKOIL": "ukoil",
        "IN10Y": "in10y",
        "SPX": "spx",
        "EURINR": "eurinr",
        "AW1!": "aw1",
    }

    if not os.path.exists(base_folder):
        st.warning("Folder 'asset_class_charts_weekly' not found.")
    else:
        tab_labels = list(weekly_tabs.keys())
        tabs = st.tabs(tab_labels)

        for tab, (display_name, folder_name) in zip(tabs, weekly_tabs.items()):
            with tab:
                folder_path = os.path.join(base_folder, folder_name)

                if not os.path.exists(folder_path):
                    st.info("No charts available.")
                    continue

                images = [
                    f for f in os.listdir(folder_path)
                    if f.lower().endswith((".png", ".jpg", ".jpeg"))
                ]

                if not images:
                    st.info("No charts available.")
                    continue

                # ---- SORT BY DATE & TIME FROM FILENAME ----
                def extract_datetime(filename):
                    try:
                        parts = filename.rsplit("_", 2)
                        dt_str = parts[-2] + "_" + parts[-1].split(".")[0]
                        return datetime.strptime(dt_str, "%Y-%m-%d_%H-%M-%S")
                    except Exception:
                        return datetime.min

                images = sorted(images, key=extract_datetime)

                for img in images:
                    st.image(
                        os.path.join(folder_path, img),
                        use_container_width=True
                    )

# =================================================
# METAL CHARTS (TABS)
# =================================================
if view == "Metal Charts":

    st.subheader("🔩 Metal Charts")

    base_folder = "metal_charts"

    metal_tabs = {
        "Hindustan Copper": "hindustan_copper",
        "SAIL": "sail",
        "NMDC": "nmdc",
        "NMDC Steel": "nmdc_steel",
        "NALCO": "nalco",
        "Coal India": "coal_india",
        "Hindustan Zinc": "hindustan_zinc",
        "Vedanta": "vedanta",
    }

    if not os.path.exists(base_folder):
        st.warning("Folder 'metal_charts' not found.")
    else:
        tab_labels = list(metal_tabs.keys())
        tabs = st.tabs(tab_labels)

        for tab, (display_name, folder_name) in zip(tabs, metal_tabs.items()):
            with tab:
                folder_path = os.path.join(base_folder, folder_name)

                if not os.path.exists(folder_path):
                    st.info("No charts available.")
                    continue

                images = [
                    f for f in os.listdir(folder_path)
                    if f.lower().endswith((".png", ".jpg", ".jpeg"))
                ]

                if not images:
                    st.info("No charts available.")
                    continue

                # ---- SORT BY DATE & TIME FROM FILENAME ----
                def extract_datetime(filename):
                    try:
                        parts = filename.rsplit("_", 2)
                        dt_str = parts[-2] + "_" + parts[-1].split(".")[0]
                        return datetime.strptime(dt_str, "%Y-%m-%d_%H-%M-%S")
                    except Exception:
                        return datetime.min

                images = sorted(images, key=extract_datetime)

                for img in images:
                    st.image(
                        os.path.join(folder_path, img),
                        use_container_width=True
                    )



































