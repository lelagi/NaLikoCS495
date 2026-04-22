import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Hawaiʻi School Performance Dashboard",
    layout="wide"
)

# ----------------------------
# COLORS / STYLE
# ----------------------------
PAGE_BG = "#061C3B"
PANEL_BG = "rgba(21, 58, 105, 0.78)"
PANEL_BORDER = "#2EB8FF"
TEXT_MAIN = "#F4F8FF"
TEXT_MUTED = "#B7CAE6"
TITLE_COLOR = "#2EB8FF"
TITLE_I_COLOR = "#F2C94C"
NON_TITLE_I_COLOR = "#56CCF2"
GRID_COLOR = "rgba(183, 202, 230, 0.18)"

st.markdown(
    f"""
    <style>
    .stApp {{
        background:
            radial-gradient(circle at top, rgba(46,184,255,0.12), transparent 28%),
            linear-gradient(180deg, #04162F 0%, {PAGE_BG} 100%);
        color: {TEXT_MAIN};
    }}

    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, #0B254A 0%, #081A34 100%);
        border-right: 1px solid rgba(46,184,255,0.25);
    }}

    section[data-testid="stSidebar"] * {{
        color: {TEXT_MAIN} !important;
    }}

    .block-container {{
        padding-top: 2rem;
        padding-bottom: 2rem;
    }}

    .hero-title {{
        font-size: 3rem;
        font-weight: 800;
        color: white;
        line-height: 1.0;
        margin-bottom: 0.3rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}

    .hero-title span {{
        color: {TITLE_COLOR};
    }}

    .hero-subtitle {{
        font-size: 1.25rem;
        color: {TEXT_MAIN};
        margin-bottom: 0.35rem;
        font-weight: 600;
    }}

    .hero-caption {{
        color: {TEXT_MUTED};
        font-size: 0.98rem;
        margin-bottom: 1.2rem;
    }}

    .section-title {{
        color: {TITLE_COLOR};
        font-size: 1.65rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 1.25rem;
        margin-bottom: 0.55rem;
    }}

    .note-box {{
        background: rgba(46,184,255,0.09);
        border: 1px solid rgba(46,184,255,0.35);
        border-radius: 14px;
        padding: 0.85rem 1rem;
        color: {TEXT_MAIN};
        margin-bottom: 1rem;
    }}

    .mini-note {{
        color: {TEXT_MUTED};
        font-size: 0.9rem;
        margin-top: -0.15rem;
        margin-bottom: 1rem;
    }}

    .metric-card {{
        background: {PANEL_BG};
        border: 1px solid rgba(46,184,255,0.32);
        box-shadow: 0 0 0 1px rgba(46,184,255,0.08), 0 8px 24px rgba(0,0,0,0.22);
        border-radius: 18px;
        padding: 1rem 1rem 0.85rem 1rem;
        min-height: 135px;
    }}

    .metric-label {{
        color: {TEXT_MUTED};
        font-size: 0.95rem;
        font-weight: 700;
        margin-bottom: 0.55rem;
    }}

    .metric-value {{
        color: white;
        font-size: 2.7rem;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 0.2rem;
    }}

    .metric-foot {{
        color: {TEXT_MUTED};
        font-size: 0.82rem;
        margin-top: 0.35rem;
    }}

    div[data-testid="stPlotlyChart"] {{
        background: {PANEL_BG};
        border: 1px solid rgba(46,184,255,0.28);
        border-radius: 18px;
        padding: 0.6rem 0.6rem 0.2rem 0.6rem;
        box-shadow: 0 8px 24px rgba(0,0,0,0.22);
    }}

    .stSelectbox label, .stSlider label {{
        color: {TEXT_MAIN} !important;
        font-weight: 700 !important;
    }}

    .stAlert {{
        border-radius: 14px;
    }}

    hr {{
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(46,184,255,0.45), transparent);
        margin-top: 1.2rem;
        margin-bottom: 1.2rem;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# LOAD DATA
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

# Title I cleaning:
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
    "Title I": TITLE_I_COLOR,
    "Non-Title I": NON_TITLE_I_COLOR
}

# ----------------------------
# HELPERS
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


def format_value(val):
    if pd.isna(val):
        return "N/A"
    return f"{val:.1f}"


def metric_card(label, value, footnote=""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{format_value(value)}</div>
            <div class="metric-foot">{footnote}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def empty_figure(message):
    fig = go.Figure()
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 16, "color": TEXT_MUTED}
            }
        ],
        height=420,
        margin=dict(l=30, r=30, t=60, b=30),
    )
    return fig


def apply_chart_theme(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT_MAIN),
        title_font=dict(size=20, color=TEXT_MAIN),
        legend_title_font=dict(color=TEXT_MUTED),
        legend_font=dict(color=TEXT_MAIN),
        margin=dict(l=35, r=25, t=70, b=45),
        xaxis=dict(
            gridcolor=GRID_COLOR,
            zerolinecolor=GRID_COLOR,
            title_font=dict(color=TEXT_MUTED),
            tickfont=dict(color=TEXT_MUTED),
        ),
        yaxis=dict(
            gridcolor=GRID_COLOR,
            zerolinecolor=GRID_COLOR,
            title_font=dict(color=TEXT_MUTED),
            tickfont=dict(color=TEXT_MUTED),
        ),
    )
    return fig


# ----------------------------
# HEADER
# ----------------------------
st.markdown(
    """
    <div class="hero-title">
        HAWAIʻI SCHOOL PERFORMANCE <span>DASHBOARD</span>
    </div>
    <div class="hero-subtitle">
        Interactive Visualization of Attendance, Absenteeism, and Student Outcomes
    </div>
    <div class="hero-caption">
        Compare Title I and Non-Title I schools across Hawaiʻi, then explore patterns by school type,
        complex area, subgroup, and year.
    </div>
    """,
    unsafe_allow_html=True
)

# Optional: if you add a logo or image file to your repo, uncomment this:
# st.image("your_header_image.png", use_container_width=True)

st.markdown(
    """
    <div class="note-box">
        <strong>Dashboard guide:</strong> The Title I comparison cards and trend chart reflect all schools in the selected year range.
        The other charts reflect the additional sidebar filters.
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# SIDEBAR
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
# FILTERED DATA
# ----------------------------
filtered = filter_df(df, years_selected, school_type, area, subgroup)
comparison = filter_year_only(df, years_selected)

overall_avg = filtered[metric].mean()
title_avg = comparison.loc[comparison["Title I"] == 1, metric].mean()
non_title_avg = comparison.loc[comparison["Title I"] == 0, metric].mean()
gap = non_title_avg - title_avg

# ----------------------------
# KPI CARDS
# ----------------------------
st.markdown('<div class="section-title">Explore the Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="mini-note">Use the filters on the left to explore selected groups while keeping the statewide Title I comparison visible.</div>',
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card(
        f"Selected Group Average: {metric_display_name}",
        overall_avg,
        "Reflects the current sidebar filters."
    )
with c2:
    metric_card(
        f"Title I Average: {metric_display_name}",
        title_avg,
        "All Title I schools in selected years."
    )
with c3:
    metric_card(
        f"Non-Title I Average: {metric_display_name}",
        non_title_avg,
        "All Non-Title I schools in selected years."
    )
with c4:
    metric_card(
        "Gap: Non-Title I minus Title I",
        gap,
        "Positive values mean Non-Title I is higher."
    )

st.markdown("<hr>", unsafe_allow_html=True)

# ----------------------------
# TREND CHART
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
    fig_trend = apply_chart_theme(fig_trend)
    st.plotly_chart(fig_trend, use_container_width=True)

    if pd.notna(title_avg) and pd.notna(non_title_avg):
        if metric == "Absenteeism (%)":
            if title_avg > non_title_avg:
                takeaway = f"Across {years_selected[0]}–{years_selected[1]}, Title I schools show higher average absenteeism than Non-Title I schools."
            elif title_avg < non_title_avg:
                takeaway = f"Across {years_selected[0]}–{years_selected[1]}, Non-Title I schools show higher average absenteeism than Title I schools."
            else:
                takeaway = f"Across {years_selected[0]}–{years_selected[1]}, Title I and Non-Title I schools show similar average absenteeism."
        else:
            if non_title_avg > title_avg:
                takeaway = f"Across {years_selected[0]}–{years_selected[1]}, Non-Title I schools show higher average {metric_display_name.lower()} than Title I schools."
            elif title_avg > non_title_avg:
                takeaway = f"Across {years_selected[0]}–{years_selected[1]}, Title I schools show higher average {metric_display_name.lower()} than Non-Title I schools."
            else:
                takeaway = f"Across {years_selected[0]}–{years_selected[1]}, Title I and Non-Title I schools show similar average {metric_display_name.lower()}."

        st.markdown(
            f'<div class="note-box"><strong>Key takeaway:</strong> {takeaway}</div>',
            unsafe_allow_html=True
        )

# ----------------------------
# FILTERED CHARTS
# ----------------------------
st.markdown('<div class="section-title">Filtered Exploration</div>', unsafe_allow_html=True)

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
        fig_schooltype = apply_chart_theme(fig_schooltype)
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
            title=f"{metric_display_name} by Complex Area",
            color_discrete_sequence=[TITLE_COLOR]
        )
        fig_area = apply_chart_theme(fig_area)
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
            fig_scatter = apply_chart_theme(fig_scatter)

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
            fig_scatter = apply_chart_theme(fig_scatter)

    st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown(
    """
    <div class="mini-note">
        Styling inspired by your brochure’s dark blue background, bright cyan headings, and highlighted dashboard presentation layout.
    </div>
    """,
    unsafe_allow_html=True
)    if school_type != "All":
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

    st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown(
    """
    <div class="mini-note">
        Styling inspired by your brochure’s dark blue background, bright cyan headings, and highlighted dashboard presentation layout.
    </div>
    """,
    unsafe_allow_html=True
)
