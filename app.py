import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime


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
    df_main = pd.read_excel("Book1.xlsx", sheet_name="comparision charts")
    df_rbi = pd.read_excel("Book1.xlsx", sheet_name="Rbi net liquidity")

    df_main.columns = df_main.columns.str.strip()
    df_rbi.columns = df_rbi.columns.str.strip()

    return df_main, df_rbi

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()

df_main, df_rbi = load_data()

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
        "Asset Class Charts"
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
def plot_single_line(df, x, y, height=350, y_label=None, title=None, color=None):
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
        template="plotly_white"
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

    data[m["date"]] = pd.to_datetime(data[m["date"]])

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

    rbi = df_rbi.copy()

    rbi["DATE-1"] = pd.to_datetime(rbi["DATE-1"])
    rbi["DATE_2"] = pd.to_datetime(rbi["DATE_2"])

    # keep RAW values (no conversion)
    rbi["NET_LIQ_LAKHS"] = rbi["NET LIQ INC TODAY"]
    rbi["AMOUNT_LAKHS"] = rbi["AMOUNT"]

    # -------- Chart 1: RBI Net Liquidity Injected (RAW) --------
    plot_single_line(
        rbi.rename(
            columns={
                "DATE-1": "Date",
                "NET LIQ INC TODAY": "Net Liquidity"
            }
        ),
        "Date",
        "Net Liquidity",
        title="RBI Net Liquidity Injected (Raw)",
        height=600
    )

    # -------- Chart 2: Amount --------
    plot_single_line(
        rbi.rename(
            columns={
                "DATE_2": "Date",
                "AMOUNT_LAKHS": "Amount"
            }
        ),
        "Date",
        "Amount",
        title="Net Durable Liquidity",
        height=600
    )

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

