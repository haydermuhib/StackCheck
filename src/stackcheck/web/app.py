"""
Streamlit Web Dashboard for StackCheck.
Unified Tech Stack Intelligence Engine & Data Analytics Interface.
"""

import os
import signal
import time
import streamlit as st


from stackcheck import __version__
from stackcheck.config import get_assets_dir
from stackcheck.updater import UpdateChecker
from stackcheck.launcher import stop_running_instance, get_running_instance
from stackcheck.models import SearchQuery, WorkplaceType, ExperienceLevel, Project
from stackcheck.client.hiringcafe import HiringCafeClient
from stackcheck.client.normalizer import SUGGESTED_ROLES, SUGGESTED_LOCATIONS, JobNormalizer
from stackcheck.analyzer.metrics import MetricsEngine
from stackcheck.storage.repository import JobRepository
from stackcheck.web.dialogs import create_project_dialog, delete_project_dialog, clear_jobs_dialog
from stackcheck.web.tabs.dashboard import render_dashboard_tab
from stackcheck.web.tabs.analytics import render_analytics_tab
from stackcheck.web.tabs.jobs import render_jobs_tab


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
        job_cnt = len(st.session_state.jobs)
        cached_stats = st.session_state.repo.get_cached_stats(st.session_state.active_project_id, expected_job_count=job_cnt)
        if cached_stats:
            st.session_state.stats = cached_stats
        else:
            st.session_state.stats = MetricsEngine.aggregate(st.session_state.jobs, query_keywords=proj_title)
            if job_cnt > 0:
                st.session_state.repo.save_cached_stats(st.session_state.active_project_id, st.session_state.stats, job_cnt)


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
    /* Metric card layout and top-right delta badge */
    [data-testid="stMetric"] {
        position: relative;
    }
    [data-testid="stMetric"]:has([data-testid="stMetricDelta"]) [data-testid="stMetricLabel"] {
        padding-right: 110px;
    }
    [data-testid="stMetric"] div:has(> [data-testid="stMetricDelta"]) {
        height: 0 !important;
        min-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: 0 !important;
        overflow: visible !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        position: absolute;
        top: 12px;
        right: 14px;
        margin: 0 !important;
        white-space: nowrap;
        z-index: 2;
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
            job_cnt = len(st.session_state.jobs)
            cached_stats = st.session_state.repo.get_cached_stats(selected_proj_id, expected_job_count=job_cnt)
            if cached_stats:
                st.session_state.stats = cached_stats
            else:
                st.session_state.stats = MetricsEngine.aggregate(st.session_state.jobs, query_keywords=p_name)
                if job_cnt > 0:
                    st.session_state.repo.save_cached_stats(selected_proj_id, st.session_state.stats, job_cnt)
            st.rerun()

        # Workspace actions with confirmation modals
        col_proj_a, col_proj_b = st.columns([1, 1])
        with col_proj_a:
            if st.button("New", icon=":material/add:", width="stretch", key="btn_open_new_proj_dlg"):
                create_project_dialog()
        with col_proj_b:
            if active_project.id != "default":
                if st.button("Delete", icon=":material/delete:", width="stretch", key="btn_open_del_proj_dlg"):
                    delete_project_dialog(active_project.id, active_project.name)
            else:
                st.button("Default", icon=":material/lock:", disabled=True, width="stretch", help="The default workspace cannot be deleted.")

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
                            st.session_state.repo.save_cached_stats(active_project.id, st.session_state.stats, len(st.session_state.jobs))
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
                    st.session_state.repo.save_cached_stats(st.session_state.active_project_id, st.session_state.stats, len(st.session_state.jobs))

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
        col_sum_a, col_sum_b = st.columns([1, 1])
        with col_sum_a:
            if st.button("Recalculate", icon=":material/refresh:", width="stretch", disabled=len(st.session_state.jobs) == 0, help="Force recalculate and update analytics cache"):
                with st.spinner("Recalculating analytics..."):
                    st.session_state.stats = MetricsEngine.aggregate(st.session_state.jobs, query_keywords=active_project.name)
                    st.session_state.repo.save_cached_stats(active_project.id, st.session_state.stats, len(st.session_state.jobs))
                    st.session_state.flash_msg = ("success", f"Recalculated analytics for '{active_project.name}'.")
                    st.rerun()
        with col_sum_b:
            if st.button("Clear jobs", icon=":material/delete_sweep:", width="stretch", disabled=len(st.session_state.jobs) == 0):
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

    with tab_dash:
        render_dashboard_tab(jobs, stats)

    with tab_analytics:
        render_analytics_tab(jobs, stats)

    with tab_jobs:
        render_jobs_tab(jobs, stats, active_project)


if __name__ == "__main__":
    main()
