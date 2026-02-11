"""
Project Planner
AI-powered project idea generation based on skill gaps and career progression.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json

from src.database import Project, ProjectCategory, DifficultyLevel, ProjectStatus, Skill
from src.planning.skill_mapper import SkillMapper
from src.generation.ai_provider import get_ai_client
import random


@dataclass
class ProjectBrief:
    """Represents a complete project specification."""
    title: str
    description: str
    category: ProjectCategory
    difficulty: DifficultyLevel
    technologies: List[str]
    primary_language: str
    skills: List[str]
    learning_objectives: List[str]
    deliverables: List[str]
    estimated_hours: int
    app_type: str = "script"  # script, web, api, system, tool


class ProjectPlanner:
    """
    Intelligent project planning engine.
    Plans projects based on skill gaps, progression, and diversity requirements.
    """
    
    def __init__(self, session: Session, config):
        """
        Initialize project planner.
        
        Args:
            session: Database session
            config: System configuration
        """
        self.session = session
        self.config = config
        self.skill_mapper = SkillMapper(session)
        self.ai_client = get_ai_client(config)
    
    def generate_project_idea(self) -> ProjectBrief:
        """
        Generate a new project idea based on current skill gaps.
        
        Returns:
            ProjectBrief with complete project specification
        """
        # Step 1: Analyze skill gaps and select category
        category = self.skill_mapper.select_category_for_project(self.config)
        
        # Step 2: Select specific skills to focus on
        target_skills = self.skill_mapper.select_skills_for_project(category, num_skills=3)
        
        if not target_skills:
            # Fallback if no skills found
            avg_proficiency = 0
            # Try to pick any random skill from the database
            all_skills = self.session.query(Skill).all()
            if all_skills:
                target_skills = [random.choice(all_skills)]
        
        if target_skills:
            avg_proficiency = sum(s.proficiency for s in target_skills) / len(target_skills)
        else:
             avg_proficiency = 0
        difficulty = self.skill_mapper.get_difficulty_for_proficiency(
            avg_proficiency,
            self.config
        )
        
        # Step 4: Get recommended technologies
        technologies = self.skill_mapper.get_technologies_for_skills(target_skills)
        
        # Step 5: Check recent projects for diversity
        recent_projects = self._get_recent_projects(days=7)
        recent_titles = [p.title for p in recent_projects]
        recent_techs = []
        for p in recent_projects:
            if p.technologies:
                recent_techs.extend(p.technologies)
        
        # Step 6: Use AI to generate creative project idea
        project_idea = self._generate_ai_project_idea(
            category=category,
            skills=[s.name for s in target_skills],
            technologies=technologies,
            difficulty=difficulty,
            avoid_titles=recent_titles,
            avoid_techs=list(set(recent_techs))
        )
        
        return project_idea
    
    def _get_recent_projects(self, days: int = 7) -> List[Project]:
        """Get projects created in the last N days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        projects = (
            self.session.query(Project)
            .filter(Project.created_at >= cutoff_date)
            .order_by(Project.created_at.desc())
            .all()
        )
        
        return projects
    
    def _generate_ai_project_idea(
        self,
        category: ProjectCategory,
        skills: List[str],
        technologies: List[str],
        difficulty: DifficultyLevel,
        avoid_titles: List[str] = None,
        avoid_techs: List[str] = None
    ) -> ProjectBrief:
        """
        Use AI to generate a creative, relevant project idea.
        
        Args:
            category: Project category
            skills: Skills to focus on
            technologies: Recommended technologies
            difficulty: Target difficulty level
            avoid_titles: Recently used project titles to avoid
            avoid_techs: Recently used technologies to avoid repetition
            
        Returns:
            ProjectBrief with AI-generated project specification
        """
        avoid_titles = avoid_titles or []
        avoid_techs = avoid_techs or []
        
        # Build prompt for AI
        system_message = """You are an expert technical project designer for Computer Science students pursuing careers in AI and software engineering. Generate creative, meaningful project ideas that build real skills and look good in a portfolio."""
        
        user_prompt = f"""Generate a unique, portfolio-worthy project idea with the following requirements:

**Category**: {category.value.replace('_', ' ').title()}
**Skills to Develop**: {', '.join(skills)}
**Difficulty Level**: {difficulty.value.title()}
**Recommended Technologies**: {', '.join(technologies[:5])}

**Constraints**:
- Avoid these recent project titles: {', '.join(avoid_titles[-3:]) if avoid_titles else 'None'}
- Try to use different technologies than: {', '.join(set(avoid_techs[-5:])) if avoid_techs else 'None'}
- Project should be completable in 2-4 hours for initial version
- Must be genuinely useful or educational, not just a toy example
- Should demonstrate industry-relevant skills

**Required Output Format (JSON)**:
{{
  "title": "Project title (creative, descriptive, max 60 chars)",
  "description": "2-3 sentence description of what the project does and why it's valuable",
  "technologies": ["tech1", "tech2", "tech3"],
  "primary_language": "main programming language",
  "learning_objectives": ["objective1", "objective2", "objective3"],
  "deliverables": ["file/component1", "file/component2", "README.md", "tests"],
  "estimated_hours": 3
}}

Generate ONLY the JSON, no additional text."""
        
        try:
            # Get AI response
            response = self.ai_client.generate(
                prompt=user_prompt,
                system_message=system_message,
                temperature=0.8,  # Higher temperature for creativity
                max_tokens=800
            )
            
            # Parse JSON response
            # Try to extract JSON if wrapped in markdown code blocks
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response.strip()
            
            project_data = json.loads(json_str)
            
            # Create ProjectBrief from AI response
            project_brief = ProjectBrief(
                title=project_data["title"],
                description=project_data["description"],
                category=category,
                difficulty=difficulty,
                technologies=project_data["technologies"],
                primary_language=project_data["primary_language"],
                skills=skills,
                learning_objectives=project_data["learning_objectives"],
                deliverables=project_data["deliverables"],
                estimated_hours=project_data.get("estimated_hours", 3)
            )
            
            return project_brief
        
        except Exception as e:
            # Fallback to template-based generation if AI fails
            print(f"AI generation failed: {e}, using fallback...")
            return self._generate_fallback_project(category, skills, technologies, difficulty)
    
    def _generate_fallback_project(
        self,
        category: ProjectCategory,
        skills: List[str],
        technologies: List[str],
        difficulty: DifficultyLevel
    ) -> ProjectBrief:
        """Generate a basic project idea without AI (fallback)."""
        
        # Enhanced fallback generation
        skill_name = skills[0] if skills else "Python"
        tech = technologies[0] if technologies else "Python"
        
        # Templates for each category
        templates = {
            ProjectCategory.AI_ML: [
                {
                    "title": f"{skill_name} Classifier",
                    "description": f"Build a classification model using {skill_name} and {tech} to categorize datasets. Includes data preprocessing, training visualization, and metrics.",
                    "app_type": "script"
                },
                {
                    "title": f"{skill_name} Data Analyzer",
                    "description": f"A data analysis tool leveraging {skill_name} to uncover insights. Features pandas integration and matplotlib plotting.",
                    "app_type": "script"
                },
                {
                    "title": f"Predictive Model with {tech}",
                    "description": f"Create a predictive engine using {tech} libraries. Focuses on regression analysis and feature engineering.",
                    "app_type": "script"
                }
            ],
            ProjectCategory.FULL_STACK: [
                {
                    "title": f"{skill_name} Task Manager",
                    "description": f"A web-based task management application built with {tech}. Demonstrates CRUD operations and state management.",
                    "app_type": "web"
                },
                {
                    "title": f"{tech} Dashboard",
                    "description": f"Interactive dashboard displaying real-time data using {tech}. Highlights UI/UX principles and component design.",
                    "app_type": "web"
                },
                {
                    "title": f"{skill_name} Portfolio API",
                    "description": f"RESTful API service for portfolio data, implemented in {tech}. Includes authentication and documentation.",
                    "app_type": "api"
                }
            ],
            ProjectCategory.SYSTEM_DESIGN: [
                {
                    "title": f"{skill_name} Load Balancer",
                    "description": f"Simulation of a load balancer using {tech}. Demonstrates round-robin and least-connections algorithms.",
                    "app_type": "system"
                },
                {
                    "title": f"Distributed {skill_name} Cache",
                    "description": f"In-memory caching system designed for distributed environments. Implements LRU eviction and consistency checks.",
                    "app_type": "system"
                },
                {
                    "title": f"{tech} Rate Limiter",
                    "description": f"API rate limiter middleware using {tech}. Explore token bucket and leaky bucket algorithms.",
                    "app_type": "system"
                }
            ],
            ProjectCategory.SECURITY_BLOCKCHAIN: [
                {
                    "title": f"{skill_name} Encryptor",
                    "description": f"File encryption utility using {tech}. Implements AES and RSA standards for secure data storage.",
                    "app_type": "tool"
                },
                {
                    "title": f"{tech} Vulnerability Scanner",
                    "description": f"Automated script to scan for common vulnerabilities. Focuses on {skill_name} security best practices.",
                    "app_type": "tool"
                },
                {
                    "title": f"Simple Block Chain in {tech}",
                    "description": f"Educational implementation of a blockchain structure. Covers hashing, mining, and transaction validation.",
                    "app_type": "tool"
                }
            ]
        }
        
        category_templates = templates.get(category, templates[ProjectCategory.AI_ML])
        # Pick a random template
        template = random.choice(category_templates)
        
        return ProjectBrief(
            title=template["title"],
            description=template["description"],
            category=category,
            difficulty=difficulty,
            technologies=technologies[:3],
            primary_language="python", # Simplifying for fallback to ensure templates work
            skills=skills,
            learning_objectives=[f"Master {skill}" for skill in skills] + ["Understand project structure", "Implement core logic"],
            deliverables=["src/main.py", "README.md", "requirements.txt", "tests/test_core.py"],
            estimated_hours=3,
            app_type=template.get("app_type", "script")
        )
    
    def validate_project_novelty(self, project_brief: ProjectBrief) -> bool:
        """
        Check if project title is unique (not recently used).
        
        Args:
            project_brief: Project to validate
            
        Returns:
            True if project is novel enough
        """
        # Check for exact title match
        existing = (
            self.session.query(Project)
            .filter(Project.title == project_brief.title)
            .first()
        )
        
        if existing:
            return False
        
        # Check for very similar titles in recent projects (last 30 days)
        cutoff = datetime.utcnow() - timedelta(days=30)
        recent = (
            self.session.query(Project)
            .filter(Project.created_at >= cutoff)
            .all()
        )
        
        # Simple similarity check (could be enhanced)
        title_lower = project_brief.title.lower()
        for proj in recent:
            if proj.title.lower() in title_lower or title_lower in proj.title.lower():
                return False
        
        return True
    
    def create_project_record(self, project_brief: ProjectBrief) -> Project:
        """
        Create database record for the project.
        
        Args:
            project_brief: Project specification
            
        Returns:
            Created Project object
        """
        project = Project(
            title=project_brief.title,
            description=project_brief.description,
            category=project_brief.category,
            difficulty=project_brief.difficulty,
            technologies=project_brief.technologies,
            primary_language=project_brief.primary_language,
            status=ProjectStatus.PLANNED,
            file_structure={},
            lines_of_code=0,
            has_readme=False,
            has_tests=False,
            documentation_coverage=0.0,
            code_quality_score=0.0,
            created_at=datetime.utcnow()
        )
        
        self.session.add(project)
        self.session.commit()
        
        # Link skills to project
        from src.database import Skill, ProjectSkill
        
        for skill_name in project_brief.skills:
            skill = (
                self.session.query(Skill)
                .filter(Skill.name == skill_name)
                .first()
            )
            
            if skill:
                project_skill = ProjectSkill(
                    project_id=project.id,
                    skill_id=skill.id,
                    contribution_weight=1.0
                )
                self.session.add(project_skill)
        
        self.session.commit()
        
        return project
