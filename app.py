import streamlit as st
import pandas as pd
import plotly.express as px
import os
import base64
import io

# =================================================
# PASSWORD PROTECTION
# =================================================
def check_password():
    def password_entered():
        if st.session_state["password"] == "Market@2025":  # 🔴 CHANGE PASSWORD
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("🔐 Enter Password", type="password",
                      on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("🔐 Enter Password", type="password",
                      on_change=password_entered, key="password")
        st.error("❌ Incorrect password")
        return False
    return True


# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(page_title="Daily Excel Dashboard", layout="wide")

# BLOCK APP UNTIL PASSWORD IS CORRECT
if not check_password():
    st.stop()

st.title("📊 Daily Excel Dashboard")

# =================================================
# LOAD EXCEL FROM STREAMLIT SECRETS (PRIVATE)
# =================================================
try:
    excel_bytes = base64.b64decode(st.secrets["files"]["book1"])
except Exception:
    st.error("❌ Excel file not found in Streamlit Secrets.")
    st.stop()

excel_file = io.BytesIO(excel_bytes)

df_main = pd.read_excel(excel_file, sheet_name="comparision charts")
df_rbi = pd.read_excel(excel_file, sheet_name="Rbi net liquidity")

df_main.columns = df_main.columns.str.strip()
df_rbi.columns = df_rbi.columns.str.strip()

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
        "date": "DATE 1", "high": "HIGH 1", "low": "LOW 1",
        "hl": "H/L 1", "hr": "H RATIO 1", "lr": "L RATIO 1"
    },
    "Dataset 2": {
        "date": "DATE 2", "high": "HIGH 2", "low": "LOW 2",
        "hl": "H/L 2", "hr": "H RATIO 2", "lr": "L RATIO 2"
    },
    "Dataset 3": {
        "date": "DATE 3", "high": "HIGH 3", "low": "LOW 3",
        "hl": "H/L 3", "hr": "H RATIO 3", "lr": "L RATIO 3"
    }
}

# =================================================
# COMMON PLOT FUNCTION
# =================================================
def plot_single_line(df, x, y, height=350, y_label=None):
    fig = px.line(df, x=x, y=y)
    fig.update_traces(
        line=dict(width=2.6),
        hovertemplate="Date: %{x|%d-%m-%y}<br>Value: %{y}<extra></extra>"
    )
    fig.update_layout(
        hovermode="x unified",
        height=height,
        yaxis_title=y_label,
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

# =================================================
# DATASET 1 / 2 / 3
# =================================================
if view in ["Dataset 1", "Dataset 2", "Dataset 3"]:

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

    # HIGH vs LOW
    plot_df1 = filtered[[m["date"], m["high"], m["low"]]].rename(
        columns={m["date"]: "Date", m["high"]: "HIGH", m["low"]: "LOW"}
    )

    fig1 = px.line(plot_df1, x="Date", y=["HIGH", "LOW"])
    fig1.update_traces(
        hovertemplate="<b>%{fullData.name}</b><br>Date: %{x|%d-%m-%y}<br>Value: %{y}<extra></extra>"
    )
    fig1.update_layout(hovermode="x unified", height=550)
    st.plotly_chart(fig1, use_container_width=True)

    # H/L Ratio
    plot_single_line(
        filtered.rename(columns={m["date"]: "Date", m["hl"]: "H/L Ratio"}),
        "Date",
        "H/L Ratio"
    )

    # H Ratio vs L Ratio
    plot_df3 = filtered[[m["date"], m["hr"], m["lr"]]].rename(
        columns={m["date"]: "Date", m["hr"]: "H RATIO", m["lr"]: "L RATIO"}
    )

    fig3 = px.line(plot_df3, x="Date", y=["H RATIO", "L RATIO"])
    fig3.update_layout(hovermode="x unified", height=350)
    st.plotly_chart(fig3, use_container_width=True)

# =================================================
# RBI NET LIQUIDITY
# =================================================
if view == "RBI Net Liquidity Injected":

    st.subheader("🏦 RBI Net Liquidity Injected (₹ in Lakhs)")

    rbi = df_rbi.copy()
    rbi["DATE-1"] = pd.to_datetime(rbi["DATE-1"])
    rbi["DATE_2"] = pd.to_datetime(rbi["DATE_2"])

    rbi["NET_LIQ_LAKHS"] = rbi["NET LIQ INC TODAY"] / 100000
    rbi["AMOUNT_LAKHS"] = rbi["AMOUNT"] / 100000

    plot_single_line(rbi, "DATE-1", "NET_LIQ_LAKHS", 400)
    plot_single_line(rbi, "DATE_2", "AMOUNT_LAKHS", 400)

# =================================================
# ASSET CLASS CHARTS (STATIC IMAGES)
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

        for img in images:
            title = img.replace("_", " ").split(".")[0].title()
            st.markdown(f"### {title}")
            st.image(os.path.join(charts_folder, img), use_container_width=True)
