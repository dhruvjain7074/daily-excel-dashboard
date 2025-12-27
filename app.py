import streamlit as st
import pandas as pd
import plotly.express as px
import os

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(page_title="Daily Excel Dashboard", layout="wide")

# =================================================
# GLOBAL CSS (UI POLISH)
# =================================================
st.markdown(
    """
    <style>

    html, body, [class*="css"] {
        font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        background-color: #f6f8fa;
    }

    .block-container {
        padding: 2rem 2.5rem;
        max-width: 100%;
    }

    h1 {
        font-size: 2.1rem;
        font-weight: 700;
        margin-bottom: 1.2rem;
    }

    h2, h3 {
        font-weight: 600;
        margin-top: 1.5rem;
    }

    div[data-baseweb="select"] > div {
        background-color: white;
        border-radius: 10px;
        border: 1px solid #e1e4e8;
    }

    input {
        border-radius: 8px !important;
    }

    .chart-card {
        background-color: white;
        border-radius: 14px;
        padding: 1.2rem;
        margin-bottom: 1.6rem;
        box-shadow: 0 6px 18px rgba(0, 0, 0, 0.05);
    }

    img {
        border-radius: 12px;
    }

    hr {
        border: none;
        border-top: 1px solid #e5e7eb;
        margin: 2.5rem 0;
    }

    </style>
    """,
    unsafe_allow_html=True
)

st.title("📊 Daily Excel Dashboard")

# =================================================
# LOAD DATA
# =================================================
def load_data():
    df_main = pd.read_excel("Book1.xlsx", sheet_name="comparision charts")
    df_rbi = pd.read_excel("Book1.xlsx", sheet_name="Rbi net liquidity")

    df_main.columns = df_main.columns.str.strip()
    df_rbi.columns = df_rbi.columns.str.strip()

    return df_main, df_rbi

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()

df, df_rbi = load_data()

# =================================================
# MAIN DROPDOWN
# =================================================
view = st.selectbox(
    "Select View",
    [
        "Dataset 1",
        "Dataset 2",
        "Dataset 3",
        "RBI Net Liquidity Injected",
        "Asset Class Charts"
    ]
)

# =================================================
# DATASET MAPPING
# =================================================
mapping = {
    "Dataset 1": {
        "date": "DATE 1",
        "high": "HIGH 1",
        "low": "LOW 1",
        "hl": "H/L 1",
        "hr": "H RATIO 1",
        "lr": "L RATIO 1"
    },
    "Dataset 2": {
        "date": "DATE 2",
        "high": "HIGH 2",
        "low": "LOW 2",
        "hl": "H/L 2",
        "hr": "H RATIO 2",
        "lr": "L RATIO 2"
    },
    "Dataset 3": {
        "date": "DATE 3",
        "high": "HIGH 3",
        "low": "LOW 3",
        "hl": "H/L 3",
        "hr": "H RATIO 3",
        "lr": "L RATIO 3"
    }
}

# =================================================
# COMMON PLOT HELPER
# =================================================
def plot_single_line(df, x, y, height=350, y_label=None):
    fig = px.line(df, x=x, y=y)
    fig.update_traces(
        line=dict(width=2.6),
        hovertemplate=
            "Date: %{x|%d-%m-%y}<br>"
            "Value: %{y}<extra></extra>"
    )
    fig.update_layout(
        hovermode="x unified",
        height=height,
        yaxis_title=y_label,
        template="plotly_white"
    )
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =================================================
# DATASET 1 / 2 / 3
# =================================================
if view in ["Dataset 1", "Dataset 2", "Dataset 3"]:

    m = mapping[view]

    data = df[
        [m["date"], m["high"], m["low"], m["hl"], m["hr"], m["lr"]]
    ].dropna()

    data[m["date"]] = pd.to_datetime(data[m["date"]])

    st.subheader("📅 Date Filter")

    min_date = data[m["date"]].min().date()
    max_date = data[m["date"]].max().date()

    start_date, end_date = st.date_input(
        "Select date range",
        [min_date, max_date]
    )

    filtered = data[
        (data[m["date"]] >= pd.to_datetime(start_date)) &
        (data[m["date"]] <= pd.to_datetime(end_date))
    ]

    # Chart 1: HIGH vs LOW
    plot_df1 = filtered[[m["date"], m["high"], m["low"]]].rename(
        columns={m["date"]: "Date", m["high"]: "HIGH", m["low"]: "LOW"}
    )

    fig1 = px.line(plot_df1, x="Date", y=["HIGH", "LOW"])
    fig1.update_traces(
        hovertemplate=
            "<b>%{fullData.name}</b><br>"
            "Date: %{x|%d-%m-%y}<br>"
            "Value: %{y}<extra></extra>"
    )
    fig1.update_layout(
        hovermode="x unified",
        height=600,
        template="plotly_white"
    )
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chart 2 & 3
    plot_single_line(
        filtered.rename(columns={m["date"]: "Date", m["hl"]: "H/L Ratio"}),
        "Date",
        "H/L Ratio"
    )

    plot_df3 = filtered[[m["date"], m["hr"], m["lr"]]].rename(
        columns={m["date"]: "Date", m["hr"]: "H RATIO", m["lr"]: "L RATIO"}
    )

    fig3 = px.line(plot_df3, x="Date", y=["H RATIO", "L RATIO"])
    fig3.update_traces(
        hovertemplate=
            "<b>%{fullData.name}</b><br>"
            "Date: %{x|%d-%m-%y}<br>"
            "Value: %{y}<extra></extra>"
    )
    fig3.update_layout(
        hovermode="x unified",
        height=350,
        template="plotly_white"
    )
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.plotly_chart(fig3, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =================================================
# RBI NET LIQUIDITY INJECTED
# =================================================
if view == "RBI Net Liquidity Injected":

    st.subheader("🏦 RBI Net Liquidity Injected (₹ in Lakhs)")

    rbi = df_rbi.copy()
    rbi["DATE-1"] = pd.to_datetime(rbi["DATE-1"])
    rbi["DATE_2"] = pd.to_datetime(rbi["DATE_2"])

    rbi["NET_LIQ_LAKHS"] = rbi["NET LIQ INC TODAY"] / 100000
    rbi["AMOUNT_LAKHS"] = rbi["AMOUNT"] / 100000

    plot_single_line(
        rbi, "DATE-1", "NET_LIQ_LAKHS", 400, "Net Liquidity (Lakhs)"
    )

    plot_single_line(
        rbi, "DATE_2", "AMOUNT_LAKHS", 400, "Amount (Lakhs)"
    )

# =================================================
# ASSET CLASS CHARTS
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
            for img in sorted(images):
                title = img.replace("_", " ").split(".")[0].title()
                st.markdown(f"### {title}")
                st.markdown('<div class="chart-card">', unsafe_allow_html=True)
                st.image(
                    os.path.join(charts_folder, img),
                    use_container_width=True
                )
                st.markdown('</div>', unsafe_allow_html=True)
