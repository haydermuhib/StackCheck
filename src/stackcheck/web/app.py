"""
Streamlit Web Dashboard for StackCheck.
Unified Tech Stack Intelligence Engine & Data Analytics Interface.
"""

import os
import sys
import signal
import time
import json
from pathlib import Path
import streamlit as st
import pandas as pd

from stackcheck import __version__
from stackcheck.updater import UpdateChecker
from stackcheck.launcher import stop_running_instance, get_running_instance
from stackcheck.models import SearchQuery, WorkplaceType, ExperienceLevel, Region, Project
from stackcheck.client.hiringcafe import HiringCafeClient
from stackcheck.client.normalizer import SUGGESTED_ROLES, SUGGESTED_LOCATIONS, JobNormalizer
from stackcheck.analyzer.metrics import MetricsEngine
from stackcheck.storage.repository import JobRepository
from stackcheck.storage.exporters import ReportExporter
from stackcheck.web.charts import (
    plot_top_skills,
    plot_co_occurrence_heatmap,
    plot_salary_by_tech,
    plot_distributions,
    plot_category_breakdown,
    plot_salary_by_country_scatter,
    plot_top_hiring_companies,
    plot_experience_skill_matrix,
    plot_stack_density_distribution
)


def get_assets_dir() -> Path:
    """Resolve the assets directory reliably across local dev, installed packages, user workspace, and PyInstaller bundles."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        meipass_assets = Path(sys._MEIPASS) / "assets"
        if meipass_assets.exists():
            return meipass_assets

    from stackcheck.launcher import STACKCHECK_DIR
    user_assets = STACKCHECK_DIR / "assets"
    if user_assets.exists() and (user_assets / "logo.png").exists():
        return user_assets

    repo_assets = Path(__file__).resolve().parent.parent.parent.parent / "assets"
    if repo_assets.exists():
        return repo_assets

    pkg_assets = Path(__file__).resolve().parent.parent / "assets"
    if pkg_assets.exists():
        return pkg_assets

    cwd_assets = Path.cwd() / "assets"
    if cwd_assets.exists():
        return cwd_assets

    return repo_assets


def init_session():
    """Initialize repository, projects, and cached job state."""
    if "flash_msg" not in st.session_state:
        st.session_state.flash_msg = None
    if "repo" not in st.session_state:
        st.session_state.repo = JobRepository()
    if "client" not in st.session_state:
        st.session_state.client = HiringCafeClient()
    
    projects = st.session_state.repo.get_projects()
    if not projects:
        default_proj = st.session_state.repo.create_project("Default Workspace", "General tech stack research and job intelligence.")
        projects = [default_proj]
        
    if "active_project_id" not in st.session_state:
        st.session_state.active_project_id = projects[0].id
        
    # Guard against deleted project id
    proj_ids = [p.id for p in projects]
    if st.session_state.active_project_id not in proj_ids:
        st.session_state.active_project_id = proj_ids[0]

    if "jobs" not in st.session_state:
        stored = st.session_state.repo.get_all_jobs(project_id=st.session_state.active_project_id)
        st.session_state.jobs = stored if stored else []
    if "stats" not in st.session_state:
        active_proj = st.session_state.repo.get_project(st.session_state.active_project_id)
        proj_title = active_proj.name if active_proj else "Active Project"
        if st.session_state.jobs:
            st.session_state.stats = MetricsEngine.aggregate(st.session_state.jobs, query_keywords=proj_title)
        else:
            st.session_state.stats = MetricsEngine.aggregate([], query_keywords=proj_title)


def main():
    assets_dir = get_assets_dir()
    icon_path = assets_dir / "icon.png"
    logo_path = assets_dir / "logo.png"

    st.set_page_config(
        page_title="StackCheck | Tech Market Intelligence",
        page_icon=str(icon_path) if icon_path.exists() else "📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    init_session()
    active_project = st.session_state.repo.get_project(st.session_state.active_project_id) or Project(id="default", name="Default Workspace")

    # Custom styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-header">📊 StackCheck — Tech Stack Market Intelligence</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sub-header">📁 Active Project Workspace: <b>{active_project.name}</b> • {len(st.session_state.jobs)} jobs collected across {active_project.total_searches} search runs</div>',
        unsafe_allow_html=True
    )

    # ----------------- SIDEBAR CONTROLS -----------------
    with st.sidebar:
        if logo_path.exists():
            st.image(str(logo_path), width="stretch")
            st.markdown("<div style='margin-bottom: 0.8rem;'></div>", unsafe_allow_html=True)

        if st.session_state.get("flash_msg"):
            f_type, f_txt = st.session_state.pop("flash_msg")
            if f_type == "success":
                st.success(f_txt)
            elif f_type == "error":
                st.error(f_txt)
            elif f_type == "warning":
                st.warning(f_txt)
            elif f_type == "info":
                st.info(f_txt)

        # 1. Project Selector & Management
        st.header("📁 Research Workspace")
        projects = st.session_state.repo.get_projects()
        proj_map = {f"📁 {p.name} ({p.total_jobs} jobs)": p.id for p in projects}
        proj_labels = list(proj_map.keys())
        
        current_idx = 0
        for i, p in enumerate(projects):
            if p.id == st.session_state.active_project_id:
                current_idx = i
                break
                
        selected_proj_label = st.selectbox("Select Project Workspace:", proj_labels, index=current_idx)
        selected_proj_id = proj_map[selected_proj_label]
        
        if selected_proj_id != st.session_state.active_project_id:
            st.session_state.active_project_id = selected_proj_id
            st.session_state.jobs = st.session_state.repo.get_all_jobs(project_id=selected_proj_id)
            switched_proj = st.session_state.repo.get_project(selected_proj_id)
            p_name = switched_proj.name if switched_proj else "Project"
            st.session_state.stats = MetricsEngine.aggregate(st.session_state.jobs, query_keywords=p_name)
            st.rerun()

        # Display saved criteria for the currently selected project
        if active_project.last_keywords:
            with st.container():
                st.markdown(
                    f"""
                    <div style='background: #f8fafc; border: 1px solid #cbd5e1; border-left: 4px solid #3b82f6; padding: 10px 12px; border-radius: 6px; margin: 10px 0;'>
                        <div style='font-size: 0.8rem; font-weight: 700; color: #1e293b; margin-bottom: 4px;'>📌 SAVED PROJECT CRITERIA</div>
                        <div style='font-size: 0.78rem; color: #334155; margin-bottom: 2px;'><b>Query:</b> <code style='color: #0284c7;'>{active_project.last_keywords}</code></div>
                        <div style='font-size: 0.78rem; color: #334155; margin-bottom: 2px;'><b>Location:</b> {active_project.last_location or "Global / Any"}</div>
                        <div style='font-size: 0.78rem; color: #334155;'><b>Workplace:</b> {active_project.last_workplace or "Any"} | <b>Level:</b> {active_project.last_experience or "All"}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if st.button("🔄 Scrape More / Re-run Query", width="stretch", key="btn_rerun_saved_query"):
                    with st.spinner(f"Scraping fresh jobs for '{active_project.last_keywords}'..."):
                        wp_enum = WorkplaceType(active_project.last_workplace) if active_project.last_workplace and active_project.last_workplace != "any" else None
                        exp_enum = ExperienceLevel(active_project.last_experience) if active_project.last_experience and active_project.last_experience != "any" else None
                        q = SearchQuery(
                            keywords=active_project.last_keywords or "Data Analyst",
                            location=active_project.last_location or "",
                            workplace_type=wp_enum,
                            experience_level=exp_enum,
                            limit=active_project.last_limit or 50,
                            project_id=active_project.id
                        )
                        fresh_jobs = st.session_state.client.search_jobs(q)
                        if fresh_jobs:
                            run_id = st.session_state.repo.save_search_run(q, total_found=len(fresh_jobs), project_id=active_project.id)
                            res = st.session_state.repo.save_jobs(fresh_jobs, search_run_id=run_id, project_id=active_project.id)
                            st.session_state.jobs = st.session_state.repo.get_all_jobs(project_id=active_project.id)
                            st.session_state.stats = MetricsEngine.aggregate(st.session_state.jobs, query_keywords=active_project.last_keywords or active_project.name or "General")
                            st.session_state.flash_msg = ("success", f"✔ Scraped {len(fresh_jobs)} postings: {res['new_count']} new added ({res['updated_count']} duplicates updated).")
                            st.rerun()
                        else:
                            st.warning("No new postings found on HiringCafe for this query.")

        # Project management expander
        with st.expander("➕ Create or Manage Projects"):
            new_pname = st.text_input("New Project Name:", placeholder="e.g. Data Analyst Global 2026")
            new_pdesc = st.text_input("Description (optional):", placeholder="e.g. Worldwide analyst tech stack study")
            if st.button("✨ Create Project", width="stretch"):
                if new_pname.strip():
                    new_p = st.session_state.repo.create_project(new_pname.strip(), new_pdesc.strip())
                    st.session_state.active_project_id = new_p.id
                    st.session_state.jobs = []
                    st.session_state.stats = MetricsEngine.aggregate([], query_keywords=new_p.name)
                    st.session_state.flash_msg = ("success", f"Project '{new_p.name}' created!")
                    st.rerun()
                else:
                    st.error("Please enter a project name.")

            st.markdown("---")
            if active_project.id != "default":
                if st.button(f"🗑 Delete '{active_project.name}'", type="secondary", width="stretch"):
                    st.session_state.repo.delete_project(active_project.id)
                    st.session_state.active_project_id = "default"
                    st.session_state.jobs = st.session_state.repo.get_all_jobs(project_id="default")
                    st.session_state.stats = MetricsEngine.aggregate(st.session_state.jobs, query_keywords="Default Workspace")
                    st.session_state.flash_msg = ("info", f"Project '{active_project.name}' deleted.")
                    st.rerun()
            else:
                st.caption("ℹ️ The Default Workspace cannot be deleted.")

        st.markdown("---")
        st.header("🔍 Scraper & Pipeline Filters")

        # Preset Role Pickers
        role_choices = ["(Custom Keywords)"] + SUGGESTED_ROLES
        selected_role = st.selectbox("⚡ Role Quick-Picks:", role_choices, index=1)
        
        default_kw = selected_role if selected_role != "(Custom Keywords)" else "Data Analyst"
        keywords_input = st.text_input("Role / Search Keywords:", value=default_kw)

        # Country / Location Presets
        loc_names = [name for name, _ in SUGGESTED_LOCATIONS]
        loc_map = {name: val for name, val in SUGGESTED_LOCATIONS}
        selected_loc_name = st.selectbox("🌍 Country / Region Quick-Picks:", loc_names, index=0)
        
        preset_loc_val = loc_map[selected_loc_name]
        location_input = st.text_input("Location / Country (Auto-Normalized):", value=preset_loc_val, placeholder="e.g. Worldwide, Pakistan, USA, UK, Germany, Remote")
        st.caption("💡 Select 'Global / Any Location' or enter countries. Multi-page pagination auto-scrapes all pages.")

        # Workplace Mode
        workplace_choice = st.selectbox(
            "Workplace Mode:",
            options=["Any Workplace", "Remote Only", "Hybrid", "Onsite / Office"],
            index=0
        )
        workplace_map = {
            "Any Workplace": None,
            "Remote Only": WorkplaceType.REMOTE,
            "Hybrid": WorkplaceType.HYBRID,
            "Onsite / Office": WorkplaceType.ONSITE
        }
        selected_workplace = workplace_map[workplace_choice]

        # Experience Level
        exp_choice = st.selectbox(
            "Experience Level:",
            options=["All Levels", "Entry Level / Junior", "Mid Level", "Senior / Staff", "Lead / Principal"],
            index=0
        )
        exp_map = {
            "All Levels": None,
            "Entry Level / Junior": ExperienceLevel.ENTRY,
            "Mid Level": ExperienceLevel.MID,
            "Senior / Staff": ExperienceLevel.SENIOR,
            "Lead / Principal": ExperienceLevel.LEAD
        }
        selected_exp = exp_map[exp_choice]

        # Limit (increased up to 500)
        limit = st.slider("Job Postings Limit (Pagination Depth):", min_value=10, max_value=500, value=50, step=10)

        # Trigger Pipeline
        run_btn = st.button("🚀 Scrape & Add to Project", type="primary", width="stretch")

        if run_btn:
            with st.spinner(f"Ingesting live postings from HiringCafe into '{active_project.name}'..."):
                prog_bar = st.progress(10)
                status_text = st.empty()

                def progress_cb(curr, total, msg):
                    pct = int((curr / max(total, 1)) * 90)
                    prog_bar.progress(pct)
                    status_text.text(msg)

                canonical_loc = JobNormalizer.normalize_location_query(location_input)
                query = SearchQuery(
                    keywords=keywords_input,
                    location=canonical_loc,
                    workplace_type=selected_workplace,
                    experience_level=selected_exp,
                    limit=limit,
                    project_id=st.session_state.active_project_id
                )

                new_jobs = st.session_state.client.search_jobs(query, progress_callback=progress_cb)

                if new_jobs:
                    prog_bar.progress(100)
                    status_text.text("Pipeline Complete!")
                    run_id = st.session_state.repo.save_search_run(query, len(new_jobs), project_id=st.session_state.active_project_id)
                    save_res = st.session_state.repo.save_jobs(new_jobs, search_run_id=run_id, project_id=st.session_state.active_project_id)
                    st.session_state.jobs = st.session_state.repo.get_all_jobs(project_id=st.session_state.active_project_id)
                    st.session_state.stats = MetricsEngine.aggregate(st.session_state.jobs, query_keywords=active_project.name)

                    new_cnt = save_res.get("new_count", len(new_jobs)) if isinstance(save_res, dict) else len(new_jobs)
                    upd_cnt = save_res.get("updated_count", 0) if isinstance(save_res, dict) else 0
                    if upd_cnt > 0:
                        st.session_state.flash_msg = ("success", f"✔ Ingested {len(new_jobs)} postings into '{active_project.name}': **{new_cnt} newly added**, **{upd_cnt} duplicate/existing postings refreshed**! Total unique jobs in project: **{len(st.session_state.jobs)}**")
                    else:
                        st.session_state.flash_msg = ("success", f"✔ Successfully added **{new_cnt} new postings** into '{active_project.name}'! Total unique jobs in project: **{len(st.session_state.jobs)}**")
                    st.rerun()
                else:
                    prog_bar.empty()
                    err = getattr(st.session_state.client, "last_error", None)
                    if err:
                        status_text.empty()
                        st.error(f"❌ Scraping Error: {err}")
                    else:
                        status_text.text("No results returned.")
                        st.warning("⚠️ No postings found for this exact query. Try broadening the keywords or location.")

        st.markdown("---")
        st.markdown(f"**Project Summary (`{active_project.name}`):**")
        st.write(f"📁 Stored Postings in Project: **{len(st.session_state.jobs)}**")
        if st.button("🗑 Clear Jobs in this Project", width="stretch"):
            st.session_state.repo.clear_project_jobs(st.session_state.active_project_id)
            st.session_state.jobs = []
            st.session_state.stats = MetricsEngine.aggregate([], query_keywords="Cleared")
            st.session_state.flash_msg = ("info", f"Cleared all jobs in '{active_project.name}'.")
            st.rerun()

        # ----------------- SYSTEM & SERVER MANAGEMENT -----------------
        st.markdown("---")
        with st.expander("⚙️ Server & Updates", expanded=False):
            info = get_running_instance()
            if info:
                st.caption(f"🟢 **Status:** Active on port `{info.get('port', 8501)}` (PID `{info.get('pid')}`)")
            else:
                st.caption("🟢 **Status:** Active (In-Process)")

            # Clean Server Stop / Shutdown Button
            if st.button("🛑 Stop Server & Release Port", type="secondary", width="stretch"):
                st.warning("Shutting down StackCheck server...")
                time.sleep(0.4)
                stop_running_instance()
                try:
                    os.kill(os.getpid(), signal.SIGTERM)
                except OSError:
                    pass
                st.info("StackCheck server has stopped. You can safely close this browser tab.")
                st.stop()

            st.markdown("---")
            st.caption(f"**Installed Version:** `v{__version__}`")
            if "update_info" not in st.session_state:
                st.session_state.update_info = None

            if st.button("🔄 Check for Updates", width="stretch"):
                with st.spinner("Checking GitHub for newer releases..."):
                    res = UpdateChecker.check_for_update()
                    st.session_state.update_info = res
                    if res and res.get("has_update"):
                        st.session_state.update_msg = f"✨ New version **v{res['latest_version']}** available!"
                    else:
                        st.session_state.update_msg = f"✔ StackCheck is up to date (v{__version__})."

            if st.session_state.get("update_msg"):
                st.info(st.session_state.update_msg)

            up_info = st.session_state.get("update_info")
            if up_info and up_info.get("has_update"):
                target_asset = up_info.get("target_asset")
                if target_asset and target_asset.get("download_url"):
                    if st.button(f"⬇️ Download & Update to v{up_info['latest_version']}", type="primary", width="stretch"):
                        prog_bar = st.progress(0)
                        status_lbl = st.empty()
                        status_lbl.text(f"Downloading {target_asset['name']}...")

                        target_path = UpdateChecker.get_install_target_path()
                        downloaded_bytes = [0]

                        def on_progress(chunk_len, total_len):
                            downloaded_bytes[0] += chunk_len
                            if total_len > 0:
                                pct = min(100, int((downloaded_bytes[0] / total_len) * 100))
                                prog_bar.progress(pct)
                                mb_done = downloaded_bytes[0] / (1024 * 1024)
                                mb_total = total_len / (1024 * 1024)
                                status_lbl.text(f"Downloading: {mb_done:.1f} MB / {mb_total:.1f} MB ({pct}%)")

                        try:
                            UpdateChecker.download_asset(
                                download_url=target_asset["download_url"],
                                dest_path=target_path,
                                progress_callback=on_progress
                            )
                            prog_bar.progress(100)
                            status_lbl.empty()
                            st.success(f"🎉 Updated to v{up_info['latest_version']}! Please restart StackCheck to apply.")
                        except Exception as e:
                            st.error(f"Update failed: {e}")

    # ----------------- MAIN TABS -----------------
    tab_dash, tab_analytics, tab_jobs = st.tabs([
        "📊 Executive Market Dashboard",
        "📈 Deep Statistical Analytics",
        "💼 Interactive Job Explorer"
    ])

    jobs = st.session_state.jobs
    stats = st.session_state.stats

    # ----------------- TAB 1: EXECUTIVE DASHBOARD -----------------
    with tab_dash:
        if not jobs:
            st.info("👋 Welcome to StackCheck! Use the left sidebar to select a role or country and click **'Scrape & Run Market Pipeline'** to analyze live job market data.")
        else:
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
            salary_str = f"${avg_salary_val:,.0f} / yr" if avg_salary_val > 0 else "Disclosed in Postings"

            with kpi1:
                st.metric("Total Jobs Analyzed", f"{stats.total_jobs}")
            with kpi2:
                st.metric("Unique Companies", f"{stats.unique_companies}")
            with kpi3:
                st.metric("Top Demanded Skill", f"{top_skill_name}", delta=f"{top_skill_pct} of jobs")
            with kpi4:
                st.metric("Avg Benchmark Salary", salary_str)

            st.markdown("---")

            col_chart, col_side = st.columns([1.6, 1])

            with col_chart:
                st.subheader("🏆 Top In-Demand Tech Skills")
                weight_toggle = st.checkbox("Apply Section-Weighted Priority Multipliers (1.8x Requirements vs 1.0x Context)", value=False)
                fig_top = plot_top_skills(stats, top_n=14, use_weighted=weight_toggle)
                if fig_top:
                    st.pyplot(fig_top, width="stretch")

            with col_side:
                st.subheader("📦 Domain Category Breakdown")
                fig_cat = plot_category_breakdown(stats)
                if fig_cat:
                    st.pyplot(fig_cat, width="stretch")
                else:
                    st.write("No category data available.")

    # ----------------- TAB 2: DEEP STATISTICAL ANALYTICS -----------------
    with tab_analytics:
        if not jobs:
            st.info("Run a search in the sidebar to populate deep statistical visualizations.")
        else:
            # High-Level Market Analytics KPIs
            mkpi1, mkpi2, mkpi3, mkpi4 = st.columns(4)
            with mkpi1:
                st.metric("Salary Disclosure Rate", f"{stats.salary_transparency_pct:.1f}%", help="Percentage of postings with explicit salary information")
            with mkpi2:
                avg_b = stats.stack_density_stats.get("avg_skills_per_job", 0.0) if stats.stack_density_stats else 0.0
                st.metric("Avg Stack Breadth", f"{avg_b} skills / job", help="Average number of tech skills requested per job post")
            with mkpi3:
                # Calculate remote premium if available
                rem_med = stats.workplace_salary_stats.get("remote", {}).get("median") if stats.workplace_salary_stats else None
                ons_med = stats.workplace_salary_stats.get("onsite", {}).get("median") if stats.workplace_salary_stats else None
                if rem_med and ons_med and ons_med > 0:
                    diff_pct = ((rem_med - ons_med) / ons_med) * 100
                    st.metric("Remote Pay Premium", f"${rem_med:,.0f}/yr", delta=f"{diff_pct:+.1f}% vs Onsite")
                elif rem_med:
                    st.metric("Remote Median Salary", f"${rem_med:,.0f}/yr")
                else:
                    st.metric("Remote Pay Premium", "N/A", help="Insufficient remote/onsite salary samples")
            with mkpi4:
                max_b = stats.stack_density_stats.get("max_skills", 0) if stats.stack_density_stats else 0
                st.metric("Max Stack Density", f"{max_b} skills", help="Highest number of skills required in a single job posting")

            st.markdown("---")

            # 1. Geographic Compensation Scatter / Strip Plot
            st.subheader("🗺️ Geographic Compensation Distribution")
            st.caption("Categorical strip plot with horizontal jitter showing individual job posting salaries across countries, with median compensation benchmarks.")
            col_opt1, col_opt2 = st.columns([1, 3])
            with col_opt1:
                color_option = st.radio(
                    "Color Markers By:",
                    options=["Seniority Level", "Workplace Mode"],
                    horizontal=True,
                    key="geo_scatter_color_by"
                )
                color_key = "experience" if "Seniority" in color_option else "workplace"

            country_fig = plot_salary_by_country_scatter(stats.country_salary_data, color_by=color_key)
            if country_fig:
                st.pyplot(country_fig, width="stretch")
            else:
                st.info("Insufficient salary and location samples in the current dataset to render country compensation scatter (minimum 2 samples required).")

            st.markdown("---")

            # 2. Tech Stack Synergies & Co-Occurrence
            st.subheader("🔗 Tech Stack Synergies & Co-Occurrence Correlation")
            st.caption("Visualizes how often technologies co-occur in the same job requirements (e.g. Python + SQL, Power BI + DAX).")
            heatmap_fig = plot_co_occurrence_heatmap(stats, top_n=10)
            if heatmap_fig:
                st.pyplot(heatmap_fig, width="stretch")

            st.markdown("---")

            # 3. Salary Benchmarks & Workplace/Experience Distributions
            col_sal, col_dist = st.columns([1.2, 1])

            with col_sal:
                st.subheader("💵 Salary Benchmarks by Technology")
                sal_fig = plot_salary_by_tech(stats)
                if sal_fig:
                    st.pyplot(sal_fig, width="stretch")
                else:
                    st.info("Insufficient structured salary samples in current query to render compensation error bars.")

            with col_dist:
                st.subheader("🌍 Workplace & Experience Distribution")
                fig_wp, fig_exp = plot_distributions(stats)
                if fig_wp:
                    st.pyplot(fig_wp, width="stretch")
                if fig_exp:
                    st.pyplot(fig_exp, width="stretch")

            st.markdown("---")

            # 4. Seniority & Experience Intelligence
            st.subheader("🎓 Seniority & Experience Intelligence")
            st.caption("Top demanded technologies and salary progression across career seniority tiers.")
            col_exp_chart, col_exp_bench = st.columns([1.5, 1])

            with col_exp_chart:
                exp_fig = plot_experience_skill_matrix(stats.experience_skills_breakdown)
                if exp_fig:
                    st.pyplot(exp_fig, width="stretch")
                else:
                    st.info("No experience-segmented skill distribution data available.")

            with col_exp_bench:
                st.markdown("##### 📊 Compensation by Experience Tier")
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

            st.markdown("---")

            # 5. Employer Landscape & Tech Stack Density
            st.subheader("🏢 Employer Landscape & Tech Stack Density")
            col_comp, col_dens = st.columns([1.2, 1])

            with col_comp:
                st.caption("Top companies actively hiring for these skillsets and their primary tech stacks.")
                comp_fig = plot_top_hiring_companies(stats.top_hiring_companies, top_n=10)
                if comp_fig:
                    st.pyplot(comp_fig, width="stretch")
                else:
                    st.info("No employer hiring data available.")

            with col_dens:
                st.caption("Distribution of how many distinct technologies/tools are demanded per job posting.")
                dens_fig = plot_stack_density_distribution(stats.stack_density_stats)
                if dens_fig:
                    st.pyplot(dens_fig, width="stretch")
                else:
                    st.info("No stack density distribution available.")

            # 6. Geographic Table
            if stats.geo_breakdown:
                st.markdown("---")
                st.subheader("🌐 Regional Tech Partitioning")
                geo_rows = []
                for reg_name, g_info in stats.geo_breakdown.items():
                    top_skills_str = ", ".join([f"{s['skill']} ({s['percentage']}%)" for s in g_info.top_skills[:4]])
                    geo_rows.append({
                        "Region": reg_name,
                        "Postings Count": g_info.total_jobs,
                        "Top Demanded Technologies": top_skills_str
                    })
                st.dataframe(pd.DataFrame(geo_rows), width="stretch", hide_index=True)

    # ----------------- TAB 3: JOBS EXPLORER -----------------
    with tab_jobs:
        if not jobs:
            st.info("No job postings available to explore. Run a search to populate.")
        else:
            st.subheader(f"💼 Extracted Postings Directory ({len(jobs)} total in {active_project.name})")
            
            # Interactive Multi-Select Filter Controls
            col_f0, col_f1, col_f2 = st.columns([1.2, 1.4, 1.4])
            with col_f0:
                search_runs = st.session_state.repo.get_search_runs(project_id=st.session_state.active_project_id)
                run_options = ["All Searches in Project"] + [f"🔍 {r['keywords']} ({r['total_found']} jobs) • {r['created_at'][:16]}" for r in search_runs]
                run_map = {f"🔍 {r['keywords']} ({r['total_found']} jobs) • {r['created_at'][:16]}": r["id"] for r in search_runs}
                selected_run_label = st.selectbox("Scrape Batch / Run:", run_options)
                selected_run_id = run_map.get(selected_run_label)

            with col_f1:
                # Experience Level Multi-Select (e.g. select Entry only, or Entry + Mid)
                standard_exps = ["Entry", "Mid", "Senior", "Lead", "Executive", "Any"]
                available_exps = [e for e in standard_exps if any(j.experience_level.value.capitalize() == e for j in jobs)]
                if not available_exps:
                    available_exps = sorted(list({j.experience_level.value.capitalize() for j in jobs if j.experience_level}))
                selected_exps = st.multiselect(
                    "Filter by Experience Level(s):",
                    options=available_exps,
                    placeholder="All Levels (e.g. Entry, Mid)...",
                    help="Select one or multiple experience levels, or leave empty for all."
                )

            with col_f2:
                # Country Multi-Select
                available_countries = sorted(list({j.country for j in jobs if j.country and j.country != "Unknown"}))
                selected_countries = st.multiselect(
                    "Filter by Country:",
                    options=available_countries,
                    placeholder="All Countries...",
                    help="Select one or multiple countries, or leave empty for all."
                )

            col_s1, col_s2 = st.columns([1.8, 1.2])
            with col_s1:
                # Skills Multi-Select
                all_extracted_skills = sorted(list({s.canonical_name for j in jobs for s in j.extracted_skills}))
                selected_skills = st.multiselect(
                    "Filter by Technology / Skill(s):",
                    options=all_extracted_skills,
                    placeholder="All Skills (e.g. SQL, Python, Power BI)...",
                    help="Filter jobs that require chosen technologies."
                )
            with col_s2:
                search_filter = st.text_input("Search Title / Company / Snippet:", placeholder="e.g. Analyst, Remote, Equifax...")

            # Optional skill matching toggle if multiple skills chosen
            require_all_skills = False
            if len(selected_skills) > 1:
                match_mode = st.radio(
                    "Skill Match Mode:",
                    options=["Match ANY selected skill (OR)", "Match ALL selected skills (AND)"],
                    horizontal=True
                )
                require_all_skills = (match_mode == "Match ALL selected skills (AND)")

            # Apply all active filters to jobs list
            filtered_jobs = jobs
            if selected_run_id:
                filtered_jobs = [j for j in filtered_jobs if getattr(j, "search_run_id", None) == selected_run_id]

            # 1. Experience Level Filter (Multi-select)
            if selected_exps:
                sel_exps_lower = {e.lower() for e in selected_exps}
                filtered_jobs = [j for j in filtered_jobs if j.experience_level.value.lower() in sel_exps_lower]

            # 2. Country Filter (Multi-select)
            if selected_countries:
                sel_countries_lower = {c.lower() for c in selected_countries}
                filtered_jobs = [
                    j for j in filtered_jobs
                    if (j.country and j.country.lower() in sel_countries_lower)
                    or any(c in (j.location or "").lower() for c in sel_countries_lower)
                ]

            # 3. Skills Filter (Multi-select: OR vs AND)
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
                st.warning("⚠️ No postings match the selected filter combination. Try clearing some selections.")
            else:
                jobs_df = MetricsEngine.to_jobs_dataframe(filtered_jobs)
                col_cfg = {
                    "Apply URL": st.column_config.LinkColumn(
                        "Apply Link",
                        help="Direct company application or job posting portal",
                        max_chars=120,
                        display_text="🔗 Apply Now"
                    )
                }
                display_cols = ["Job Title", "Company", "Location", "Country", "Workplace", "Experience", "Salary", "Extracted Skills", "Apply URL"]
                valid_cols = [c for c in display_cols if c in jobs_df.columns]
                st.dataframe(
                    jobs_df[valid_cols],
                    column_config=col_cfg,
                    width="stretch",
                    hide_index=True
                )

            # Expandable details cards
            st.subheader("📑 Detailed Section & Requirement Extraction")
            for idx, job in enumerate(filtered_jobs[:10]):
                with st.expander(f"📍 {job.title} — {job.company} ({job.location})"):
                    col_d1, col_d2 = st.columns([1, 1])
                    with col_d1:
                        st.write(f"**Workplace:** {job.workplace_type.value.capitalize()} | **Experience:** {job.experience_level.value.capitalize()}")
                        st.write(f"**Salary:** {job.salary.formatted if job.salary else 'Not Listed'}")
                        target_link = job.link or job.apply_url or job.url
                        if target_link and target_link.startswith("http"):
                            st.markdown(f"**Direct Application:** [🔗 Open Official Careers / ATS Portal]({target_link})")
                        else:
                            st.caption("Apply link not provided in posting")
                    with col_d2:
                        skills_tags = " • ".join([f"`{s.canonical_name} ({s.priority_weight}x)`" for s in job.extracted_skills])
                        st.markdown(f"**Extracted Skills & Weights:**\n{skills_tags}")

                    if job.requirements_bullets:
                        st.markdown("**Core Requirements Extracted:**")
                        for b in job.requirements_bullets[:4]:
                            st.markdown(f"- {b}")

            # Data Exporters
            if jobs:
                st.markdown("---")
                st.subheader(f"💾 Active Data Exporters ({active_project.name})")
                col_e1, col_e2, col_e3 = st.columns(3)
                safe_proj_name = "".join(c if c.isalnum() else "_" for c in active_project.name).lower()
                json_data = json.dumps(stats.model_dump(), indent=2, default=str)
                csv_data = MetricsEngine.to_jobs_dataframe(filtered_jobs).to_csv(index=False)
                md_path = ReportExporter.export_markdown(stats, filename=f"stackcheck_{safe_proj_name}_brief.md")
                with open(md_path, "r", encoding="utf-8") as f:
                    md_content = f.read()

                with col_e1:
                    st.download_button(
                        "📄 Download JSON Analytics",
                        data=json_data,
                        file_name=f"stackcheck_{safe_proj_name}_analytics.json",
                        mime="application/json",
                        width="stretch"
                    )
                with col_e2:
                    st.download_button(
                        f"📊 Download CSV ({len(filtered_jobs)} Postings)",
                        data=csv_data,
                        file_name=f"stackcheck_{safe_proj_name}_jobs.csv",
                        mime="text/csv",
                        width="stretch"
                    )
                with col_e3:
                    st.download_button(
                        "📝 Download Markdown Brief",
                        data=md_content,
                        file_name=f"stackcheck_{safe_proj_name}_brief.md",
                        mime="text/markdown",
                        width="stretch"
                    )


if __name__ == "__main__":
    main()
