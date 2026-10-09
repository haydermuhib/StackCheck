"""
Executive Dashboard Tab for StackCheck Web Dashboard.
Renders high-level KPIs, top skills demand chart, and domain category breakdown.
"""

from typing import List
import streamlit as st
from stackcheck.models import JobPost, AggregatedStats
from stackcheck.web.charts import plot_top_skills, plot_category_breakdown


def render_dashboard_tab(jobs: List[JobPost], stats: AggregatedStats):
    """Render the executive dashboard KPI cards and overview charts."""
    if not jobs:
        st.info(
            "Welcome to StackCheck. Use the left sidebar to select a role or country, "
            "then click 'Collect postings into project' to analyze live job market data."
        )
        return

    # Top KPI Cards
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    top_skill_name = stats.top_skills_overall[0]["skill"] if stats.top_skills_overall else "N/A"
    top_skill_pct = f"{stats.top_skills_overall[0]['percentage']}%" if stats.top_skills_overall else "0%"
    
    # Compute average market salary
    avg_salary_val = 0
    if stats.salary_by_top_tech:
        sal_list = [v["avg"] for v in stats.salary_by_top_tech.values() if v.get("avg", 0) > 0]
        if sal_list:
            avg_salary_val = sum(sal_list) / len(sal_list)
    salary_str = f"${avg_salary_val:,.0f} / yr" if avg_salary_val > 0 else "Disclosed in postings"

    with kpi1:
        st.metric("Total jobs analyzed", f"{stats.total_jobs}", border=True)
    with kpi2:
        st.metric("Unique companies", f"{stats.unique_companies}", border=True)
    with kpi3:
        st.metric("Top demanded skill", f"{top_skill_name}", delta=f"{top_skill_pct} of jobs", border=True)
    with kpi4:
        st.metric("Average benchmark salary", salary_str, border=True)

    col_chart, col_side = st.columns([1.6, 1])

    with col_chart:
        st.subheader("Top in-demand technologies", icon=":material/bar_chart:")
        weight_toggle = st.checkbox("Apply section-weighted priority multipliers (1.8x requirements vs 1.0x context)", value=False)
        fig_top = plot_top_skills(stats, top_n=14, use_weighted=weight_toggle)
        if fig_top:
            st.pyplot(fig_top, width="stretch")

    with col_side:
        st.subheader("Domain category breakdown", icon=":material/category:")
        fig_cat = plot_category_breakdown(stats)
        if fig_cat:
            st.pyplot(fig_cat, width="stretch")
        else:
            st.write("No category data available.")
