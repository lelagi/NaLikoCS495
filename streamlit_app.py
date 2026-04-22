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

# Clean Title I column:
# "Yes" = Title I
# blank = Non-Title I
df["Title I"] = df["Title I"].fillna("").astype(str).str.strip()
df["Title I"] = df["Title I"].apply(lambda x: 1 if x.lower() == "yes" else 0)
df["Title I Label"] = df["Title I"].map({1: "Title I", 0: "Non-Title I"})

metric_options = {
    "Absenteeism": "Absenteeism (%)",
    "Regular Attendance": "Regular Attendance (%)",
    "Math Proficiency": "Math Proficiency (%)",
    "Language Arts Proficiency": "LA Proficiency (%)",
    "Science Proficiency": "Science Proficiency (%)",
    "College Enrollment Rate": "College Enrollment Rate (%)",
    "On-Time Graduation": "On-Time Graduation (%)",
    "Extended High School Completion": "Extended High School Completion (%)",
}

metric_label_lookup = {v: k for k, v in metric_options.items()}

years = sorted(df["Year"].dropna().unique().tolist())
school_types = ["All"] + sorted(df["School Type"].dropna().astype(str).unique().tolist())
areas = ["All"] + sorted(df["Complex Area"].dropna().astype(str).unique().tolist())
subgroups = ["All"] + sorted(df["Subgroup Description"].dropna().astype(str).unique().tolist())

title_colors = {
    "Title I": "#E45756",
    "Non-Title I": "#4C78A8"
}

# ----------------------------
# helper functions
# ----------------------------
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

def filter_year_only(data, years_selected):
    filtered = data.copy()
    filtered = filtered[
        (filtered["Year"] >= years_selected[0]) &
        (filtered["Year"] <= years_selected[1])
    ]
    return filtered

def indicator_figure(title, value):
    fig = go.Figure(
        go.Indicator(
            mode="number",
            value=0 if pd.isna(value) else round(value, 2),
            number={"valueformat": ".2f"},
            title={"text": title}
        )
    )
    fig.update_layout(height=180, margin=dict(l=20, r=20, t=50, b=20))
    return fig

def empty_figure(message):
    fig = go.Figure()
    fig.update_layout(
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 16}
            }
        ],
        height=400
    )
    return fig

# ----------------------------
# page
# ----------------------------
st.title("Hawaiʻi School Performance Dashboard")
st.write(
    "Compare outcomes between Title I and Non-Title I schools across Hawaiʻi, "
    "then explore patterns by school type, complex area, subgroup, and year."
)

st.info(
    "Title I comparison cards and the trend chart reflect all schools in the selected year range. "
    "The other charts reflect the additional sidebar filters."
)

# ----------------------------
# sidebar
# ----------------------------
st.sidebar.header("Filters")

metric = st.sidebar.selectbox(
    "Metric",
    options=list(metric_options.values()),
    format_func=lambda x: metric_label_lookup[x]
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

metric_display_name = metric_label_lookup[metric]

# ----------------------------
# filtered datasets
# ----------------------------
filtered = filter_df(df, years_selected, school_type, area, subgroup)
comparison = filter_year_only(df, years_selected)

# ----------------------------
# KPI cards
# ----------------------------
overall_avg = filtered[metric].mean()
title_avg = comparison.loc[comparison["Title I"] == 1, metric].mean()
non_title_avg = comparison.loc[comparison["Title I"] == 0, metric].mean()
gap = non_title_avg - title_avg

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.plotly_chart(
        indicator_figure(f"Selected Group Average: {metric_display_name}", overall_avg),
        use_container_width=True
    )
with col2:
    st.plotly_chart(
        indicator_figure(f"Title I Average: {metric_display_name}", title_avg),
        use_container_width=True
    )
with col3:
    st.plotly_chart(
        indicator_figure(f"Non-Title I Average: {metric_display_name}", non_title_avg),
        use_container_width=True
    )
with col4:
    st.plotly_chart(
        indicator_figure("Gap: Non-Title I minus Title I", gap),
        use_container_width=True
    )

# ----------------------------
# trend chart
# ----------------------------
trend_df = comparison.groupby(["Year", "Title I Label"], as_index=False)[metric].mean()

if trend_df.empty:
    st.plotly_chart(
        empty_figure("No data available for the selected year range."),
        use_container_width=True
    )
else:
    fig_trend = px.line(
        trend_df,
        x="Year",
        y=metric,
        color="Title I Label",
        markers=True,
        title=f"{metric_display_name} Over Time: Title I vs Non-Title I",
        color_discrete_map=title_colors
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    if pd.notna(title_avg) and pd.notna(non_title_avg):
        if metric == "Absenteeism (%)":
            if title_avg > non_title_avg:
                takeaway = (
                    f"Across {years_selected[0]}–{years_selected[1]}, Title I schools show higher average "
                    f"{metric_display_name.lower()} than Non-Title I schools."
                )
            elif title_avg < non_title_avg:
                takeaway = (
                    f"Across {years_selected[0]}–{years_selected[1]}, Non-Title I schools show higher average "
                    f"{metric_display_name.lower()} than Title I schools."
                )
            else:
                takeaway = (
                    f"Across {years_selected[0]}–{years_selected[1]}, Title I and Non-Title I schools show similar "
                    f"average {metric_display_name.lower()}."
                )
        else:
            if non_title_avg > title_avg:
                takeaway = (
                    f"Across {years_selected[0]}–{years_selected[1]}, Non-Title I schools show higher average "
                    f"{metric_display_name.lower()} than Title I schools."
                )
            elif title_avg > non_title_avg:
                takeaway = (
                    f"Across {years_selected[0]}–{years_selected[1]}, Title I schools show higher average "
                    f"{metric_display_name.lower()} than Non-Title I schools."
                )
            else:
                takeaway = (
                    f"Across {years_selected[0]}–{years_selected[1]}, Title I and Non-Title I schools show similar "
                    f"average {metric_display_name.lower()}."
                )
        st.caption(takeaway)

# ----------------------------
# filtered charts
# ----------------------------
if filtered.empty:
    st.warning("No data available for this filter combination. Try changing School Type, Complex Area, Subgroup, or Year Range.")
else:
    schooltype_df = (
        filtered.groupby("School Type", as_index=False)[metric]
        .mean()
        .sort_values(metric, ascending=False)
    )

    if schooltype_df.empty:
        fig_schooltype = empty_figure("No school type data available for this filter combination.")
    else:
        fig_schooltype = px.bar(
            schooltype_df,
            x="School Type",
            y=metric,
            color="School Type",
            title=f"{metric_display_name} by School Type"
        )
        fig_schooltype.update_layout(showlegend=False)

    st.plotly_chart(fig_schooltype, use_container_width=True)

    area_df = (
        filtered.groupby("Complex Area", as_index=False)[metric]
        .mean()
        .sort_values(metric, ascending=False)
    )

    if area_df.empty:
        fig_area = empty_figure("No complex area data available for this filter combination.")
    else:
        fig_area = px.bar(
            area_df,
            x="Complex Area",
            y=metric,
            title=f"{metric_display_name} by Complex Area"
        )
        fig_area.update_xaxes(tickangle=35)

    st.plotly_chart(fig_area, use_container_width=True)

    if metric != "Absenteeism (%)":
        scatter_df = filtered.dropna(subset=["Absenteeism (%)", metric]).copy()

        if scatter_df.empty:
            fig_scatter = empty_figure("No scatterplot data available for this filter combination.")
        else:
            fig_scatter = px.scatter(
                scatter_df,
                x="Absenteeism (%)",
                y=metric,
                color="Title I Label",
                symbol="School Type",
                hover_data=["School Name", "Complex Area", "Year", "Subgroup Description"],
                trendline="ols",
                title=f"Absenteeism vs {metric_display_name}",
                color_discrete_map=title_colors
            )
    else:
        scatter_df = filtered.dropna(subset=["Absenteeism (%)"]).copy()

        if scatter_df.empty:
            fig_scatter = empty_figure("No absenteeism distribution data available for this filter combination.")
        else:
            fig_scatter = px.histogram(
                scatter_df,
                x="Absenteeism (%)",
                color="Title I Label",
                barmode="overlay",
                title="Absenteeism Distribution",
                color_discrete_map=title_colors
            )

    st.plotly_chart(fig_scatter, use_container_width=True)        (filtered["Year"] >= years_selected[0]) &
        (filtered["Year"] <= years_selected[1])
    ]
    return filtered

def indicator_figure(title, value):
    display_value = None if pd.isna(value) else round(value, 2)

    fig = go.Figure(
        go.Indicator(
            mode="number",
            value=0 if display_value is None else display_value,
            number={"valueformat": ".2f"},
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

# Filtered data for exploration charts
filtered = filter_df(df, years_selected, school_type, area, subgroup)

# Comparison data for Title I vs Non-Title I story
comparison = filter_year_only(df, years_selected)

overall_avg = filtered[metric].mean()
title_avg = comparison.loc[comparison["Title I"] == 1, metric].mean()
non_title_avg = comparison.loc[comparison["Title I"] == 0, metric].mean()
gap = non_title_avg - title_avg

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.plotly_chart(indicator_figure(f"Filtered Average {metric}", overall_avg), use_container_width=True)
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
    title=f"{metric} Over Time: Title I vs Non-Title I"
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
