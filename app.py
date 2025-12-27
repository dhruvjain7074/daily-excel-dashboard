import streamlit as st
import pandas as pd
import plotly.express as px
import os

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(page_title="Daily Excel Dashboard", layout="wide")

# =================================================
# GLOBAL CSS (CLEAN + PROFESSIONAL)
# =================================================
st.markdown(
    """
    <style>

    /* ---------- Page ---------- */
    body {
        background-color: #f4f6f9;
        color: #1f2937;
        font-family: "Inter", system-ui, -apple-system, BlinkMacSystemFont;
    }

    .block-container {
        max-width: 1400px;
        padding: 2rem 2.5rem;
        margin: auto;
    }

    /* ---------- Headings ---------- */
    h1 {
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }

    h2, h3 {
        font-weight: 600;
        margin-top: 1.8rem;
    }

    /* ---------- Dropdown ---------- */
    div[data-baseweb="select"] {
        max-width: 380px;
    }

    /* ---------- Section Cards ---------- */
    .section-card {
        background: white;
        border-radius: 10px;
        padding: 1.4rem;
        margin-bottom: 1.6rem;
        border: 1px solid #e5e7eb;
    }

    /* ---------- Asset Chart Grid ---------- */
    .image-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 24px;
        margin-top: 1.2rem;
    }

    .image-item {
        background: white;
        border-radius: 10px;
        padding: 12px;
        border: 1px solid #e5e7eb;
    }

    .image-title {
        font-size: 0.95rem;
        font-weight: 600;
        margin-bottom: 8px;
    }

    img {
        width: 100%;
        border-radius: 8px;
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
# COMMON PLOT FUNCTION
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
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# =================================================
# DATASET 1 / 2 / 3 VIEW
# =================================================
if view in ["Dataset 1", "Dataset 2", "Dataset 3"]:

    m = mapping[view]

    data = df[
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
        height=550,
        template="plotly_white"
    )

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

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

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
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
        rbi,
        "DATE-1",
        "NET_LIQ_LAKHS",
        height=420,
        y_label="Net Liquidity (Lakhs)"
    )

    plot_single_line(
        rbi,
        "DATE_2",
        "AMOUNT_LAKHS",
        height=420,
        y_label="Amount (Lakhs)"
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
        images = sorted(
            f for f in os.listdir(charts_folder)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        )

        if not images:
            st.info("No images found.")
        else:
            st.markdown('<div class="image-grid">', unsafe_allow_html=True)

            for img in images:
                title = img.replace("_", " ").split(".")[0].title()
                st.markdown(
                    f"""
                    <div class="image-item">
                        <div class="image-title">{title}</div>
                        <img src="{charts_folder}/{img}">
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            st.markdown("</div>", unsafe_allow_html=True)
