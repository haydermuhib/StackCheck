"""
Job Explorer & Data Exports Tab for StackCheck Web Dashboard.
Renders interactive multi-criteria filter controls, tabular job post directory,
detailed section/requirement cards, and file download exporters.
"""

import json
from typing import List
import streamlit as st


from stackcheck.models import JobPost, AggregatedStats, Project
from stackcheck.analyzer.metrics import MetricsEngine
from stackcheck.storage.exporters import ReportExporter


def render_jobs_tab(jobs: List[JobPost], stats: AggregatedStats, active_project: Project):
    """Render the jobs explorer directory, filtering controls, and dataset exporters."""
    if not jobs:
        st.info("No job postings available to explore. Run a search to populate.")
        return

    st.subheader(f"Extracted postings directory ({len(jobs)} total in {active_project.name})", icon=":material/table_rows:")
    
    # Interactive Multi-Select Filter Controls
    col_f0, col_f1, col_f2 = st.columns([1.2, 1.4, 1.4])
    with col_f0:
        search_runs = st.session_state.repo.get_search_runs(project_id=st.session_state.active_project_id)
        run_options = ["All searches in project"] + [f"{r['keywords']} ({r['total_found']} jobs) • {r['created_at'][:16]}" for r in search_runs]
        run_map = {f"{r['keywords']} ({r['total_found']} jobs) • {r['created_at'][:16]}": r["id"] for r in search_runs}
        selected_run_label = st.selectbox("Scrape batch or run:", run_options)
        selected_run_id = run_map.get(selected_run_label)

    with col_f1:
        standard_exps = ["Entry", "Mid", "Senior", "Lead", "Executive", "Any"]
        available_exps = [e for e in standard_exps if any(j.experience_level.value.capitalize() == e for j in jobs)]
        if not available_exps:
            available_exps = sorted(list({j.experience_level.value.capitalize() for j in jobs if j.experience_level}))
        selected_exps = st.multiselect(
            "Filter by experience level:",
            options=available_exps,
            placeholder="All levels (e.g. Entry, Mid)...",
            help="Select one or multiple experience levels, or leave empty for all."
        )

    with col_f2:
        available_countries = sorted(list({j.country for j in jobs if j.country and j.country != "Unknown"}))
        selected_countries = st.multiselect(
            "Filter by country:",
            options=available_countries,
            placeholder="All countries...",
            help="Select one or multiple countries, or leave empty for all."
        )

    col_s1, col_s2 = st.columns([1.8, 1.2])
    with col_s1:
        all_extracted_skills = sorted(list({s.canonical_name for j in jobs for s in j.extracted_skills}))
        selected_skills = st.multiselect(
            "Filter by technology or skill:",
            options=all_extracted_skills,
            placeholder="All skills (e.g. SQL, Python, Power BI)...",
            help="Filter jobs that require chosen technologies."
        )
    with col_s2:
        search_filter = st.text_input("Search title, company, or text:", placeholder="e.g. Analyst, Remote, Equifax...")

    # Optional skill matching toggle if multiple skills chosen
    require_all_skills = False
    if len(selected_skills) > 1:
        match_mode = st.segmented_control(
            "Skill match mode:",
            options=["Match any selected skill", "Match all selected skills"],
            default="Match any selected skill",
            key="skill_match_mode"
        )
        require_all_skills = (match_mode == "Match all selected skills")

    # Apply all active filters to jobs list
    filtered_jobs = jobs
    if selected_run_id:
        filtered_jobs = [j for j in filtered_jobs if getattr(j, "search_run_id", None) == selected_run_id]

    # 1. Experience Level Filter
    if selected_exps:
        sel_exps_lower = {e.lower() for e in selected_exps}
        filtered_jobs = [j for j in filtered_jobs if j.experience_level.value.lower() in sel_exps_lower]

    # 2. Country Filter
    if selected_countries:
        sel_countries_lower = {c.lower() for c in selected_countries}
        filtered_jobs = [
            j for j in filtered_jobs
            if (j.country and j.country.lower() in sel_countries_lower)
            or any(c in (j.location or "").lower() for c in sel_countries_lower)
        ]

    # 3. Skills Filter
    if selected_skills:
        sel_skills_set = set(selected_skills)
        if require_all_skills:
            filtered_jobs = [
                j for j in filtered_jobs
                if sel_skills_set.issubset({s.canonical_name for s in j.extracted_skills})
            ]
        else:
            filtered_jobs = [
                j for j in filtered_jobs
                if any(s.canonical_name in sel_skills_set for s in j.extracted_skills)
            ]

    # 4. Search Filter
    if search_filter:
        sf = search_filter.strip().lower()
        filtered_jobs = [
            j for j in filtered_jobs
            if sf in j.title.lower()
            or sf in j.company.lower()
            or any(sf in s.canonical_name.lower() for s in j.extracted_skills)
            or sf in (j.location or "").lower()
            or sf in (j.country or "").lower()
        ]

    st.caption(f"Showing **{len(filtered_jobs)}** postings (filtered from {len(jobs)} total in project)")

    if not filtered_jobs:
        st.warning("No postings match the selected filter combination. Try clearing some selections.")
    else:
        jobs_df = MetricsEngine.to_jobs_dataframe(filtered_jobs)
        col_cfg = {
            "Apply URL": st.column_config.LinkColumn(
                "Apply Link",
                help="Direct company application or job posting portal",
                max_chars=120,
                display_text="Apply now"
            ),
            "Salary (USD/yr)": st.column_config.NumberColumn(
                "Salary (USD/yr)",
                help="Normalized annual compensation converted to USD",
                format="$%d"
            )
        }
        display_cols = ["Job Title", "Company", "Location", "Country", "Workplace", "Experience", "Salary", "Salary (USD/yr)", "Extracted Skills", "Apply URL"]
        valid_cols = [c for c in display_cols if c in jobs_df.columns]
        st.dataframe(
            jobs_df[valid_cols],
            column_config=col_cfg,
            width="stretch",
            hide_index=True
        )

    # Expandable details cards
    st.subheader("Detailed section and requirement extraction", icon=":material/article:")
    st.caption(
        "When StackCheck collects postings, its language processor separates candidate requirements "
        "from everyday tasks and applies contextual weights (such as 1.8x for primary qualifications). "
        "Open any card below to review extracted requirements and employer expectations."
    )

    col_sort1, col_sort2 = st.columns([1.6, 1.4])
    with col_sort1:
        sort_order = st.selectbox(
            "Sort cards by:",
            options=["Recent scraped order", "Highest salary first", "Most tech skills demanded", "Company name (A-Z)"],
            index=0
        )
    with col_sort2:
        card_limit_choice = st.selectbox(
            "Display cards count:",
            options=["Top 10 postings", "Top 25 postings", "Top 50 postings", "All matching postings"],
            index=0
        )

    # Apply sorting using canonical JobPost.salary_usd_estimate property
    cards_to_show = list(filtered_jobs)
    if sort_order == "Highest salary first":
        cards_to_show.sort(key=lambda j: j.salary_usd_estimate, reverse=True)
    elif sort_order == "Most tech skills demanded":
        cards_to_show.sort(key=lambda j: len(j.extracted_skills), reverse=True)
    elif sort_order == "Company name (A-Z)":
        cards_to_show.sort(key=lambda j: j.company.lower() if j.company else "")

    # Apply card count limit
    count_map = {"Top 10 postings": 10, "Top 25 postings": 25, "Top 50 postings": 50, "All matching postings": len(cards_to_show)}
    limit_n = count_map.get(card_limit_choice, 10)
    visible_cards = cards_to_show[:limit_n]

    st.caption(f"Displaying **{len(visible_cards)}** of **{len(cards_to_show)}** filtered postings:")

    for idx, job in enumerate(visible_cards):
        if job.salary and job.salary.formatted != "Not specified":
            usd_equiv = job.salary_usd_estimate
            if (job.salary.currency or "USD").upper() != "USD" and usd_equiv > 0:
                sal_display = f"{job.salary.formatted} (approx. ${usd_equiv:,.0f} USD/yr)"
            else:
                sal_display = job.salary.formatted
            sal_tag = f" • {sal_display}"
        else:
            sal_display = "Not listed"
            sal_tag = ""

        skills_count = len(job.extracted_skills)
        with st.expander(f"{job.title} | {job.company} ({job.location}){sal_tag} [{skills_count} skills]", icon=":material/description:"):
            col_d1, col_d2 = st.columns([1, 1])
            with col_d1:
                st.write(f"**Workplace:** {job.workplace_type.value.capitalize()} | **Experience:** {job.experience_level.value.capitalize()}")
                st.write(f"**Salary:** {sal_display}")
                target_link = job.link or job.apply_url or job.url
                if target_link and target_link.startswith("http"):
                    st.markdown(f"**Direct application:** [Open official careers portal]({target_link})")
                else:
                    st.caption("Apply link not provided in posting")
            with col_d2:
                skills_tags = " • ".join([f"`{s.canonical_name} ({s.priority_weight}x)`" for s in job.extracted_skills])
                st.markdown(f"**Extracted skills and weights:**\n{skills_tags}")

            if job.requirements_bullets:
                st.markdown("**Core requirements extracted:**")
                for b in job.requirements_bullets[:5]:
                    st.markdown(f"- {b}")

            if job.task_bullets:
                st.markdown("**Day-to-day responsibilities extracted:**")
                for b in job.task_bullets[:4]:
                    st.markdown(f"- {b}")

    # Data Exporters
    if jobs:
        st.subheader(f"Export dataset ({active_project.name})", icon=":material/download:")
        col_e1, col_e2, col_e3 = st.columns(3)
        safe_proj_name = "".join(c if c.isalnum() else "_" for c in active_project.name).lower()
        json_data = json.dumps(stats.model_dump(), indent=2, default=str)
        csv_data = MetricsEngine.to_jobs_dataframe(filtered_jobs).to_csv(index=False)
        md_path = ReportExporter.export_markdown(stats, filename=f"stackcheck_{safe_proj_name}_brief.md")
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        with col_e1:
            st.download_button(
                "Download JSON analytics",
                icon=":material/data_object:",
                data=json_data,
                file_name=f"stackcheck_{safe_proj_name}_analytics.json",
                mime="application/json",
                width="stretch"
            )
        with col_e2:
            st.download_button(
                f"Download CSV ({len(filtered_jobs)} postings)",
                icon=":material/table_chart:",
                data=csv_data,
                file_name=f"stackcheck_{safe_proj_name}_jobs.csv",
                mime="text/csv",
                width="stretch"
            )
        with col_e3:
            st.download_button(
                "Download Markdown brief",
                icon=":material/description:",
                data=md_content,
                file_name=f"stackcheck_{safe_proj_name}_brief.md",
                mime="text/markdown",
                width="stretch"
            )
