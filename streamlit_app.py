import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Hawaiʻi School Performance Dashboard", layout="wide")

# ----------------------------
# load data
# ----------------------------
df = pd.read_csv("combined_kpi_dataset.csv")

numeric_cols = [
    "LA Proficiency (%)",
    "Math Proficiency (%)",
    "Science Proficiency (%)",
    "Regular Attendance (%)",
    "Absenteeism (%)",
    "College Enrollment Rate (%)",
    "Extended High School Completion (%)",
    "On-Time Graduation (%)",
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df["Title I"] = pd.to_numeric(df["Title I"], errors="coerce").fillna(0).astype(int)
df["Title I Label"] = df["Title I"].map({1: "Title I", 0: "Non-Title I"})

metric_options = {
    "Absenteeism": "Absenteeism (%)",
    "Regular Attendance": "Regular Attendance (%)",
    "Math Proficiency": "Math Proficiency (%)",
    "LA Proficiency": "LA Proficiency (%)",
    "Science Proficiency": "Science Proficiency (%)",
    "College Enrollment Rate": "College Enrollment Rate (%)",
    "On-Time Graduation": "On-Time Graduation (%)",
    "Extended High School Completion": "Extended High School Completion (%)",
}

years = sorted(df["Year"].dropna().unique().tolist())
school_types = ["All"] + sorted(df["School Type"].dropna().astype(str).unique().tolist())
areas = ["All"] + sorted(df["Complex Area"].dropna().astype(str).unique().tolist())
subgroups = ["All"] + sorted(df["Subgroup Description"].dropna().astype(str).unique().tolist())

def filter_df(data, years_selected, school_type, area, subgroup):
    filtered = data.copy()

    filtered = filtered[
        (filtered["Year"] >= years_selected[0]) &
        (filtered["Year"] <= years_selected[1])
    ]

    if school_type != "All":
        filtered = filtered[filtered["School Type"] == school_type]

    if area != "All":
        filtered = filtered[filtered["Complex Area"] == area]

    if subgroup != "All":
        filtered = filtered[filtered["Subgroup Description"] == subgroup]

    return filtered

def indicator_figure(title, value):
    fig = go.Figure(
        go.Indicator(
            mode="number",
            value=0 if pd.isna(value) else round(value, 2),
            title={"text": title}
        )
    )
    fig.update_layout(height=180, margin=dict(l=20, r=20, t=50, b=20))
    return fig

# ----------------------------
# page
# ----------------------------
st.title("Hawaiʻi School Performance Dashboard")
st.write("Explore absenteeism, attendance, proficiencies, and school outcomes across Hawaiʻi schools.")

st.sidebar.header("Filters")

metric = st.sidebar.selectbox(
    "Metric",
    options=list(metric_options.values()),
    format_func=lambda x: [k for k, v in metric_options.items() if v == x][0]
)

school_type = st.sidebar.selectbox("School Type", school_types)
area = st.sidebar.selectbox("Complex Area", areas)
subgroup = st.sidebar.selectbox("Subgroup", subgroups)
years_selected = st.sidebar.slider(
    "Year Range",
    min_value=int(min(years)),
    max_value=int(max(years)),
    value=(int(min(years)), int(max(years)))
)

filtered = filter_df(df, years_selected, school_type, area, subgroup)
comparison = filtered.copy()

overall_avg = filtered[metric].mean()
title_avg = comparison.loc[comparison["Title I"] == 1, metric].mean()
non_title_avg = comparison.loc[comparison["Title I"] == 0, metric].mean()
gap = non_title_avg - title_avg

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.plotly_chart(indicator_figure(f"Average {metric}", overall_avg), use_container_width=True)
with col2:
    st.plotly_chart(indicator_figure("Title I Average", title_avg), use_container_width=True)
with col3:
    st.plotly_chart(indicator_figure("Non-Title I Average", non_title_avg), use_container_width=True)
with col4:
    st.plotly_chart(indicator_figure("Gap (Non - Title I)", gap), use_container_width=True)

trend_df = comparison.groupby(["Year", "Title I Label"], as_index=False)[metric].mean()
fig_trend = px.line(
    trend_df,
    x="Year",
    y=metric,
    color="Title I Label",
    markers=True,
    title=f"{metric} Over Time"
)
st.plotly_chart(fig_trend, use_container_width=True)

schooltype_df = (
    filtered.groupby("School Type", as_index=False)[metric]
    .mean()
    .sort_values(metric, ascending=False)
)
fig_schooltype = px.bar(
    schooltype_df,
    x="School Type",
    y=metric,
    color="School Type",
    title=f"{metric} by School Type"
)
fig_schooltype.update_layout(showlegend=False)
st.plotly_chart(fig_schooltype, use_container_width=True)

area_df = (
    filtered.groupby("Complex Area", as_index=False)[metric]
    .mean()
    .sort_values(metric, ascending=False)
)
fig_area = px.bar(
    area_df,
    x="Complex Area",
    y=metric,
    title=f"{metric} by Complex Area"
)
fig_area.update_xaxes(tickangle=35)
st.plotly_chart(fig_area, use_container_width=True)

if metric != "Absenteeism (%)":
    scatter_df = filtered.dropna(subset=["Absenteeism (%)", metric]).copy()
    fig_scatter = px.scatter(
        scatter_df,
        x="Absenteeism (%)",
        y=metric,
        color="Title I Label",
        symbol="School Type",
        hover_data=["School Name", "Complex Area", "Year", "Subgroup Description"],
        trendline="ols",
        title=f"Absenteeism vs {metric}"
    )
else:
    scatter_df = filtered.dropna(subset=["Absenteeism (%)"]).copy()
    fig_scatter = px.histogram(
        scatter_df,
        x="Absenteeism (%)",
        color="Title I Label",
        barmode="overlay",
        title="Absenteeism Distribution"
    )

st.plotly_chart(fig_scatter, use_container_width=True)
