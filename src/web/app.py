"""
Web Interface for GitHub Activity Generator
Built with Streamlit and Plotly.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.config_manager import get_config_manager
from src.database import get_database_manager, Project, Skill, DailyActivity, ProjectStatus
from src.tracking.analytics import AnalyticsEngine
from src.orchestration.workflow_engine import WorkflowEngine
import time
import threading

# Page Config
st.set_page_config(
    page_title="GitHub Activity Generator",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Managers
@st.cache_resource
def get_managers():
    config_manager = get_config_manager()
    config = config_manager.load_config()
    db_url = f"sqlite:///{config.database.path}"
    db_manager = get_database_manager(db_url)
    session = db_manager.get_session()
    analytics = AnalyticsEngine(session)
    return config, session, analytics

config, session, analytics = get_managers()

# Sidebar
st.sidebar.title("🚀 Control Panel")

# System Status
st.sidebar.subheader("System Status")
scheduler_active = st.sidebar.checkbox("Scheduler Active", value=config.scheduling.enabled, disabled=True)
mode = st.sidebar.selectbox("Automation Mode", ["auto", "review", "manual"], index=["auto", "review", "manual"].index(config.automation.mode), disabled=True)

# Actions
st.sidebar.subheader("Actions")
if st.sidebar.button("Generate Project Now ⚡"):
    with st.spinner("Generating project... Check terminal for logs."):
        # We run this in a separate thread/process ideally, but for now blocking is okay for single user
        try:
            engine = WorkflowEngine(dry_run=False) # Respect config
            project = engine.run_daily_workflow()
            if project:
                st.success(f"Project '{project.title}' generated successfully!")
                session.commit() # Ensure DB update is seen
                time.sleep(2)
                st.rerun()
            else:
                st.error("Project generation failed or skipped.")
        except Exception as e:
            st.error(f"Error: {e}")

# Main Content
st.title("GitHub Activity Dashboard 📊")

# Top Metrics
stats = analytics.get_total_stats()
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Projects", stats["projects"])
with col2:
    st.metric("Total Commits", stats["commits"])
with col3:
    streak = analytics.calculate_streak()
    st.metric("Current Streak", f"{streak} days")
with col4:
    score = analytics.calculate_portfolio_score()
    st.metric("Portfolio Score", f"{score}/100")

# Tabs
tab1, tab2, tab3 = st.tabs(["Overview", "Skills", "History"])

with tab1:
    # Recent Activity Chart
    st.subheader("Activity History")
    activities = analytics.get_activity_history(30)
    if activities:
        data = [{"date": a.date, "commits": a.commits_made} for a in activities]
        df = pd.DataFrame(data)
        fig = px.bar(df, x="date", y="commits", title="Daily Commits (Last 30 Days)", color_discrete_sequence=["#00CC96"])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No activity data available yet.")

with tab2:
    # Skills Radar/Bar Chart
    st.subheader("Skill Proficiency")
    skills = analytics.get_skill_proficiency()
    if skills:
        skill_data = [{"skill": s.name, "proficiency": s.proficiency, "category": s.category.value} for s in skills]
        df_skills = pd.DataFrame(skill_data)
        
        # Sort by proficiency
        df_skills = df_skills.sort_values("proficiency", ascending=True)
        
        fig = px.bar(
            df_skills, 
            x="proficiency", 
            y="skill", 
            orientation='h', 
            color="category",
            title="Skill Proficiency Levels",
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No skills tracked yet.")

with tab3:
    # Project History Table
    st.subheader("Project History")
    projects = session.query(Project).order_by(Project.created_at.desc()).all()
    
    if projects:
        project_data = []
        for p in projects:
            project_data.append({
                "Title": p.title,
                "Category": p.category.value,
                "Difficulty": p.difficulty.value,
                "Status": p.status.value,
                "Date": p.created_at.strftime("%Y-%m-%d"),
                "Repo": p.repository_url
            })
        
        st.dataframe(pd.DataFrame(project_data), use_container_width=True)
    else:
        st.info("No projects generated yet.")

# Footer
st.markdown("---")
st.caption("GitHub Activity Generator Local Dashboard v1.0.0")
