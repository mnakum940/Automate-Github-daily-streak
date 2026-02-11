"""
Workflow Engine
Orchestrates the daily project generation workflow.
"""

from typing import Optional
from pathlib import Path
from sqlalchemy.orm import Session
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import datetime

from src.config_manager import get_config_manager
from src.database import get_database_manager, Project, ProjectStatus, Skill, DailyActivity
from src.planning.project_planner import ProjectPlanner
from src.generation.code_generator import CodeGenerator
from src.generation.doc_generator import DocGenerator
from src.automation.git_manager import GitManager
from src.planning.skill_mapper import SkillMapper


console = Console()


class WorkflowEngine:
    """Orchestrates the end-to-end project generation workflow."""
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize workflow engine.
        
        Args:
            dry_run: If True, generate locally without pushing to GitHub
        """
        self.dry_run = dry_run
        
        # Load configuration
        self.config_manager = get_config_manager()
        self.config_manager.load_config()  # Ensure config is loaded
        self.config = self.config_manager.config
        
        # Initialize database
        db_url = f"sqlite:///{self.config.database.path}"
        self.db_manager = get_database_manager(db_url)
        self.session = self.db_manager.get_session()
        
        # Initialize components (after config is loaded)
        from src.generation.ai_provider import AIClient, AIProvider
        
        # Initialize AI client globally before other components use it
        if not hasattr(self, '_ai_initialized'):
            provider_type = AIProvider(self.config.ai.provider)
            kwargs = {'model': self.config.ai.model}
            
            if provider_type == AIProvider.OPENAI:
                kwargs['api_key'] = self.config.ai.api_key
            
            ai_client = AIClient(provider_type, **kwargs)
            
            # Store in global singleton
            from src.generation import ai_provider
            ai_provider._ai_client_instance = ai_client
            self._ai_initialized = True
        
        self.project_planner = ProjectPlanner(self.session, self.config)
        self.code_generator = CodeGenerator(self.config)
        self.doc_generator = DocGenerator(self.config)
        self.git_manager = GitManager(self.config)
        self.skill_mapper = SkillMapper(self.session)
    
    def run_daily_workflow(self) -> Optional[Project]:
        """
        Execute the complete daily workflow.
        
        Returns:
            Created Project object if successful, None otherwise
        """
        try:
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                # Step 1: Generate project idea
                task1 = progress.add_task("Analyzing skill gaps and generating project idea...", total=None)
                project_brief = self.project_planner.generate_project_idea()
                progress.update(task1, completed=True)
                
                console.print(f"\n[green]Generated Idea:[/green] {project_brief.title}")
                console.print(f"[cyan]Category:[/cyan] {project_brief.category.value.title()}")
                console.print(f"[cyan]Difficulty:[/cyan] {project_brief.difficulty.value.title()}")
                console.print(f"[cyan]Technologies:[/cyan] {', '.join(project_brief.technologies[:3])}")
                console.print()
                
                # Step 2: Validate novelty
                task2 = progress.add_task("Validating project novelty...", total=None)
                is_novel = self.project_planner.validate_project_novelty(project_brief)
                progress.update(task2, completed=True)
                
                if not is_novel:
                    console.print("[yellow]Warning:[/yellow] Similar project exists, but continuing...")
                
                # Step 3: Create project record
                task3 = progress.add_task("Creating project record in database...", total=None)
                project = self.project_planner.create_project_record(project_brief)
                project.status = ProjectStatus.IN_PROGRESS
                self.session.commit()
                progress.update(task3, completed=True)
                
                # Step 4: Generate code
                task4 = progress.add_task("Generating project code with AI...", total=None)
                project_dir = self.code_generator.generate_project(project_brief, project)
                self.session.commit()
                progress.update(task4, completed=True)
                
                console.print(f"\n[green]Project generated at:[/green] {project_dir}")
                console.print(f"[cyan]Files created:[/cyan] {len(project.file_structure)}")
                console.print(f"[cyan]Lines of code:[/cyan] {project.lines_of_code}")
                console.print()
                
                # Step 5: Generate documentation
                task5 = progress.add_task("Generating documentation...", total=None)
                self.doc_generator.generate_documentation(project_dir, project_brief)
                project.has_readme = True
                project.documentation_coverage = 100.0  # Simulated
                progress.update(task5, completed=True)
                
                # Step 6: Generate commit messages
                task6 = progress.add_task("Generating semantic commit messages...", total=None)
                commit_messages = self.doc_generator.generate_commit_messages(project_brief)
                progress.update(task6, completed=True)
                
                # Step 7: Git operations
                task7 = progress.add_task("Performing Git operations...", total=None)
                
                # Initialize local repo
                repo = self.git_manager.initialize_repo(project_dir, project)
                
                # Create commits locally
                commits = self.git_manager.create_commits(repo, project_dir, commit_messages, project)
                for commit in commits:
                    self.session.add(commit)
                self.session.commit()
                
                # Remote operations (if not dry run)
                if not self.dry_run:
                    # Ensure unique repository name
                    import time
                    base_repo_name = project.repository_name or project.title.lower().replace(" ", "-").replace("_", "-")
                    
                    # Prevent duplicate repo name errors in DB
                    timestamp = int(time.time())
                    project.repository_name = f"{base_repo_name}-{timestamp}"
                    
                    should_push = False
                    mode = self.config.automation.mode
                    
                    if mode == "auto":
                        should_push = True
                    elif mode == "review" or mode == "manual":
                        # If running interactively, ask for confirmation
                        # Check if we are in a TTY/interactive session (simplified assumption: if using Console)
                        # But for scheduler, we can't ask.
                        # We'll assume if called from main.py run, it is interactive.
                        # If called from scheduler, it might not be.
                        # For now, let's use rich Prompt. If not interactive, it might fail or default.
                        
                        # We will only prompt if we are NOT in a scheduled job context.
                        # How to know? We can pass a flag to run_daily_workflow.
                        pass  # handled below
                    
                    # Logic for pushing
                    perform_push = False
                    if mode == "auto":
                        perform_push = True
                    else:
                        # Interactive confirmation
                        from rich.prompt import Confirm
                        console.print(f"\n[bold yellow]Review Mode ({mode}):[/bold yellow] Project generated at {project_dir}")
                        if Confirm.ask("Push this project to GitHub now?"):
                            perform_push = True
                        else:
                            console.print("[yellow]Push skipped. You can push manually later.[/yellow]")
                    
                    if perform_push:
                        remote_url = self.git_manager.create_remote_repo(project)
                        if remote_url:
                            project.repository_url = remote_url
                            self.git_manager.push_to_remote(repo, remote_url)
                            project.is_private = self.config.github.default_visibility == "private"
                            project.repository_name = remote_url.split('/')[-1].replace('.git', '')
                
                progress.update(task7, completed=True)
                
                # Step 8: Update skills
                task8 = progress.add_task("Updating skill proficiency...", total=None)
                self._update_skills(project, project_brief)
                progress.update(task8, completed=True)
                
                # Step 9: Mark project as completed
                project.status = ProjectStatus.COMPLETED
                project.completed_at = datetime.utcnow()
                project.code_quality_score = 75.0  # Simulated
                self.session.commit()
                
                # Step 10: Log daily activity
                self._log_daily_activity(project)
                
                # Step 11: Check Achievements
                self._check_achievements(project)
                
                console.print("[bold green]Workflow completed successfully![/bold green]")
                console.print(f"\n[bold]Project ID:[/bold] {project.id}")
                console.print(f"[bold]Location:[/bold] {project_dir}")
                
                if not self.dry_run and project.repository_url:
                    console.print(f"[bold]GitHub:[/bold] {project.repository_url}")
                
                console.print(f"\n[bold]Commits Created:[/bold]")
                for i, commit in enumerate(commits, 1):
                    console.print(f"  {i}. {commit.commit_message}")
                console.print()
                
                if self.dry_run:
                    console.print("[yellow]DRY RUN:[/yellow] Project generated locally. No GitHub push performed.\n")
                
                return project
        
        except Exception as e:
            console.print(f"\n[red]Workflow failed:[/red] {e}")
            console.print(f"[red]Error details:[/red] {str(e)}")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            return None
        
        finally:
            self.session.close()
    
    def _update_skills(self, project: Project, project_brief):
        """Update skill proficiencies based on project completion."""
        for skill_name in project_brief.skills:
            skill = (
                self.session.query(Skill)
                .filter(Skill.name == skill_name)
                .first()
            )
            
            if skill:
                self.skill_mapper.update_skill_proficiency(
                    skill,
                    project_brief.difficulty,
                    contribution_weight=1.0
                )
        
        self.session.commit()
    
    def _check_achievements(self, project: Project):
        """Check and unlock achievements."""
        from src.database import Achievement
        
        # 1. Project Count Achievements
        project_count = self.session.query(Project).count()
        
        achievements = self.session.query(Achievement).filter_by(
            is_unlocked=False, 
            criteria_type='project_count'
        ).all()
        
        for ach in achievements:
            if project_count >= ach.criteria_value:
                self._unlock_achievement(ach)
        
        # 2. Skill Level Achievements
        # Calculate average proficiency
        avg_proficiency = 0
        skills = self.session.query(Skill).all()
        if skills:
            avg_proficiency = sum(s.proficiency for s in skills) / len(skills)
            
        achievements = self.session.query(Achievement).filter_by(
            is_unlocked=False, 
            criteria_type='skill_level'
        ).all()
        
        for ach in achievements:
            if avg_proficiency >= ach.criteria_value:
                self._unlock_achievement(ach)

    def _unlock_achievement(self, achievement):
        """Unlock an achievement and notify."""
        achievement.is_unlocked = True
        achievement.unlocked_at = datetime.utcnow()
        self.session.commit()
        
        console.print(f"\n[bold yellow]🏆 Achievement Unlocked: {achievement.name}[/bold yellow]")
        console.print(f"[yellow]{achievement.icon} {achievement.description}[/yellow]\n")
    
    def _log_daily_activity(self, project: Project):
        """Log activity for today."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get or create today's activity record
        activity = (
            self.session.query(DailyActivity)
            .filter(DailyActivity.date == today)
            .first()
        )
        
        if not activity:
            activity = DailyActivity(
                date=today,
                projects_created=0,
                projects_completed=0,
                commits_made=0,
                lines_added=0,
                skills_practiced=[],
                technologies_used=[],
                execution_successful=True
            )
            self.session.add(activity)
        
        # Update activity
        activity.projects_created += 1
        activity.projects_completed += 1
        activity.lines_added += project.lines_of_code
        activity.execution_successful = True
        
        # Add technologies
        if project.technologies:
            existing_techs = set(activity.technologies_used or [])
            existing_techs.update(project.technologies)
            activity.technologies_used = list(existing_techs)
        
        self.session.commit()
