"""
Analytics Engine
Aggregates data for dashboard and reporting.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from sqlalchemy import func
from rich.console import Console

from src.database import Project, Skill, Commit, DailyActivity, ProjectStatus, ProjectSkill

class AnalyticsEngine:
    """Provides data aggregation and analysis for the system."""
    
    def __init__(self, session):
        self.session = session
    
    def get_total_stats(self) -> Dict:
        """Get high-level system statistics."""
        return {
            "projects": self.session.query(Project).count(),
            "completed": self.session.query(Project).filter(Project.status == ProjectStatus.COMPLETED).count(),
            "commits": self.session.query(Commit).count(),
            "skills": self.session.query(Skill).count(),
            "lines_of_code": 0  # Placeholder, would need to sum from projects
        }
    
    def get_skill_proficiency(self) -> List[Skill]:
        """Get all skills ordered by proficiency."""
        return self.session.query(Skill).order_by(Skill.proficiency.desc()).all()
    
    def get_activity_history(self, days: int = 30) -> List[DailyActivity]:
        """Get daily activity for the last N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return self.session.query(DailyActivity).filter(
            DailyActivity.date >= cutoff
        ).order_by(DailyActivity.date.asc()).all()
    
    def get_top_technologies(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most frequently used technologies."""
        # This requires parsing technologies from projects
        # For now, we can aggregate from Project.technologies (JSON)
        # But SQL query on JSON is specific to DB. 
        # We'll do it in python for sqlite compatibility.
        projects = self.session.query(Project).all()
        tech_counts = {}
        for p in projects:
            if p.technologies:
                import json
                try:
                    techs = json.loads(p.technologies) if isinstance(p.technologies, str) else p.technologies
                    for t in techs:
                        tech_counts[t] = tech_counts.get(t, 0) + 1
                except:
                    pass
        
        return sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    def calculate_streak(self) -> int:
        """Calculate current activity streak in days."""
        activities = self.session.query(DailyActivity).order_by(DailyActivity.date.desc()).all()
        if not activities:
            return 0
            
        streak = 0
        today = datetime.utcnow().date()
        
        # Check if active today
        last_active = activities[0].date.date()
        if last_active == today:
            streak = 1
        elif last_active == today - timedelta(days=1):
            streak = 1
        else:
            return 0
            
        # Iterate backwards
        for i in range(1, len(activities)):
            current = activities[i].date.date()
            prev = activities[i-1].date.date()
            
            if (prev - current).days == 1:
                streak += 1
            else:
                break
        
        return streak
    
    def calculate_portfolio_score(self) -> float:
        """Calculate overall portfolio readiness score (0-100)."""
        # Factors:
        # 1. Skill Proficiency (50%)
        # 2. Project Completion (30%)
        # 3. Consistency/Streak (20%)
        
        # 1. Avg Proficiency
        skills = self.session.query(Skill).all()
        if not skills:
            return 0.0
        avg_proficiency = sum(s.proficiency for s in skills) / len(skills)
        
        # 2. Projects (cap at 20 projects for full score)
        completed = self.session.query(Project).filter(Project.status == ProjectStatus.COMPLETED).count()
        project_score = min(completed * 5, 100)
        
        # 3. Streak (cap at 30 days)
        streak = self.calculate_streak()
        streak_score = min(streak * 3.33, 100)
        
        # Weighted sum
        score = (avg_proficiency * 0.5) + (project_score * 0.3) + (streak_score * 0.2)
        return round(score, 1)
