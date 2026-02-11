"""
Skill Mapper
Manages skill taxonomy, categorization, and tracking logic.
"""

from typing import List, Dict, Set, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from src.database import Skill, Project, ProjectSkill, ProjectCategory, DifficultyLevel


class SkillMapper:
    """
    Manages skill taxonomy and proficiency tracking.
    """
    
    # Skill to technology mapping
    SKILL_TECHNOLOGIES = {
        # AI/ML Skills
        "Machine Learning": ["python", "scikit-learn", "numpy", "pandas", "matplotlib"],
        "Deep Learning": ["python", "pytorch", "tensorflow", "keras", "transformers"],
        "Natural Language Processing": ["python", "nltk", "spacy", "transformers", "huggingface"],
        "Computer Vision": ["python", "opencv", "pytorch", "tensorflow", "pillow"],
        "MLOps": ["mlflow", "kubeflow", "docker", "kubernetes", "fastapi"],
        
        # Full-Stack Skills
        "Backend Development": ["python", "fastapi", "django", "flask", "nodejs", "express"],
        "Frontend Development": ["javascript", "typescript", "react", "nextjs", "vue", "html", "css"],
        "REST APIs": ["fastapi", "express", "django-rest", "swagger", "postman"],
        "Database Design": ["postgresql", "mongodb", "redis", "sqlite", "sqlalchemy"],
        "Web Frameworks": ["fastapi", "django", "express", "react", "nextjs"],
        
        # System Design Skills
        "Distributed Systems": ["docker", "kubernetes", "microservices", "grpc", "rabbitmq"],
        "Caching Strategies": ["redis", "memcached", "cdn", "nginx"],
        "Message Queues": ["rabbitmq", "kafka", "celery", "redis"],
        "Microservices": ["docker", "kubernetes", "grpc", "consul", "istio"],
        "Load Balancing": ["nginx", "haproxy", "aws-elb", "kubernetes"],
        
        # Security/Blockchain Skills
        "Authentication": ["jwt", "oauth", "passport", "auth0", "session management"],
        "Encryption": ["cryptography", "hashlib", "bcrypt", "aes", "rsa"],
        "Web Security": ["owasp", "xss-prevention", "csrf", "sql-injection-prevention"],
        "Smart Contracts": ["solidity", "ethereum", "web3", "truffle", "hardhat"],
        "Security Auditing": ["penetration-testing", "vulnerability-scanning", "security-analysis"]
    }
    
    # Category to skill mapping
    CATEGORY_SKILLS = {
        ProjectCategory.AI_ML: [
            "Machine Learning", "Deep Learning", "Natural Language Processing",
            "Computer Vision", "MLOps"
        ],
        ProjectCategory.FULL_STACK: [
            "Backend Development", "Frontend Development", "REST APIs",
            "Database Design", "Web Frameworks"
        ],
        ProjectCategory.SYSTEM_DESIGN: [
            "Distributed Systems", "Caching Strategies", "Message Queues",
            "Microservices", "Load Balancing"
        ],
        ProjectCategory.SECURITY_BLOCKCHAIN: [
            "Authentication", "Encryption", "Web Security",
            "Smart Contracts", "Security Auditing"
        ]
    }
    
    def __init__(self, session: Session):
        """
        Initialize skill mapper.
        
        Args:
            session: Database session
        """
        self.session = session
    
    def get_skills_for_category(self, category: ProjectCategory) -> List[Skill]:
        """
        Get all skills belonging to a category.
        
        Args:
            category: Project category
            
        Returns:
            List of Skill objects
        """
        skill_names = self.CATEGORY_SKILLS.get(category, [])
        
        skills = (
            self.session.query(Skill)
            .filter(Skill.name.in_(skill_names))
            .all()
        )
        
        return skills
    
    def get_skill_gaps(self, config) -> Dict[ProjectCategory, float]:
        """
        Analyze skill gaps based on current proficiency and target weights.
        
        Args:
            config: System configuration with skill focus areas
            
        Returns:
            Dictionary mapping categories to gap scores (higher = more gap)
        """
        gaps = {}
        
        # Get focus areas (handle both dict and object attribute access)
        if hasattr(config.skills, 'focus_areas'):
            focus_areas = config.skills.focus_areas
            if isinstance(focus_areas, dict):
                # Already a dict
                pass
            else:
                # Convert to dict if needed
                focus_areas = focus_areas.__dict__ if hasattr(focus_areas, '__dict__') else {}
        else:
            focus_areas = {}
        
        for category in ProjectCategory:
            category_key = category.value  # e.g., "ai_ml"
            target_weight = focus_areas.get(category_key, 0)
            
            # Get current proficiency for this category
            skills = self.get_skills_for_category(category)
            
            if skills:
                avg_proficiency = sum(s.proficiency for s in skills) / len(skills)
            else:
                avg_proficiency = 0.0
            
            # Gap score: how far below target (considering both weight and proficiency)
            # Higher weight categories with low proficiency get higher gaps
            gap_score = target_weight * (100 - avg_proficiency) / 100
            
            gaps[category] = gap_score
        
        return gaps
    
    def select_category_for_project(self, config) -> ProjectCategory:
        """
        Select the best category for next project based on skill gaps.
        
        Args:
            config: System configuration
            
        Returns:
            ProjectCategory to focus on
        """
        gaps = self.get_skill_gaps(config)
        
        # Select category with highest gap
        selected_category = max(gaps.items(), key=lambda x: x[1])[0]
        
        return selected_category
    
    def select_skills_for_project(
        self,
        category: ProjectCategory,
        num_skills: int = 3
    ) -> List[Skill]:
        """
        Select specific skills to focus on for a project.
        
        Args:
            category: Project category
            num_skills: Number of skills to select
            
        Returns:
            List of Skill objects prioritized by lowest proficiency
        """
        skills = self.get_skills_for_category(category)
        
        # Sort by proficiency (lowest first) and projects count
        sorted_skills = sorted(
            skills,
            key=lambda s: (s.proficiency, s.projects_count)
        )
        
        return sorted_skills[:num_skills]
    
    def get_technologies_for_skills(self, skills: List[Skill]) -> List[str]:
        """
        Get recommended technologies for given skills.
        
        Args:
            skills: List of skills
            
        Returns:
            List of technology names
        """
        technologies = set()
        
        for skill in skills:
            skill_techs = self.SKILL_TECHNOLOGIES.get(skill.name, [])
            technologies.update(skill_techs[:2])  # Take top 2 from each skill
        
        return list(technologies)
    
    def update_skill_proficiency(
        self,
        skill: Skill,
        difficulty: DifficultyLevel,
        contribution_weight: float = 1.0
    ):
        """
        Update skill proficiency based on project completion.
        
        Args:
            skill: Skill to update
            difficulty: Project difficulty level
            contribution_weight: How much this project contributes (0.0-1.0)
        """
        # Calculate proficiency gain based on difficulty
        difficulty_multipliers = {
            DifficultyLevel.BEGINNER: 2.0,
            DifficultyLevel.INTERMEDIATE: 4.0,
            DifficultyLevel.ADVANCED: 6.0
        }
        
        base_gain = difficulty_multipliers.get(difficulty, 2.0)
        actual_gain = base_gain * contribution_weight
        
        # Apply diminishing returns as proficiency increases
        current_prof = skill.proficiency
        if current_prof >= 80:
            actual_gain *= 0.5  # Half gain when nearly expert
        elif current_prof >= 50:
            actual_gain *= 0.75  # Reduced gain when intermediate
        
        # Update proficiency (cap at 100)
        skill.proficiency = min(100, current_prof + actual_gain)
        skill.projects_count += 1
        skill.last_used = datetime.utcnow()
        skill.updated_at = datetime.utcnow()
    
    def get_difficulty_for_proficiency(
        self,
        avg_proficiency: float,
        config
    ) -> DifficultyLevel:
        """
        Determine appropriate difficulty level based on proficiency.
        
        Args:
            avg_proficiency: Average proficiency of selected skills
            config: System configuration
            
        Returns:
            Appropriate difficulty level
        """
        # Get progression rate from config (handle both dict and object attribute access)
        if hasattr(config.skills, 'progression'):
            progression = config.skills.progression
            rate = progression.get('advancement_rate', 'moderate') if isinstance(progression, dict) else progression.advancement_rate
        else:
            rate = 'moderate'
        
        # Define thresholds based on rate
        if rate == "slow":
            intermediate_threshold = 40
            advanced_threshold = 70
        elif rate == "fast":
            intermediate_threshold = 20
            advanced_threshold = 50
        else:  # moderate
            intermediate_threshold = 30
            advanced_threshold = 60
        
        # Select difficulty
        if avg_proficiency < intermediate_threshold:
            return DifficultyLevel.BEGINNER
        elif avg_proficiency < advanced_threshold:
            return DifficultyLevel.INTERMEDIATE
        else:
            return DifficultyLevel.ADVANCED
    
    def get_skill_summary(self) -> Dict[str, any]:
        """
        Get summary of all skills and proficiencies.
        
        Returns:
            Dictionary with skill statistics
        """
        all_skills = self.session.query(Skill).all()
        
        summary = {
            "total_skills": len(all_skills),
            "average_proficiency": sum(s.proficiency for s in all_skills) / len(all_skills) if all_skills else 0,
            "by_category": {}
        }
        
        for category in ProjectCategory:
            category_skills = self.get_skills_for_category(category)
            if category_skills:
                avg_prof = sum(s.proficiency for s in category_skills) / len(category_skills)
                summary["by_category"][category.value] = {
                    "count": len(category_skills),
                    "average_proficiency": avg_prof
                }
        
        return summary
