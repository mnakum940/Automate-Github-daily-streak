"""
Dashboard Visualization
Renders interactive CLI dashboard using Rich.
"""

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.progress import BarColumn, Progress, TextColumn
from rich.text import Text
from rich import box
from datetime import datetime

from src.tracking.analytics import AnalyticsEngine
from src.database import get_database_manager
from src.config_manager import get_config_manager

console = Console()

class Dashboard:
    """CLI Dashboard renderer."""
    
    def __init__(self):
        config_manager = get_config_manager()
        config = config_manager.load_config()
        
        db_url = f"sqlite:///{config.database.path}"
        db_manager = get_database_manager(db_url)
        self.session = db_manager.get_session()
        self.analytics = AnalyticsEngine(self.session)
        
    def render(self):
        """Render the full dashboard."""
        layout = Layout()
        
        # Split layout
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=1)
        )
        
        layout["left"].split_column(
            Layout(name="stats", size=10),
            Layout(name="skills")
        )
        
        layout["right"].split_column(
            Layout(name="activity"),
            Layout(name="tech", size=10)
        )
        
        # Header
        current_time = datetime.now().strftime("%A, %d %B %Y | %H:%M")
        layout["header"].update(
            Panel(
                f"[bold white]GitHub Activity Generator[/bold white] [cyan]v1.0.0[/cyan]\n[dim]{current_time}[/dim]",
                style="on blue",
                box=box.HEAVY
            )
        )
        
        # Stats
        stats = self.analytics.get_total_stats()
        stats_table = Table.grid(expand=True, padding=(1, 2))
        stats_table.add_column("Metric", justify="center")
        stats_table.add_column("Value", justify="center")
        stats_table.add_column("Metric", justify="center")
        stats_table.add_column("Value", justify="center")
        
        stats_table.add_row(
            "[cyan]Total Projects[/cyan]", f"[bold]{stats['projects']}[/]",
            "[cyan]Completed[/cyan]", f"[bold green]{stats['completed']}[/]"
        )
        stats_table.add_row(
            "[cyan]Total Commits[/cyan]", f"[bold]{stats['commits']}[/]",
            "[cyan]Skills Tracked[/cyan]", f"[bold]{stats['skills']}[/]"
        )
        
        portfolio_score = self.analytics.calculate_portfolio_score()
        score_color = "green" if portfolio_score > 70 else "yellow" if portfolio_score > 40 else "red"
        stats_table.add_row(
            "[cyan]Portfolio Score[/cyan]", f"[bold {score_color}]{portfolio_score}[/]",
            "", ""
        )
        
        activity_streak = self.analytics.calculate_streak()
        streak_color = "green" if activity_streak > 0 else "red"
        
        layout["left"]["stats"].update(
            Panel(
                stats_table,
                title=f"[bold]Overview (Streak: [{streak_color}]{activity_streak} days[/{streak_color}])[/]",
                border_style="cyan"
            )
        )
        
        # Skills
        skills = self.analytics.get_skill_proficiency()
        skill_table = Table(box=box.SIMPLE, expand=True, show_header=False)
        skill_table.add_column("Name", ratio=3)
        skill_table.add_column("Bar", ratio=4)
        skill_table.add_column("Pct", ratio=1, justify="right")
        
        for skill in skills[:15]:  # Show top 15
            bar = self._make_progress_bar(skill.proficiency)
            skill_table.add_row(
                skill.name,
                bar,
                f"{skill.proficiency:.1f}%"
            )
            
        layout["left"]["skills"].update(
            Panel(
                skill_table,
                title="[bold]Skill Proficiency[/]",
                border_style="green"
            )
        )
        
        # Recent Activity
        activities = self.analytics.get_activity_history(days=10)
        activity_text = Text()
        if not activities:
            activity_text.append("No recent activity.", style="dim")
        else:
            for act in activities:
                date_str = act.date.strftime("%Y-%m-%d")
                status = "[green]OK[/]" if act.projects_completed > 0 else "[red]-[/]"
                activity_text.append(f"{date_str} {status} - {act.projects_completed} projects, {act.commits_made} commits\n")
        
        layout["right"]["activity"].update(
            Panel(
                activity_text,
                title="[bold]Recent Activity[/]",
                border_style="magenta"
            )
        )
        
        # Top Tech
        techs = self.analytics.get_top_technologies()
        tech_text = Text()
        for t, count in techs:
            tech_text.append(f"{t}: {count}  ", style="yellow")
            
        
        # Achievements
        from src.database import Achievement
        achievements = self.session.query(Achievement).filter_by(is_unlocked=True).order_by(Achievement.unlocked_at.desc()).limit(5).all()
        
        ach_text = Text()
        if not achievements:
            ach_text.append("No achievements unlocked yet. Keep coding!", style="dim")
        else:
            for ach in achievements:
                ach_text.append(f"{ach.icon} {ach.name}\n", style="bold gold1")
                ach_text.append(f"   {ach.description}\n", style="dim")
        
        layout["right"]["tech"].split_column(
            Layout(name="tech_list", ratio=2),
            Layout(name="achievements", ratio=3)
        )
        
        layout["right"]["tech"]["tech_list"].update(
            Panel(
                tech_text,
                title="[bold]Top Technologies[/]",
                border_style="yellow"
            )
        )
        
        layout["right"]["tech"]["achievements"].update(
            Panel(
                ach_text,
                title="[bold]Achievements 🏆[/]",
                border_style="gold1"
            )
        )
        
        # Footer
        layout["footer"].update(
            Panel(
                Text("Press Ctrl+C to exit", justify="center", style="dim"),
                box=box.SIMPLE
            )
        )
        
        console.print(layout)
        
    def _make_progress_bar(self, percentage: float) -> str:
        """Create a text-based progress bar."""
        width = 20
        filled = int(width * (percentage / 100))
        bar = "#" * filled + "-" * (width - filled)
        color = "red"
        if percentage > 30: color = "yellow"
        if percentage > 70: color = "green"
        return f"[{color}]{bar}[/{color}]"
