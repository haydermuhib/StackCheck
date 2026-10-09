"""
Deep Statistical Analytics Tab for StackCheck Web Dashboard.
Renders market analytics KPIs, geographic compensation scatter, currency converter settings,
technology co-occurrence heatmap, salary benchmarks, experience breakdowns, and employer landscape.
"""

from typing import List
import streamlit as st
import pandas as pd
from stackcheck.models import JobPost, AggregatedStats
from stackcheck.analyzer.currency import currency_manager
from stackcheck.web.charts import (
    plot_salary_by_country_scatter,
    plot_co_occurrence_heatmap,
    plot_salary_by_tech,
    plot_distributions,
    plot_experience_skill_matrix,
    plot_top_hiring_companies,
    plot_stack_density_distribution
)


def render_analytics_tab(jobs: List[JobPost], stats: AggregatedStats):
    """Render the deep statistical analytics visualizations and benchmark tables."""
    if not jobs:
        st.info("Run a search in the sidebar to populate statistical visualizations.")
        return

    # High-Level Market Analytics KPIs
    mkpi1, mkpi2, mkpi3, mkpi4 = st.columns(4)
    with mkpi1:
        st.metric(
            "Salary disclosure rate",
            f"{stats.salary_transparency_pct:.1f}%",
            help="Percentage of postings with explicit salary information",
            border=True
        )
    with mkpi2:
        avg_b = stats.stack_density_stats.get("avg_skills_per_job", 0.0) if stats.stack_density_stats else 0.0
        st.metric(
            "Average stack breadth",
            f"{avg_b} skills / job",
            help="Average number of tech skills requested per job post",
            border=True
        )
    with mkpi3:
        rem_med = stats.workplace_salary_stats.get("remote", {}).get("median") if stats.workplace_salary_stats else None
        ons_med = stats.workplace_salary_stats.get("onsite", {}).get("median") if stats.workplace_salary_stats else None
        if rem_med and ons_med and ons_med > 0:
            diff_pct = ((rem_med - ons_med) / ons_med) * 100
            st.metric("Remote pay premium", f"${rem_med:,.0f}/yr", delta=f"{diff_pct:+.1f}% vs onsite", border=True)
        elif rem_med:
            st.metric("Remote median salary", f"${rem_med:,.0f}/yr", border=True)
        else:
            st.metric("Remote pay premium", "N/A", help="Insufficient remote/onsite salary samples", border=True)
    with mkpi4:
        max_b = stats.stack_density_stats.get("max_skills", 0) if stats.stack_density_stats else 0
        st.metric("Max stack density", f"{max_b} skills", help="Highest number of skills required in a single job posting", border=True)

    # 1. Geographic Compensation Scatter / Strip Plot
    st.subheader("Geographic compensation distribution", icon=":material/public:")
    st.caption("Categorical strip plot with horizontal jitter showing individual job posting salaries across countries, with median compensation benchmarks.")
    col_opt1, col_opt2 = st.columns([1.5, 2.5])
    with col_opt1:
        color_option = st.segmented_control(
            "Color markers by:",
            options=["Seniority level", "Workplace mode"],
            default="Seniority level",
            key="geo_scatter_color_by"
        )
        color_key = "experience" if color_option == "Seniority level" else "workplace"

    country_fig = plot_salary_by_country_scatter(stats.country_salary_data, color_by=color_key)
    if country_fig:
        st.pyplot(country_fig, width="stretch")
    else:
        st.info("Insufficient salary and location samples in the current dataset to render country compensation scatter (minimum 2 samples required).")

    with st.expander("Currency normalization and live exchange rates", icon=":material/currency_exchange:", expanded=False):
        st.caption(
            "All international salaries are automatically converted to USD for unified global benchmarks. "
            f"Current source: **{currency_manager.source}** (Last updated: {currency_manager.last_updated or 'Today'})."
        )
        c_btn1, c_btn2, _ = st.columns([1.5, 1.5, 3])
        with c_btn1:
            if st.button("Sync live exchange rates", icon=":material/sync:", key="btn_sync_live_rates"):
                with st.spinner("Fetching latest market rates from Open Exchange API..."):
                    success = currency_manager.fetch_live_rates()
                    if success:
                        st.success("Live rates updated successfully.")
                        st.rerun()
                    else:
                        st.warning("Live sync unavailable (offline/network). Retaining existing rates.")
        with c_btn2:
            if st.button("Reset to default rates", icon=":material/restart_alt:", key="btn_reset_rates"):
                currency_manager.reset_to_defaults()
                st.info("Reset to default baseline rates.")
                st.rerun()

        # Quick editor for common currencies
        common_currs = ["EUR", "GBP", "INR", "PHP", "CAD", "AUD", "CRC", "JPY", "PKR", "BRL", "MXN", "PLN", "SGD", "NZD", "CHF"]
        st.markdown("**Customize exchange rates (1 Currency Unit = X USD):**")
        rate_cols = st.columns(5)
        changed = False
        for i, c_code in enumerate(common_currs):
            curr_rate = currency_manager.rates.get(c_code, 1.0)
            with rate_cols[i % 5]:
                new_r = st.number_input(
                    f"1 {c_code} ($)",
                    value=float(curr_rate),
                    format="%.6f",
                    step=0.0001,
                    key=f"rate_input_{c_code}"
                )
                if abs(new_r - curr_rate) > 1e-7:
                    currency_manager.update_custom_rate(c_code, new_r)
                    changed = True

        if changed:
            st.success("Custom exchange rates saved. Updating analysis.")
            st.rerun()

    # 2. Tech Stack Correlation & Co-Occurrence
    st.subheader("Technology co-occurrence matrix", icon=":material/hub:")
    st.caption("Visualizes how often technologies appear together in the same job requirements (for example Python with SQL, or Tableau with dbt).")
    heatmap_fig = plot_co_occurrence_heatmap(stats, top_n=10)
    if heatmap_fig:
        st.pyplot(heatmap_fig, width="stretch")

    # 3. Salary Benchmarks & Workplace/Experience Distributions
    col_sal, col_dist = st.columns([1.3, 1])

    with col_sal:
        st.subheader("Salary benchmarks by technology", icon=":material/payments:")
        st.caption("Displays Min, Avg, and Max compensation with sample size validation.")
        
        c_ctrl1, c_ctrl2 = st.columns([1, 1.2])
        with c_ctrl1:
            sal_min_samples = st.selectbox(
                "Min postings required (N):",
                options=[1, 2, 3, 5, 10],
                index=2,
                help="Filters out one-off outlier roles that skew salary averages.",
                key="sal_min_samples_select"
            )
        with c_ctrl2:
            sal_sort_mode = st.selectbox(
                "Rank order by:",
                options=["Highest average salary", "Most disclosed postings (sample count)"],
                index=0,
                key="sal_sort_mode_select"
            )
        
        sort_key = "sample_count" if "sample" in sal_sort_mode.lower() else "avg_salary"
        sal_fig = plot_salary_by_tech(stats, min_samples=sal_min_samples, sort_by=sort_key)
        if sal_fig:
            st.pyplot(sal_fig, width="stretch")
        else:
            st.info(f"No technologies have at least {sal_min_samples} salary samples in the current dataset. Try lowering the minimum postings threshold.")

    with col_dist:
        st.subheader("Workplace and experience distribution", icon=":material/pie_chart:")
        fig_wp, fig_exp = plot_distributions(stats)
        if fig_wp:
            st.pyplot(fig_wp, width="stretch")
        if fig_exp:
            st.pyplot(fig_exp, width="stretch")

    # 4. Seniority & Experience Intelligence
    st.subheader("Seniority and experience patterns", icon=":material/school:")
    st.caption("Top demanded technologies and salary progression across career seniority tiers.")
    col_exp_chart, col_exp_bench = st.columns([1.5, 1])

    with col_exp_chart:
        exp_fig = plot_experience_skill_matrix(stats.experience_skills_breakdown)
        if exp_fig:
            st.pyplot(exp_fig, width="stretch")
        else:
            st.info("No experience-segmented skill distribution data available.")

    with col_exp_bench:
        st.markdown("##### Compensation by experience tier")
        if stats.experience_salary_stats:
            exp_rows = []
            order = ["entry", "mid", "senior", "lead", "executive"]
            sorted_tiers = sorted(
                stats.experience_salary_stats.keys(),
                key=lambda x: order.index(x.lower()) if x.lower() in order else 99
            )
            for tier in sorted_tiers:
                t_data = stats.experience_salary_stats[tier]
                exp_rows.append({
                    "Tier": tier.capitalize(),
                    "Median Salary": f"${t_data['median']:,.0f}",
                    "Min - Max Range": f"${t_data['min']:,.0f} - ${t_data['max']:,.0f}",
                    "Samples": int(t_data["count"])
                })
            st.dataframe(pd.DataFrame(exp_rows), width="stretch", hide_index=True)
        else:
            st.caption("No salary samples tagged with experience level.")

    # 5. Employer Landscape & Tech Stack Density
    st.subheader("Employer landscape and stack density", icon=":material/domain:")
    col_comp, col_dens = st.columns([1.2, 1])

    with col_comp:
        st.caption("Top companies actively hiring for these skillsets and their primary tech stacks.")
        comp_fig = plot_top_hiring_companies(stats.top_hiring_companies, top_n=10)
        if comp_fig:
            st.pyplot(comp_fig, width="stretch")
        else:
            st.info("No employer hiring data available.")

    with col_dens:
        st.caption("Distribution of how many distinct technologies and tools are demanded per job posting.")
        dens_fig = plot_stack_density_distribution(stats.stack_density_stats)
        if dens_fig:
            st.pyplot(dens_fig, width="stretch")
        else:
            st.info("No stack density distribution available.")

    # 6. Geographic Table
    if stats.geo_breakdown:
        st.subheader("Regional technology distribution", icon=":material/map:")
        geo_rows = []
        for reg_name, g_info in stats.geo_breakdown.items():
            top_skills_str = ", ".join([f"{s['skill']} ({s['percentage']}%)" for s in g_info.top_skills[:4]])
            geo_rows.append({
                "Region": reg_name,
                "Postings Count": g_info.total_jobs,
                "Top Demanded Technologies": top_skills_str
            })
        st.dataframe(pd.DataFrame(geo_rows), width="stretch", hide_index=True)
