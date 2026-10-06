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
from stackcheck.analyzer.currency import currency_manager
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


# ----------------- CONFIRMATION MODAL DIALOGS -----------------
@st.dialog("Create new project", icon=":material/add_circle:")
def create_project_dialog():
    st.write("Enter details for the new research workspace.")
    new_pname = st.text_input("Project name:", placeholder="e.g. Data Analyst Global 2026", key="dlg_new_pname")
    new_pdesc = st.text_input("Description (optional):", placeholder="e.g. Worldwide analyst tech stack study", key="dlg_new_pdesc")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Create project", icon=":material/add:", type="primary", width="stretch", key="dlg_btn_confirm_create"):
            if new_pname.strip():
                new_p = st.session_state.repo.create_project(new_pname.strip(), new_pdesc.strip())
                st.session_state.active_project_id = new_p.id
                st.session_state.jobs = []
                st.session_state.stats = MetricsEngine.aggregate([], query_keywords=new_p.name)
                st.session_state.flash_msg = ("success", f"Project '{new_p.name}' created.")
                st.rerun()
            else:
                st.error("Please enter a project name.")
    with col2:
        if st.button("Cancel", width="stretch", key="dlg_btn_cancel_create"):
            st.rerun()


@st.dialog("Delete project workspace", icon=":material/delete:")
def delete_project_dialog(project_id: str, project_name: str):
    st.write(f"Are you sure you want to delete **{project_name}**?")
    st.caption("This will permanently remove all associated job postings and search records from this workspace. This action cannot be undone.")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Delete project", icon=":material/delete:", type="primary", width="stretch", key="dlg_btn_confirm_delete"):
            st.session_state.repo.delete_project(project_id)
            st.session_state.active_project_id = "default"
            st.session_state.jobs = st.session_state.repo.get_all_jobs(project_id="default")
            st.session_state.stats = MetricsEngine.aggregate(st.session_state.jobs, query_keywords="Default Workspace")
            st.session_state.flash_msg = ("info", f"Project '{project_name}' deleted.")
            st.rerun()
    with col2:
        if st.button("Cancel", width="stretch", key="dlg_btn_cancel_delete"):
            st.rerun()


@st.dialog("Clear all jobs in project", icon=":material/delete_sweep:")
def clear_jobs_dialog(project_id: str, project_name: str, job_count: int):
    st.write(f"Are you sure you want to clear all **{job_count}** jobs from **{project_name}**?")
    st.caption("Saved project search criteria will be preserved, but all collected postings will be cleared.")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Clear jobs", icon=":material/delete_sweep:", type="primary", width="stretch", key="dlg_btn_confirm_clear"):
            st.session_state.repo.clear_project_jobs(project_id)
            st.session_state.jobs = []
            st.session_state.stats = MetricsEngine.aggregate([], query_keywords="Cleared")
            st.session_state.flash_msg = ("info", f"Cleared all jobs in '{project_name}'.")
            st.rerun()
    with col2:
        if st.button("Cancel", width="stretch", key="dlg_btn_cancel_clear"):
            st.rerun()


def main():
    assets_dir = get_assets_dir()
    icon_path = assets_dir / "icon.png"
    logo_path = assets_dir / "logo.png"

    st.set_page_config(
        page_title="StackCheck | Tech Market Intelligence",
        page_icon=str(icon_path) if icon_path.exists() else ":material/analytics:",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    init_session()
    active_project = st.session_state.repo.get_project(st.session_state.active_project_id) or Project(id="default", name="Default Workspace")

    # Dark Theme Card Styling
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 0.2rem;
        letter-spacing: -0.02em;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #94a3b8;
        margin-bottom: 1.5rem;
    }
    .saved-criteria-card {
        background: #1e293b;
        border: 1px solid #334155;
        border-left: 4px solid #38bdf8;
        padding: 10px 14px;
        border-radius: 6px;
        margin: 10px 0;
    }
    .saved-criteria-title {
        font-size: 0.82rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 5px;
        letter-spacing: 0.04em;
    }
    .saved-criteria-item {
        font-size: 0.8rem;
        color: #cbd5e1;
        margin-bottom: 3px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-header">StackCheck: Tech Stack Market Intelligence</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sub-header">Active project workspace: <b>{active_project.name}</b> • {len(st.session_state.jobs)} jobs collected across {active_project.total_searches} search runs</div>',
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
        st.header("Research workspace", icon=":material/folder:")
        projects = st.session_state.repo.get_projects()
        proj_map = {f"{p.name} ({p.total_jobs} jobs)": p.id for p in projects}
        proj_labels = list(proj_map.keys())
        
        current_idx = 0
        for i, p in enumerate(projects):
            if p.id == st.session_state.active_project_id:
                current_idx = i
                break
                
        selected_proj_label = st.selectbox("Select project workspace:", proj_labels, index=current_idx)
        selected_proj_id = proj_map[selected_proj_label]
        
        if selected_proj_id != st.session_state.active_project_id:
            st.session_state.active_project_id = selected_proj_id
            st.session_state.jobs = st.session_state.repo.get_all_jobs(project_id=selected_proj_id)
            switched_proj = st.session_state.repo.get_project(selected_proj_id)
            p_name = switched_proj.name if switched_proj else "Project"
            st.session_state.stats = MetricsEngine.aggregate(st.session_state.jobs, query_keywords=p_name)
            st.rerun()

        # Workspace actions with confirmation modals
        col_proj_a, col_proj_b = st.columns([1, 1])
        with col_proj_a:
            if st.button("New project", icon=":material/add:", width="stretch", key="btn_open_new_proj_dlg"):
                create_project_dialog()
        with col_proj_b:
            if active_project.id != "default":
                if st.button("Delete project", icon=":material/delete:", width="stretch", key="btn_open_del_proj_dlg"):
                    delete_project_dialog(active_project.id, active_project.name)
            else:
                st.button("Default lock", icon=":material/lock:", disabled=True, width="stretch", help="The default workspace cannot be deleted.")

        # Display saved criteria for the currently selected project
        if active_project.last_keywords:
            with st.container():
                limit_disp = "All matching (deep crawl)" if active_project.last_limit == 0 else f"{active_project.last_limit or 50} postings"
                st.markdown(
                    f"""
                    <div class='saved-criteria-card'>
                        <div class='saved-criteria-title'>SAVED PROJECT CRITERIA</div>
                        <div class='saved-criteria-item'><b>Query:</b> <code style='color: #38bdf8;'>{active_project.last_keywords}</code></div>
                        <div class='saved-criteria-item'><b>Location:</b> {active_project.last_location or "Global / Any"}</div>
                        <div class='saved-criteria-item'><b>Workplace:</b> {active_project.last_workplace or "Any"} | <b>Level:</b> {active_project.last_experience or "All"}</div>
                        <div class='saved-criteria-item'><b>Limit:</b> {limit_disp}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if st.button("Run query again", icon=":material/refresh:", width="stretch", key="btn_rerun_saved_query"):
                    with st.spinner(f"Scraping fresh jobs for '{active_project.last_keywords}'..."):
                        wp_enum = WorkplaceType(active_project.last_workplace) if active_project.last_workplace and active_project.last_workplace != "any" else None
                        exp_enum = ExperienceLevel(active_project.last_experience) if active_project.last_experience and active_project.last_experience != "any" else None
                        re_limit = active_project.last_limit if active_project.last_limit is not None else 50
                        q = SearchQuery(
                            keywords=active_project.last_keywords or "Data Analyst",
                            location=active_project.last_location or "",
                            workplace_type=wp_enum,
                            experience_level=exp_enum,
                            limit=re_limit,
                            project_id=active_project.id
                        )
                        fresh_jobs = st.session_state.client.search_jobs(q)
                        if fresh_jobs:
                            run_id = st.session_state.repo.save_search_run(q, total_found=len(fresh_jobs), project_id=active_project.id)
                            res = st.session_state.repo.save_jobs(fresh_jobs, search_run_id=run_id, project_id=active_project.id)
                            st.session_state.jobs = st.session_state.repo.get_all_jobs(project_id=active_project.id)
                            st.session_state.stats = MetricsEngine.aggregate(st.session_state.jobs, query_keywords=active_project.last_keywords or active_project.name or "General")
                            st.session_state.flash_msg = ("success", f"Collected {len(fresh_jobs)} postings: {res['new_count']} newly added ({res['updated_count']} duplicates updated).")
                            st.rerun()
                        else:
                            st.warning("No new postings found for this query.")

        st.markdown("---")
        st.header("Search and scraper filters", icon=":material/tune:")

        # Preset Role Pickers
        role_choices = ["(Custom Keywords)"] + SUGGESTED_ROLES
        selected_role = st.selectbox("Role quick-picks:", role_choices, index=1)
        
        default_kw = selected_role if selected_role != "(Custom Keywords)" else "Data Analyst"
        keywords_input = st.text_input("Role or search keywords:", value=default_kw)

        # Country / Location Presets
        loc_names = [name for name, _ in SUGGESTED_LOCATIONS]
        loc_map = {name: val for name, val in SUGGESTED_LOCATIONS}
        selected_loc_name = st.selectbox("Country or region quick-picks:", loc_names, index=0)
        
        preset_loc_val = loc_map[selected_loc_name]
        location_input = st.text_input("Location or country (auto-normalized):", value=preset_loc_val, placeholder="e.g. Worldwide, Pakistan, USA, UK, Germany, Remote")
        st.caption("Select 'Global / Any Location' or enter countries. Multi-page pagination automatically collects all matching pages.")

        # Workplace Mode
        workplace_choice = st.selectbox(
            "Workplace mode:",
            options=["Any workplace", "Remote only", "Hybrid", "Onsite or office"],
            index=0
        )
        workplace_map = {
            "Any workplace": None,
            "Remote only": WorkplaceType.REMOTE,
            "Hybrid": WorkplaceType.HYBRID,
            "Onsite or office": WorkplaceType.ONSITE
        }
        selected_workplace = workplace_map[workplace_choice]

        # Experience Level
        exp_choice = st.selectbox(
            "Experience level:",
            options=["All levels", "Entry level or junior", "Mid level", "Senior or staff", "Lead or principal"],
            index=0
        )
        exp_map = {
            "All levels": None,
            "Entry level or junior": ExperienceLevel.ENTRY,
            "Mid level": ExperienceLevel.MID,
            "Senior or staff": ExperienceLevel.SENIOR,
            "Lead or principal": ExperienceLevel.LEAD
        }
        selected_exp = exp_map[exp_choice]

        # Limit controls: Target slider + "Fetch All" toggle
        col_lim1, col_lim2 = st.columns([1.4, 1.6])
        with col_lim1:
            limit_slider = st.slider("Target limit:", min_value=10, max_value=1000, value=50, step=10, disabled=st.session_state.get("fetch_all_active", False))
        with col_lim2:
            st.write("")
            fetch_all = st.checkbox("Fetch all available", value=False, key="fetch_all_active", help="Paginates continuously until all matching jobs are collected (safety circuit breaker caps at 40 pages / ~2,500 jobs).")

        effective_limit = 0 if fetch_all else limit_slider
        if fetch_all:
            st.caption("Deep crawl active: collecting all matching postings until live results finish.")

        # Trigger Pipeline
        run_btn = st.button("Collect postings into project", icon=":material/search:", type="primary", width="stretch")

        if run_btn:
            with st.spinner(f"Ingesting live market postings into '{active_project.name}'..."):
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
                    limit=effective_limit,
                    project_id=st.session_state.active_project_id
                )

                new_jobs = st.session_state.client.search_jobs(query, progress_callback=progress_cb)

                if new_jobs:
                    prog_bar.progress(100)
                    status_text.text("Pipeline complete.")
                    run_id = st.session_state.repo.save_search_run(query, len(new_jobs), project_id=st.session_state.active_project_id)
                    save_res = st.session_state.repo.save_jobs(new_jobs, search_run_id=run_id, project_id=st.session_state.active_project_id)
                    st.session_state.jobs = st.session_state.repo.get_all_jobs(project_id=st.session_state.active_project_id)
                    st.session_state.stats = MetricsEngine.aggregate(st.session_state.jobs, query_keywords=active_project.name)

                    new_cnt = save_res.get("new_count", len(new_jobs)) if isinstance(save_res, dict) else len(new_jobs)
                    upd_cnt = save_res.get("updated_count", 0) if isinstance(save_res, dict) else 0
                    if upd_cnt > 0:
                        st.session_state.flash_msg = ("success", f"Ingested {len(new_jobs)} postings into '{active_project.name}': {new_cnt} newly added, {upd_cnt} duplicate postings refreshed. Total unique jobs in project: {len(st.session_state.jobs)}.")
                    else:
                        st.session_state.flash_msg = ("success", f"Successfully added {new_cnt} new postings into '{active_project.name}'. Total unique jobs in project: {len(st.session_state.jobs)}.")
                    st.rerun()
                else:
                    prog_bar.empty()
                    err = getattr(st.session_state.client, "last_error", None)
                    if err:
                        status_text.empty()
                        st.error(f"Scraping error: {err}")
                    else:
                        status_text.text("No results returned.")
                        st.warning("No postings found for this exact query. Try broadening the keywords or location.")

        st.markdown("---")
        st.markdown(f"**Project summary ({active_project.name}):**")
        st.write(f"Stored postings in project: **{len(st.session_state.jobs)}**")
        if st.button("Clear jobs in this project", icon=":material/delete_sweep:", width="stretch", disabled=len(st.session_state.jobs) == 0):
            clear_jobs_dialog(active_project.id, active_project.name, len(st.session_state.jobs))

        # ----------------- SYSTEM & SERVER MANAGEMENT -----------------
        st.markdown("---")
        with st.expander("Server and updates", icon=":material/settings:", expanded=False):
            info = get_running_instance()
            if info:
                st.caption(f"Status: Active on port `{info.get('port', 8501)}` (PID `{info.get('pid')}`)")
            else:
                st.caption("Status: Active (In-Process)")

            # Clean Server Stop / Shutdown Button
            if st.button("Stop server and release port", icon=":material/power_settings_new:", type="secondary", width="stretch"):
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
            st.caption(f"**Installed version:** `v{__version__}`")
            if "update_info" not in st.session_state:
                st.session_state.update_info = None

            if st.button("Check for updates", icon=":material/refresh:", width="stretch"):
                with st.spinner("Checking GitHub for newer releases..."):
                    res = UpdateChecker.check_for_update()
                    st.session_state.update_info = res
                    if res and res.get("has_update"):
                        st.session_state.update_msg = f"New version v{res['latest_version']} available."
                    else:
                        st.session_state.update_msg = f"StackCheck is up to date (v{__version__})."

            if st.session_state.get("update_msg"):
                st.info(st.session_state.update_msg)

            up_info = st.session_state.get("update_info")
            if up_info and up_info.get("has_update"):
                target_asset = up_info.get("target_asset")
                if target_asset and target_asset.get("download_url"):
                    if st.button(f"Download and update to v{up_info['latest_version']}", icon=":material/download:", type="primary", width="stretch"):
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
                            st.success(f"Updated to v{up_info['latest_version']}. Please restart StackCheck to apply.")
                        except Exception as e:
                            st.error(f"Update failed: {e}")

    # ----------------- MAIN TABS -----------------
    tab_dash, tab_analytics, tab_jobs = st.tabs([
        ":material/dashboard: Executive dashboard",
        ":material/analytics: Statistical analytics",
        ":material/work: Job explorer"
    ])

    jobs = st.session_state.jobs
    stats = st.session_state.stats

    # ----------------- TAB 1: EXECUTIVE DASHBOARD -----------------
    with tab_dash:
        if not jobs:
            st.info("Welcome to StackCheck. Use the left sidebar to select a role or country, then click 'Collect postings into project' to analyze live job market data.")
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

    # ----------------- TAB 2: DEEP STATISTICAL ANALYTICS -----------------
    with tab_analytics:
        if not jobs:
            st.info("Run a search in the sidebar to populate statistical visualizations.")
        else:
            # High-Level Market Analytics KPIs
            mkpi1, mkpi2, mkpi3, mkpi4 = st.columns(4)
            with mkpi1:
                st.metric("Salary disclosure rate", f"{stats.salary_transparency_pct:.1f}%", help="Percentage of postings with explicit salary information", border=True)
            with mkpi2:
                avg_b = stats.stack_density_stats.get("avg_skills_per_job", 0.0) if stats.stack_density_stats else 0.0
                st.metric("Average stack breadth", f"{avg_b} skills / job", help="Average number of tech skills requested per job post", border=True)
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

    # ----------------- TAB 3: JOBS EXPLORER -----------------
    with tab_jobs:
        if not jobs:
            st.info("No job postings available to explore. Run a search to populate.")
        else:
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

            # Apply sorting using converted USD values
            cards_to_show = list(filtered_jobs)
            if sort_order == "Highest salary first":
                cards_to_show.sort(
                    key=lambda j: currency_manager.convert_to_usd(
                        (j.salary.max_amount or j.salary.min_amount or 0),
                        currency=j.salary.currency,
                        country=j.country or j.location,
                        period=j.salary.period
                    ) if j.salary else 0,
                    reverse=True
                )
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
                    usd_equiv = currency_manager.convert_to_usd(
                        (job.salary.max_amount or job.salary.min_amount or 0),
                        currency=job.salary.currency,
                        country=job.country or job.location,
                        period=job.salary.period
                    )
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


if __name__ == "__main__":
    main()
