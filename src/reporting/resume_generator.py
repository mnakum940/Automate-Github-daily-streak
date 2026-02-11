"""
Resume Generator
Generates a professional resume based on tracked activity and projects.
"""

from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import json

from rich.console import Console
from sqlalchemy.orm import Session

from src.database import Project, Skill, Achievement, ProjectStatus
from src.generation.ai_provider import get_ai_client

console = Console()

class ResumeGenerator:
    """Generates professional resumes from system data."""
    
    def __init__(self, session: Session, config):
        self.session = session
        self.config = config
        self.ai_client = get_ai_client(config)
        self.output_dir = Path("output/resumes")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_resume(self, output_format: str = 'md') -> Path:
        """
        Generate a resume based on current data.
        
        Args:
            output_format: 'md' or 'html' (currently only md supported)
            
        Returns:
            Path to generated resume file
        """
        # 1. Collect Data
        data = self._collect_data()
        
        if not data["projects"]:
            console.print("[yellow]Warning: No completed projects found. Resume may be sparse.[/yellow]")
            
        # 2. Generate Content with AI
        console.print("[cyan]Generating professional descriptions with AI...[/cyan]")
        resume_content = self._generate_content_with_ai(data)
        
        # 3. Render Output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resume_{timestamp}.md"
        output_path = self.output_dir / filename
        
        output_path.write_text(resume_content, encoding='utf-8')
        
        return output_path

    def _collect_data(self) -> Dict:
        """Aggregate data from database."""
        # Projects
        projects = self.session.query(Project).filter(
            Project.status == ProjectStatus.COMPLETED
        ).order_by(Project.created_at.desc()).all()
        
        project_data = []
        for p in projects:
            project_data.append({
                "title": p.title,
                "description": p.description,
                "technologies": p.technologies,
                "url": p.repository_url,
                "date": p.created_at.strftime("%B %Y")
            })
            
        # Skills
        skills = self.session.query(Skill).order_by(Skill.proficiency.desc()).limit(10).all()
        skill_data = [{"name": s.name, "level": f"{s.proficiency:.0f}%"} for s in skills]
        
        # Achievements
        achievements = self.session.query(Achievement).filter_by(is_unlocked=True).all()
        achievement_data = [{"name": a.name, "description": a.description, "icon": a.icon} for a in achievements]
        
        return {
            "projects": project_data,
            "skills": skill_data,
            "achievements": achievement_data,
            "generated_at": datetime.now().strftime("%Y-%m-%d")
        }

    def _generate_content_with_ai(self, data: Dict) -> str:
        """Use AI to generate professional resume content."""
        
        prompt = f"""Create a professional technical resume in Markdown format based on this data:

{json.dumps(data, indent=2)}

Requirements:
1. **Header**: Use a placeholder Name "GitHub Developer" (or extracting from config if available).
2. **Professional Summary**: Write a compelling summary highlighting the diversity of projects and skills.
3. **Skills Section**: Group skills logically.
4. **Projects Section**:
   - Use the project title and date.
   - REWRITE the description to be action-oriented and professional (e.g., "Architected...", "Implemented...").
   - Highlight technologies used.
5. **Achievements Section**: List the unlocked achievements as "Honors & Awards".
6. **Format**: Clean Markdown, ready to be converted to PDF.

Output ONLY the Markdown content.
"""
        
        try:
            return self.ai_client.generate(
                prompt=prompt,
                system_message="You are a professional career coach and technical writer.",
                temperature=0.7,
                max_tokens=2000
            )
        except Exception as e:
            console.print(f"[red]AI Generation failed: {e}[/red]")
            return self._generate_fallback(data)

    def _generate_fallback(self, data: Dict) -> str:
        """Fallback template if AI fails."""
        md = f"# Technical Resume\n\nGenerated: {data['generated_at']}\n\n"
        
        md += "## Professional Summary\n\npassionate developer with experience in automated software generation.\n\n"
        
        md += "## Skills\n\n"
        for s in data['skills']:
            md += f"- **{s['name']}**: {s['level']}\n"
            
        md += "\n## Projects\n\n"
        for p in data['projects']:
            md += f"### {p['title']}\n"
            md += f"*{p['date']}* | [Repo]({p['url']})\n\n"
            md += f"{p['description']}\n\n"
            md += f"**Tech Stack**: {', '.join(p['technologies'])}\n\n"
            
        if data['achievements']:
            md += "## Honors & Awards\n\n"
            for a in data['achievements']:
                md += f"- {a['icon']} **{a['name']}**: {a['description']}\n"
                
        return md
