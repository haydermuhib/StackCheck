"""
Confirmation modal dialogs for StackCheck Web Dashboard.
Manages interactive project creation, workspace deletion, and job clearing confirmation.
"""

import streamlit as st
from stackcheck.analyzer.metrics import MetricsEngine


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
