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

st.title("📊 Daily Excel Dashboard")

# =================================================
# LOAD DATA (MULTI-SHEET)
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

    def read_worksheet(name):
        ws = sheet.worksheet(name)
        values = ws.get_all_values()
        headers = values[0]
        rows = values[1:]
        df = pd.DataFrame(rows, columns=headers)
        df.columns = df.columns.str.strip()
        return df

    df_main = read_worksheet("comparision charts")
    df_rbi = read_worksheet("Rbi net liquidity")
    df_index_oi = read_worksheet("Index oi charts")

    return df_main, df_rbi, df_index_oi

df_main, df_rbi, df_index_oi = load_data()

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
        "Asset Class Charts",
        "Asset Class Charts (Weekly)"
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
# COMMON PLOT FUNCTION
# =================================================
def plot_single_line(df, x, y, height=600, y_label=None, title=None, color=None):
    fig = px.line(df, x=x, y=y)

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
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40)  # 🔴 IMPORTANT
    )

    fig.update_yaxes(
        tickformat=",",
        showexponent="none"
    )

    st.plotly_chart(fig, use_container_width=True)

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
    # CHART 1: RBI NET LIQUIDITY
    # ===============================
    rbi_1 = df_rbi[["DATE-1", "NET LIQ INC TODAY"]].copy()

# --- Correct date parsing (NO dayfirst) ---
rbi_1["DATE-1"] = pd.to_datetime(
    rbi_1["DATE-1"],
    errors="coerce"
)

# --- Numeric cleaning ---
rbi_1["NET LIQ INC TODAY"] = (
    rbi_1["NET LIQ INC TODAY"]
    .astype(str)
    .str.replace(",", "", regex=False)
    .str.replace("₹", "", regex=False)
    .str.replace("+", "", regex=False)
    .str.strip()
)

rbi_1["NET LIQ INC TODAY"] = pd.to_numeric(
    rbi_1["NET LIQ INC TODAY"],
    errors="coerce"
)

# --- Keep valid rows only ---
rbi_1 = rbi_1.dropna(subset=["DATE-1", "NET LIQ INC TODAY"])

# --- Aggregate by date & sort ---
rbi_1 = (
    rbi_1
    .groupby("DATE-1", as_index=False)
    .sum()
    .sort_values("DATE-1")
)

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
    # CHART 2: RBI AMOUNT
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
        .str.replace("₹", "", regex=False)
        .str.replace("+", "", regex=False)
        .str.strip()
    )

    rbi_2["AMOUNT"] = pd.to_numeric(
        rbi_2["AMOUNT"],
        errors="coerce"
    )

    rbi_2 = rbi_2.dropna(subset=["DATE_2", "AMOUNT"])

    rbi_2 = (
        rbi_2
        .groupby("DATE_2", as_index=False)
        .sum()
        .sort_values("DATE_2")
    )

    plot_single_line(
        rbi_2.rename(
            columns={
                "DATE_2": "Date",
                "AMOUNT": "Amount"
            }
        ),
        x="Date",
        y="Amount",
        title="RBI Amount",
        height=600
    )

# =================================================
# INDEX FUTURES OI
# =================================================
if view == "Index Futures OI":

    st.subheader("📊 Index Futures OI")

    oi = df_index_oi.copy()

    # ---- Date conversion ----
    oi["Date_1"] = pd.to_datetime(oi["Date_1"])
    oi["Date_2"] = pd.to_datetime(oi["Date_2"])
    oi["Date_3"] = pd.to_datetime(oi["Date_3"])
    oi["DATE_4"] = pd.to_datetime(oi["DATE_4"])

    # ---- Date Filter ----
    min_date = min(
        oi["Date_1"].min(),
        oi["Date_2"].min(),
        oi["Date_3"].min(),
        oi["DATE_4"].min()
    ).date()

    max_date = max(
        oi["Date_1"].max(),
        oi["Date_2"].max(),
        oi["Date_3"].max(),
        oi["DATE_4"].max()
    ).date()

    start_date, end_date = st.date_input(
        "Select date range",
        [min_date, max_date]
    )

    # =================================================
    # Chart 1: Index Futures OI
    # =================================================
    plot_single_line(
        oi[
            (oi["Date_1"] >= pd.to_datetime(start_date)) &
            (oi["Date_1"] <= pd.to_datetime(end_date))
        ].rename(columns={"Date_1": "Date"}),
        "Date",
        "Index Futures OI",
        title="Index Futures OI"
    )

    # =================================================
    # Chart 2: Nifty Futures OI
    # =================================================
    plot_single_line(
        oi[
            (oi["Date_2"] >= pd.to_datetime(start_date)) &
            (oi["Date_2"] <= pd.to_datetime(end_date))
        ].rename(columns={"Date_2": "Date"}),
        "Date",
        "Nifty Futures oi",
        title="Nifty Futures OI"
    )

    # =================================================
    # Chart 3: Total Client OI
    # =================================================
    client_oi = oi[
        (oi["Date_3"] >= pd.to_datetime(start_date)) &
        (oi["Date_3"] <= pd.to_datetime(end_date))
    ][["Date_3", "total client oi"]].rename(
        columns={"Date_3": "Date"}
    )

    client_oi["total client oi"] = pd.to_numeric(
        client_oi["total client oi"], errors="coerce"
    )

    client_oi = client_oi.dropna(subset=["total client oi"])

    plot_single_line(
        client_oi,
        "Date",
        "total client oi",
        title="Total Client OI"
    )

    # =================================================
    # Chart 4: Client OI vs FII OI
    # =================================================
    client_fii = oi[
        (oi["DATE_4"] >= pd.to_datetime(start_date)) &
        (oi["DATE_4"] <= pd.to_datetime(end_date))
    ][["DATE_4", "Client OI", "FII OI"]].rename(
        columns={"DATE_4": "Date"}
    )

    client_fii["Client OI"] = pd.to_numeric(client_fii["Client OI"], errors="coerce")
    client_fii["FII OI"] = pd.to_numeric(client_fii["FII OI"], errors="coerce")

    client_fii = client_fii.dropna(subset=["Client OI", "FII OI"], how="all")

    fig_cf = px.line(
        client_fii,
        x="Date",
        y=["Client OI", "FII OI"],
        title="Client OI vs FII OI"
    )

    # ---- LEGEND INSIDE THE CHART (FOR REAL) ----
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
# ASSET CLASS CHARTS (ORIGINAL)
# =================================================
if view == "Asset Class Charts":

    st.subheader("📷 Asset Class Charts")

    charts_folder = "asset_class_charts"

    if not os.path.exists(charts_folder):
        st.warning("Folder 'asset_class_charts' not found.")
    else:
        images = [
            f for f in os.listdir(charts_folder)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ]

        if not images:
            st.info("No images found.")
        else:
            # ---- SORT BY DATE & TIME FROM FILENAME ----
            def extract_datetime(filename):
                try:
                    parts = filename.rsplit("_", 2)
                    dt_str = parts[-2] + "_" + parts[-1].split(".")[0]
                    return datetime.strptime(dt_str, "%Y-%m-%d_%H-%M-%S")
                except Exception:
                    return datetime.min

            images = sorted(images, key=extract_datetime)

            # ---- DISPLAY (ORIGINAL BEHAVIOR) ----
            for img in images:
                st.image(
                    os.path.join(charts_folder, img),
                    use_container_width=True
                )
# =================================================
# ASSET CLASS CHARTS (WEEKLY)
# =================================================
if view == "Asset Class Charts (Weekly)":

    st.subheader("📷 Asset Class Charts (Weekly)")

    charts_folder = "asset_class_charts_weekly"

    if not os.path.exists(charts_folder):
        st.warning("Folder 'asset_class_charts_weekly' not found.")
    else:
        images = [
            f for f in os.listdir(charts_folder)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ]

        if not images:
            st.info("No images found.")
        else:
            # ---- SORT BY DATE & TIME FROM FILENAME ----
            def extract_datetime(filename):
                try:
                    parts = filename.rsplit("_", 2)
                    dt_str = parts[-2] + "_" + parts[-1].split(".")[0]
                    return datetime.strptime(dt_str, "%Y-%m-%d_%H-%M-%S")
                except Exception:
                    return datetime.min

            images = sorted(images, key=extract_datetime)

            # ---- DISPLAY (SAME AS ORIGINAL) ----
            for img in images:
                st.image(
                    os.path.join(charts_folder, img),
                    use_container_width=True
                )







































