import streamlit as st
import pandas as pd
import plotly.express as px

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Daily Excel Dashboard", layout="wide")

# -------------------------------------------------
# REMOVE STREAMLIT SIDE PADDING
# -------------------------------------------------
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

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------
def load_data():
    df = pd.read_excel("Book1.xlsx")
    df.columns = df.columns.str.strip()
    return df

if st.button("🔄 Refresh Data"):
    st.cache_data.clear()

df = load_data()

# -------------------------------------------------
# DATASET SELECTOR
# -------------------------------------------------
dataset = st.selectbox(
    "Select Dataset",
    ["Dataset 1", "Dataset 2", "Dataset 3"]
)

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

m = mapping[dataset]

data = df[
    [m["date"], m["high"], m["low"], m["hl"], m["hr"], m["lr"]]
].dropna()

data[m["date"]] = pd.to_datetime(data[m["date"]])

# -------------------------------------------------
# DATE FILTER
# -------------------------------------------------
st.subheader("📅 Date Filter")

min_date = data[m["date"]].min().date()
max_date = data[m["date"]].max().date()

start_date, end_date = st.date_input(
    "Select date range",
    [min_date, max_date]
)

filtered_data = data[
    (data[m["date"]] >= pd.to_datetime(start_date)) &
    (data[m["date"]] <= pd.to_datetime(end_date))
]

# -------------------------------------------------
# RAW DATA
# -------------------------------------------------
st.subheader(f"{dataset} – Raw Data")
st.dataframe(filtered_data)

st.subheader("📈 Charts")

# =================================================
# CHART 1 – HIGH vs LOW
# =================================================
plot_df1 = filtered_data[[m["date"], m["high"], m["low"]]].rename(
    columns={m["date"]: "Date", m["high"]: "HIGH", m["low"]: "LOW"}
)

fig1 = px.line(plot_df1, x="Date", y=["HIGH", "LOW"])

fig1.update_traces(
    line=dict(width=2.8),
    hovertemplate=
        "<b>%{fullData.name}</b><br>" +
        "Date: %{x|%d-%m-%y}<br>" +
        "Value: %{y}<extra></extra>"
)

fig1.update_layout(
    hovermode="x unified",
    height=600,
    margin=dict(l=10, r=10, t=50, b=60),
    template="plotly_white",
    legend=dict(
        x=0.99, y=0.99,
        xanchor="right", yanchor="top",
        bgcolor="rgba(255,255,255,0.6)",
        borderwidth=1
    )
)

st.plotly_chart(fig1, use_container_width=True)

# =================================================
# CHART 2 – H/L RATIO
# =================================================
plot_df2 = filtered_data[[m["date"], m["hl"]]].rename(
    columns={m["date"]: "Date", m["hl"]: "H/L Ratio"}
)

fig2 = px.line(plot_df2, x="Date", y="H/L Ratio")

fig2.update_traces(
    line=dict(width=2.5),
    hovertemplate=
        "Date: %{x|%d-%m-%y}<br>" +
        "Value: %{y}<extra></extra>"
)

fig2.update_layout(
    hovermode="x unified",
    height=350,
    margin=dict(l=10, r=10, t=40, b=50),
    template="plotly_white"
)

st.plotly_chart(fig2, use_container_width=True)

# =================================================
# CHART 3 – H RATIO vs L RATIO
# =================================================
plot_df3 = filtered_data[[m["date"], m["hr"], m["lr"]]].rename(
    columns={m["date"]: "Date", m["hr"]: "H RATIO", m["lr"]: "L RATIO"}
)

fig3 = px.line(plot_df3, x="Date", y=["H RATIO", "L RATIO"])

fig3.update_traces(
    line=dict(width=2.5),
    hovertemplate=
        "<b>%{fullData.name}</b><br>" +
        "Date: %{x|%d-%m-%y}<br>" +
        "Value: %{y}<extra></extra>"
)

fig3.update_layout(
    hovermode="x unified",
    height=350,
    margin=dict(l=10, r=10, t=40, b=50),
    template="plotly_white"
)

st.plotly_chart(fig3, use_container_width=True)

# =================================================
# DATASET-SPECIFIC EXTRA CHARTS
# =================================================
st.subheader("📌 Additional Charts")

def single_line_chart(df, x_col, y_col, height=300):
    fig = px.line(df, x=x_col, y=y_col)
    fig.update_traces(
        line=dict(width=2.5),
        hovertemplate=
            "Date: %{x|%d-%m-%y}<br>" +
            "Value: %{y}<extra></extra>"
    )
    fig.update_layout(
        hovermode="x unified",
        height=height,
        margin=dict(l=10, r=10, t=40, b=50),
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

if dataset == "Dataset 1":
    single_line_chart(filtered_data, "DATE 1", "HIGH 1")
    single_line_chart(filtered_data, "DATE 1", "LOW 1")

if dataset == "Dataset 2":
    single_line_chart(filtered_data, "DATE 2", "HIGH 2")
    single_line_chart(filtered_data, "DATE 2", "LOW 2")

if dataset == "Dataset 3":
    single_line_chart(filtered_data, "DATE 3", "HIGH 3")
    single_line_chart(filtered_data, "DATE 3", "LOW 3")
