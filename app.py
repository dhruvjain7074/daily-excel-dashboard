import streamlit as st
import pandas as pd
import plotly.express as px
import os

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(
    page_title="Market Dashboard",
    layout="wide"
)

# =================================================
# CLEAN PROFESSIONAL CSS
# =================================================
st.markdown(
    """
    <style>

    body {
        background-color: #f4f6f8;
        color: #1f2937;
        font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont;
    }

    .block-container {
        max-width: 1400px;
        padding: 2rem 2.5rem;
        margin: auto;
    }

    h1 {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }

    h2 {
        font-size: 1.4rem;
        margin-top: 2rem;
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 0.5rem;
    }

    /* Dropdown */
    div[data-baseweb="select"] {
        max-width: 360px;
    }

    /* Image grid */
    .image-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 24px;
        margin-top: 1.5rem;
    }

    .image-item {
        background: white;
        border-radius: 8px;
        padding: 10px;
        border: 1px solid #e5e7eb;
    }

    .image-title {
        font-weight: 600;
        margin-bottom: 8px;
        font-size: 0.95rem;
    }

    img {
        border-radius: 6px;
    }

    </style>
    """,
    unsafe_allow_html=True
)

st.title("📊 Market Dashboard")

# =================================================
# LOAD DATA
# =================================================
def load_data():
    df_main = pd.read_excel("Book1.xlsx", sheet_name="comparision charts")
    df_rbi = pd.read_excel("Book1.xlsx", sheet_name="Rbi net liquidity")
    df_main.columns = df_main.columns.str.strip()
    df_rbi.columns = df_rbi.columns.str.strip()
    return df_main, df_rbi

df, df_rbi = load_data()

# =================================================
# VIEW SELECTOR
# =================================================
view = st.selectbox(
    "Select Section",
    [
        "Dataset 1",
        "Dataset 2",
        "Dataset 3",
        "RBI Net Liquidity Injected",
        "Asset Class Charts"
    ]
)

# =================================================
# DATASET CONFIG
# =================================================
mapping = {
    "Dataset 1": {"date": "DATE 1", "high": "HIGH 1", "low": "LOW 1"},
    "Dataset 2": {"date": "DATE 2", "high": "HIGH 2", "low": "LOW 2"},
    "Dataset 3": {"date": "DATE 3", "high": "HIGH 3", "low": "LOW 3"},
}

# =================================================
# DATASET VIEWS
# =================================================
if view in mapping:

    m = mapping[view]
    data = df[[m["date"], m["high"], m["low"]]].dropna()
    data[m["date"]] = pd.to_datetime(data[m["date"]])

    st.subheader("Date Filter")
    start, end = st.date_input(
        "Select range",
        [data[m["date"]].min(), data[m["date"]].max()]
    )

    data = data[
        (data[m["date"]] >= pd.to_datetime(start)) &
        (data[m["date"]] <= pd.to_datetime(end))
    ]

    fig = px.line(
        data,
        x=m["date"],
        y=[m["high"], m["low"]],
        labels={"value": "Value", "variable": ""}
    )

    fig.update_traces(
        hovertemplate=
            "<b>%{fullData.name}</b><br>"
            "Date: %{x|%d-%m-%y}<br>"
            "Value: %{y}<extra></extra>"
    )

    fig.update_layout(
        hovermode="x unified",
        height=520,
        margin=dict(l=30, r=30, t=30, b=30),
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

# =================================================
# RBI NET LIQUIDITY
# =================================================
if view == "RBI Net Liquidity Injected":

    st.subheader("RBI Net Liquidity (₹ Lakhs)")

    rbi = df_rbi.copy()
    rbi["DATE-1"] = pd.to_datetime(rbi["DATE-1"])
    rbi["NET_LAKHS"] = rbi["NET LIQ INC TODAY"] / 100000

    fig = px.line(
        rbi,
        x="DATE-1",
        y="NET_LAKHS"
    )

    fig.update_traces(
        hovertemplate=
            "Date: %{x|%d-%m-%y}<br>"
            "Value (Lakhs): %{y}<extra></extra>"
    )

    fig.update_layout(
        hovermode="x unified",
        height=500,
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)

# =================================================
# ASSET CLASS CHARTS (GRID VIEW)
# =================================================
if view == "Asset Class Charts":

    st.subheader("Asset Class Charts")

    folder = "asset_class_charts"

    if not os.path.exists(folder):
        st.warning("asset_class_charts folder not found.")
    else:
        images = [
            f for f in sorted(os.listdir(folder))
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ]

        if not images:
            st.info("No charts available.")
        else:
            st.markdown('<div class="image-grid">', unsafe_allow_html=True)

            for img in images:
                title = img.replace("_", " ").split(".")[0].title()

                st.markdown(
                    f"""
                    <div class="image-item">
                        <div class="image-title">{title}</div>
                        <img src="{folder}/{img}" style="width:100%;">
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown("</div>", unsafe_allow_html=True)
