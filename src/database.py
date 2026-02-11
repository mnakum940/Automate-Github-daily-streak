"""
Database Models and Session Management
SQLAlchemy models for tracking projects, skills, commits, and daily activity.
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, 
    DateTime, Text, ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from enum import Enum


Base = declarative_base()


class DifficultyLevel(str, Enum):
    """Project difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ProjectCategory(str, Enum):
    """Project categories aligned with skill focus areas."""
    AI_ML = "ai_ml"
    FULL_STACK = "full_stack"
    SYSTEM_DESIGN = "system_design"
    SECURITY_BLOCKCHAIN = "security_blockchain"


class ProjectStatus(str, Enum):
    """Project lifecycle status."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Project(Base):
    """Tracks generated projects and their metadata."""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(SQLEnum(ProjectCategory), nullable=False)
    difficulty = Column(SQLEnum(DifficultyLevel), nullable=False)
    
    # Technology stack
    technologies = Column(JSON, default=list)  # List of technologies used
    primary_language = Column(String(50))
    
    # GitHub information
    repository_name = Column(String(200), unique=True)
    repository_url = Column(String(500))
    is_private = Column(Boolean, default=False)
    
    # Project status
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.PLANNED)
    
    # File structure
    file_structure = Column(JSON, default=dict)  # Dictionary of file paths and purposes
    lines_of_code = Column(Integer, default=0)
    
    # Quality metrics
    has_readme = Column(Boolean, default=False)
    has_tests = Column(Boolean, default=False)
    documentation_coverage = Column(Float, default=0.0)  # Percentage
    code_quality_score = Column(Float, default=0.0)  # 0-100
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    commits = relationship("Commit", back_populates="project", cascade="all, delete-orphan")
    project_skills = relationship("ProjectSkill", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, title='{self.title}', category={self.category.value})>"


class Skill(Base):
    """Tracks individual skills and proficiency levels."""
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(SQLEnum(ProjectCategory), nullable=False)
    proficiency = Column(Float, default=0.0)  # 0-100 scale
    
    # Metadata
    description = Column(Text)
    related_technologies = Column(JSON, default=list)  # Technologies that contribute to this skill
    
    # Tracking
    projects_count = Column(Integer, default=0)  # Number of projects using this skill
    last_used = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project_skills = relationship("ProjectSkill", back_populates="skill")
    
    def __repr__(self):
        return f"<Skill(id={self.id}, name='{self.name}', proficiency={self.proficiency:.1f})>"


class ProjectSkill(Base):
    """Many-to-many relationship between projects and skills."""
    __tablename__ = "project_skills"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    
    # How much this project contributed to the skill (weight)
    contribution_weight = Column(Float, default=1.0)
    
    # Relationships
    project = relationship("Project", back_populates="project_skills")
    skill = relationship("Skill", back_populates="project_skills")
    
    def __repr__(self):
        return f"<ProjectSkill(project_id={self.project_id}, skill_id={self.skill_id})>"


class Commit(Base):
    """Tracks individual Git commits."""
    __tablename__ = "commits"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    
    # Commit information
    commit_hash = Column(String(40), unique=True)
    commit_message = Column(Text, nullable=False)
    commit_type = Column(String(50))  # feat, fix, docs, refactor, test, etc.
    
    # Files changed
    files_changed = Column(JSON, default=list)  # List of file paths
    additions = Column(Integer, default=0)
    deletions = Column(Integer, default=0)
    
    # Metadata
    author_name = Column(String(100))
    author_email = Column(String(200))
    
    # Timestamps
    committed_at = Column(DateTime, default=datetime.utcnow)
    pushed_at = Column(DateTime, nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="commits")
    
    def __repr__(self):
        return f"<Commit(id={self.id}, message='{self.commit_message[:50]}...')>"


class DailyActivity(Base):
    """Tracks daily activity and summary statistics."""
    __tablename__ = "daily_activities"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, unique=True, nullable=False)  # Date only (time set to 00:00:00)
    
    # Activity metrics
    projects_created = Column(Integer, default=0)
    projects_completed = Column(Integer, default=0)
    commits_made = Column(Integer, default=0)
    lines_added = Column(Integer, default=0)
    lines_deleted = Column(Integer, default=0)
    
    # Skills worked on
    skills_practiced = Column(JSON, default=list)  # List of skill IDs
    technologies_used = Column(JSON, default=list)  # List of technologies
    
    # Quality metrics
    average_quality_score = Column(Float, default=0.0)
    
    # Execution metadata
    execution_successful = Column(Boolean, default=True)
    execution_time_seconds = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<DailyActivity(date={self.date.date()}, projects={self.projects_created})>"


class Achievement(Base):
    """Gamification achievements."""
    __tablename__ = 'achievements'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    description = Column(String(255))
    icon = Column(String(10))  # Emoji icon
    criteria_type = Column(String(50))  # 'project_count', 'streak', 'skill_level'
    criteria_value = Column(Integer)
    is_unlocked = Column(Boolean, default=False)
    unlocked_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Achievement(name='{self.name}', unlocked={self.is_unlocked})>"


class SystemMetadata(Base):
    """Stores system-level metadata and settings."""
    __tablename__ = "system_metadata"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    value_type = Column(String(20))  # str, int, float, bool, json
    
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SystemMetadata(key='{self.key}', value='{self.value}')>"


class DatabaseManager:
    """Manages database connection and operations."""
    
    def __init__(self, database_url: str = "sqlite:///data/activity_tracker.db"):
        """
        Initialize the database manager.
        
        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)."""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            Session: SQLAlchemy session
        """
        return self.SessionLocal()
    
    def initialize_default_skills(self, session: Session):
        """
        Initialize default skills in the database.
        
        Args:
            session: Database session
        """
        default_skills = [
            # AI/ML Skills
            {"name": "Machine Learning", "category": ProjectCategory.AI_ML, 
             "description": "General machine learning algorithms and techniques"},
            {"name": "Deep Learning", "category": ProjectCategory.AI_ML,
             "description": "Neural networks and deep learning frameworks"},
            {"name": "Natural Language Processing", "category": ProjectCategory.AI_ML,
             "description": "Text processing and NLP models"},
            {"name": "Computer Vision", "category": ProjectCategory.AI_ML,
             "description": "Image and video processing with ML"},
            {"name": "MLOps", "category": ProjectCategory.AI_ML,
             "description": "Machine learning operations and deployment"},
            
            # Full-Stack Skills
            {"name": "Backend Development", "category": ProjectCategory.FULL_STACK,
             "description": "Server-side application development"},
            {"name": "Frontend Development", "category": ProjectCategory.FULL_STACK,
             "description": "Client-side UI/UX development"},
            {"name": "REST APIs", "category": ProjectCategory.FULL_STACK,
             "description": "RESTful API design and implementation"},
            {"name": "Database Design", "category": ProjectCategory.FULL_STACK,
             "description": "SQL and NoSQL database modeling"},
            {"name": "Web Frameworks", "category": ProjectCategory.FULL_STACK,
             "description": "Django, FastAPI, Express, React, etc."},
            
            # System Design Skills
            {"name": "Distributed Systems", "category": ProjectCategory.SYSTEM_DESIGN,
             "description": "Designing scalable distributed architectures"},
            {"name": "Caching Strategies", "category": ProjectCategory.SYSTEM_DESIGN,
             "description": "Redis, Memcached, CDN caching"},
            {"name": "Message Queues", "category": ProjectCategory.SYSTEM_DESIGN,
             "description": "RabbitMQ, Kafka, async processing"},
            {"name": "Microservices", "category": ProjectCategory.SYSTEM_DESIGN,
             "description": "Microservice architecture patterns"},
            {"name": "Load Balancing", "category": ProjectCategory.SYSTEM_DESIGN,
             "description": "Traffic distribution and scaling"},
            
            # Security/Blockchain Skills
            {"name": "Authentication", "category": ProjectCategory.SECURITY_BLOCKCHAIN,
             "description": "JWT, OAuth, session management"},
            {"name": "Encryption", "category": ProjectCategory.SECURITY_BLOCKCHAIN,
             "description": "Cryptographic algorithms and implementations"},
            {"name": "Web Security", "category": ProjectCategory.SECURITY_BLOCKCHAIN,
             "description": "XSS, CSRF, SQL injection prevention"},
            {"name": "Smart Contracts", "category": ProjectCategory.SECURITY_BLOCKCHAIN,
             "description": "Ethereum, Solidity, blockchain development"},
            {"name": "Security Auditing", "category": ProjectCategory.SECURITY_BLOCKCHAIN,
             "description": "Vulnerability assessment and penetration testing"},
        ]
        
        for skill_data in default_skills:
            # Check if skill already exists
            existing = session.query(Skill).filter_by(name=skill_data["name"]).first()
            if not existing:
                skill = Skill(**skill_data)
                session.add(skill)
        
        session.commit()
        
        # Initialize Achievements
        self.initialize_achievements(session)
    
    def initialize_achievements(self, session: Session):
        """Initialize default achievements."""
        defaults = [
            # Project Counts
            {"name": "Hello World", "description": "Create your first project", "icon": "🌱", "criteria_type": "project_count", "criteria_value": 1},
            {"name": "Code Warrior", "description": "Create 5 projects", "icon": "⚔️", "criteria_type": "project_count", "criteria_value": 5},
            {"name": "Project Master", "description": "Create 10 projects", "icon": "👑", "criteria_type": "project_count", "criteria_value": 10},
            
            # Streaks (simulated by checking daily activity count in window)
            {"name": "Consistency is Key", "description": "Complete 3 days of activity", "icon": "🔥", "criteria_type": "streak", "criteria_value": 3},
            
            # Skill Levels (avg proficiency)
            {"name": "Novice Coder", "description": "Reach 20% average skill proficiency", "icon": "📘", "criteria_type": "skill_level", "criteria_value": 20},
            {"name": "Expert Engineer", "description": "Reach 80% average skill proficiency", "icon": "🚀", "criteria_type": "skill_level", "criteria_value": 80},
        ]
        
        for data in defaults:
            if not session.query(Achievement).filter_by(name=data["name"]).first():
                ach = Achievement(**data)
                session.add(ach)
        
        session.commit()
    
    def get_or_create_skill(self, session: Session, name: str, category: ProjectCategory) -> Skill:
        """
        Get existing skill or create new one.
        
        Args:
            session: Database session
            name: Skill name
            category: Skill category
            
        Returns:
            Skill: The skill object
        """
        skill = session.query(Skill).filter_by(name=name).first()
        if not skill:
            skill = Skill(name=name, category=category)
            session.add(skill)
            session.commit()
        return skill


# Singleton instance
_db_manager_instance: Optional[DatabaseManager] = None


def get_database_manager(database_url: Optional[str] = None) -> DatabaseManager:
    """
    Get the singleton DatabaseManager instance.
    
    Args:
        database_url: Database URL (only used on first call)
        
    Returns:
        DatabaseManager: The database manager instance
    """
    global _db_manager_instance
    if _db_manager_instance is None:
        if database_url is None:
            database_url = "sqlite:///data/activity_tracker.db"
        _db_manager_instance = DatabaseManager(database_url)
    return _db_manager_instance
