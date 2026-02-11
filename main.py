"""
Main CLI Entry Point
Command-line interface for the GitHub Activity Generator System.
"""

import sys
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from datetime import datetime

from src.config_manager import get_config_manager
from src.database import get_database_manager

# Initialize CLI app and console
app = typer.Typer(
    name="GitHub Activity Generator",
    help="Automated intelligent GitHub activity generator for career growth",
    add_completion=False
)
console = Console()


@app.command()
def configure(
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", help="Interactive configuration setup")
):
    """
    Configure the system with GitHub credentials and preferences.
    """
    console.print(Panel.fit(
        "[bold cyan]GitHub Activity Generator - Configuration[/bold cyan]",
        border_style="cyan"
    ))
    
    if interactive:
        console.print("\n[yellow]Interactive configuration coming soon![/yellow]")
        console.print("For now, please edit the following files manually:\n")
        console.print("  1. [cyan].env[/cyan] - Copy from .env.example and add your credentials")
        console.print("  2. [cyan]config.yaml[/cyan] - Adjust settings as needed\n")
    
    # Check if .env exists
    env_path = Path(".env")
    if not env_path.exists():
        console.print("[yellow]Warning:[/yellow] .env file not found!")
        console.print("Creating .env from .env.example...\n")
        
        env_example = Path(".env.example")
        if env_example.exists():
            env_path.write_text(env_example.read_text())
            console.print("[green]OK[/green] Created .env file. [bold]Please edit it with your credentials![/bold]\n")
        else:
            console.print("[red]Error:[/red] .env.example not found!")
            raise typer.Exit(1)
    else:
        console.print("[green]OK[/green] .env file exists\n")
    
    # Try to load and validate config
    try:
        config_manager = get_config_manager()
        config = config_manager.load_config()
        console.print("✅ Configuration loaded successfully!\n")
        
        # Show current configuration summary
        table = Table(title="Current Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("GitHub Username", config.github.username or "[red]Not Set[/red]")
        table.add_row("Repository Strategy", config.github.repository_strategy)
        table.add_row("AI Provider", config.ai.provider)
        table.add_row("AI Model", config.ai.model)
        table.add_row("Automation Mode", config.automation.mode)
        table.add_row("Scheduling Enabled", "Yes" if config.scheduling.enabled else "No")
        table.add_row("Daily Time", config.scheduling.time)
        
        console.print(table)
        console.print()
        
        # Validate environment variables
        try:
            config_manager.validate_required_env_vars()
            console.print("[green]OK[/green] All required environment variables are set!\n")
        except EnvironmentError as e:
            console.print(f"[red]Error:[/red] {e}\n")
            raise typer.Exit(1)
        
    except FileNotFoundError:
        console.print("[red]Error:[/red] config.yaml not found!")
        raise typer.Exit(1)
    except ValueError as e:
        console.print(f"[red]Configuration Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def init():
    """
    Initialize the system database and create necessary directories.
    """
    console.print(Panel.fit(
        "[bold cyan]System Initialization[/bold cyan]",
        border_style="cyan"
    ))
    
    try:
        # Load configuration
        console.print("\n[1/4] Loading configuration...")
        config_manager = get_config_manager()
        config = config_manager.load_config()
        console.print("  [green]OK[/green] Configuration loaded\n")
        
        # Create directories
        console.print("[2/4] Creating directories...")
        config_manager.create_directories()
        console.print("  [green]OK[/green] Directories created\n")
        
        # Initialize database
        console.print("[3/4] Initializing database...")
        db_url = f"sqlite:///{config.database.path}"
        db_manager = get_database_manager(db_url)
        db_manager.create_tables()
        console.print("  [green]OK[/green] Database tables created\n")
        
        # Initialize default skills
        console.print("[4/4] Initializing default skills...")
        session = db_manager.get_session()
        try:
            db_manager.initialize_default_skills(session)
            console.print("  [green]OK[/green] Default skills initialized\n")
        finally:
            session.close()
        
        console.print(Panel.fit(
            "[bold green]System initialized successfully![/bold green]",
            border_style="green"
        ))
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  1. Run [cyan]python main.py configure[/cyan] to check your configuration")
        console.print("  2. Run [cyan]python main.py run --dry-run[/cyan] to test project generation")
        console.print("  3. Run [cyan]python main.py schedule[/cyan] to start daily automation\n")
        
    except Exception as e:
        console.print(f"\n[red]Initialization failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def run(
    dry_run: bool = typer.Option(False, "--dry-run", help="Generate locally without pushing to GitHub"),
    force: bool = typer.Option(False, "--force", help="Force execution even if already ran today")
):
    """
    Execute the daily project generation workflow immediately.
    """
    console.print(Panel.fit(
        "[bold cyan]Running Daily Workflow[/bold cyan]",
        border_style="cyan"
    ))
    
    if dry_run:
        console.print("\n[yellow]DRY RUN MODE:[/yellow] Will generate locally without pushing to GitHub\n")
    
    try:
        # Import workflow engine
        from src.orchestration.workflow_engine import WorkflowEngine
        
        # Execute workflow
        engine = WorkflowEngine(dry_run=dry_run)
        project = engine.run_daily_workflow()
        
        if project:
            console.print("[bold green]Success![/bold green] Project generated successfully.\n")
        else:
            console.print("[bold red]Failed![/bold red] Project generation failed.\n")
            raise typer.Exit(1)
    
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def schedule(
    time: str = typer.Option(None, "--time", "-t", help="Time to run daily (HH:MM)"),
    randomization: int = typer.Option(None, "--random", "-r", help="Randomization in minutes")
):
    """
    Start the daily project generation scheduler.
    """
    console.print(Panel.fit(
        "[bold cyan]Daily Scheduler[/bold cyan]",
        border_style="cyan"
    ))
    
    try:
        from src.automation.scheduler import DailyScheduler
        
        scheduler = DailyScheduler()
        
        # Override config if CLI args provided
        if time:
            scheduler.config.scheduling.time = time
        if randomization is not None:
            scheduler.config.scheduling.time_randomization_minutes = randomization
            
        scheduler.start()
        
    except Exception as e:
        console.print(f"\n[red]Scheduler Failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def status():
    """
    Display current system status and statistics.
    """
    console.print(Panel.fit(
        "[bold cyan]System Status[/bold cyan]",
        border_style="cyan"
    ))
    
    try:
        # Load config
        config_manager = get_config_manager()
        config = config_manager.load_config()
        
        # Connect to database
        db_url = f"sqlite:///{config.database.path}"
        db_manager = get_database_manager(db_url)
        session = db_manager.get_session()
        
        try:
            from src.database import Project, Skill, Commit, DailyActivity, ProjectStatus, Achievement
            
            # Get statistics
            total_projects = session.query(Project).count()
            completed_projects = session.query(Project).filter(
                Project.status == ProjectStatus.COMPLETED
            ).count()
            total_commits = session.query(Commit).count()
            total_skills = session.query(Skill).count()
            
            # Get activity streak
            activities = session.query(DailyActivity).order_by(
                DailyActivity.date.desc()
            ).limit(30).all()
            
            # Create statistics table
            stats_table = Table(title="Statistics", show_header=False)
            stats_table.add_column("Metric", style="cyan")
            stats_table.add_column("Value", style="green", justify="right")
            
            stats_table.add_row("Total Projects", str(total_projects))
            stats_table.add_row("Completed Projects", str(completed_projects))
            stats_table.add_row("Total Commits", str(total_commits))
            stats_table.add_row("Skills Tracked", str(total_skills))
            stats_table.add_row("Activity Days", str(len(activities)))
            
            console.print("\n", stats_table, "\n")
            
            # Show top skills
            top_skills = session.query(Skill).order_by(
                Skill.proficiency.desc()
            ).limit(5).all()
            
            if top_skills:
                skills_table = Table(title="Top Skills", show_lines=True)
                skills_table.add_column("Skill", style="cyan")
                skills_table.add_column("Category", style="yellow")
                skills_table.add_column("Proficiency", justify="right")
                
                for skill in top_skills:
                    proficiency_bar = "#" * int(skill.proficiency / 10) + "-" * (10 - int(skill.proficiency / 10))
                    skills_table.add_row(
                        skill.name,
                        skill.category.value.replace("_", " ").title(),
                        f"{proficiency_bar} {skill.proficiency:.1f}%"
                    )
                
                console.print(skills_table, "\n")
            
            # Show recent projects
            recent_projects = session.query(Project).order_by(
                Project.created_at.desc()
            ).limit(5).all()
            
            if recent_projects:
                projects_table = Table(title="Recent Projects")
                projects_table.add_column("Title", style="cyan")
                projects_table.add_column("Category", style="yellow")
                projects_table.add_column("Difficulty", style="magenta")
                projects_table.add_column("Status")
                
                for project in recent_projects:
                    status_color = {
                        ProjectStatus.COMPLETED: "green",
                        ProjectStatus.IN_PROGRESS: "yellow",
                        ProjectStatus.PLANNED: "blue",
                        ProjectStatus.FAILED: "red"
                    }.get(project.status, "white")
                    
                    projects_table.add_row(
                        project.title[:40],
                        project.category.value.replace("_", " ").title(),
                        project.difficulty.value.title(),
                        f"[{status_color}]{project.status.value.title()}[/{status_color}]"
                    )
                
                console.print(projects_table, "\n")
            
        finally:
            session.close()
            
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        console.print("\nHave you run [cyan]python main.py init[/cyan] yet?\n")
        raise typer.Exit(1)


@app.command()
def dashboard():
    """
    Display an interactive dashboard with visualizations.
    """
    console.print(Panel.fit(
        "[bold cyan]Interactive Dashboard[/bold cyan]",
        border_style="cyan"
    ))
    
    try:
        from src.tracking.dashboard import Dashboard
        
        dashboard = Dashboard()
        # In a real interactive app, we might use a loop or Live display
        # For now, just render once
        dashboard.render()
        
    except Exception as e:
        console.print(f"\n[red]Dashboard Failed:[/red] {e}")
        console.print("\nHave you run [cyan]python main.py init[/cyan] yet?\n")
        raise typer.Exit(1)


@app.command()
def resume():
    """
    Generate a professional resume based on your projects and skills.
    """
    console.print(Panel.fit(
        "[bold cyan]Interactive Resume Generator[/bold cyan]",
        border_style="cyan"
    ))
    
    try:
        # Load config
        config_manager = get_config_manager()
        config = config_manager.load_config()
        
        # Connect to database
        db_url = f"sqlite:///{config.database.path}"
        db_manager = get_database_manager(db_url)
        session = db_manager.get_session()
        
        try:
            from src.reporting.resume_generator import ResumeGenerator
            
            generator = ResumeGenerator(session, config)
            output_path = generator.generate_resume()
            
            console.print(f"\n[green]Success![/green] Resume generated at:")
            console.print(f"[bold]{output_path}[/bold]")
            
        finally:
            session.close()
            
    except Exception as e:
        console.print(f"\n[red]Resume Generation Failed:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def reset(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt")
):
    """
    Reset the database (WARNING: Deletes all data!).
    """
    if not confirm:
        console.print("[bold red]WARNING:[/bold red] This will delete ALL data in the database!")
        confirm_input = typer.confirm("Are you sure you want to continue?")
        if not confirm_input:
            console.print("Aborted.")
            raise typer.Exit(0)
    
    try:
        config_manager = get_config_manager()
        config = config_manager.load_config()
        
        db_url = f"sqlite:///{config.database.path}"
        db_manager = get_database_manager(db_url)
        
        console.print("\nDropping all tables...")
        db_manager.drop_tables()
        console.print("[green]OK[/green] Database reset complete\n")
        console.print("Run [cyan]python main.py init[/cyan] to reinitialize the database.\n")
        
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        raise typer.Exit(1)


def version_callback(value: bool):
    """Show version information."""
    if value:
        from src import __version__
        console.print(f"GitHub Activity Generator v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit"
    )
):
    """
    GitHub Activity Generator - Intelligent automated project creation for career growth.
    """
    pass


if __name__ == "__main__":
    app()
