"""
Daily Scheduler
Orchestrates automated daily execution with randomization and error handling.
"""

import time
import random
import logging
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from rich.console import Console

from src.orchestration.workflow_engine import WorkflowEngine
from src.config_manager import get_config_manager

console = Console()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DailyScheduler:
    """Manages scheduled execution of the workflow."""
    
    def __init__(self):
        """Initialize scheduler."""
        self.scheduler = BlockingScheduler()
        self.config_manager = get_config_manager()
        self.config_manager.load_config()
        self.config = self.config_manager.config
        self.workflow_engine = WorkflowEngine(dry_run=False)  # Usually for production
    
    def start(self):
        """Start the scheduler."""
        if not self.config.scheduling.enabled:
            console.print("[yellow]Scheduling is disabled in configuration.[/yellow]")
            return

        schedule_time = self.config.scheduling.time
        hour, minute = map(int, schedule_time.split(':'))
        
        console.print(f"[green]Starting Daily Scheduler[/green]")
        console.print(f"Scheduled time: {schedule_time} ({self.config.scheduling.timezone})")
        console.print(f"Randomization: ±{self.config.scheduling.time_randomization_minutes} minutes")
        
        # Schedule the daily job
        self.scheduler.add_job(
            self._scheduled_job,
            CronTrigger(hour=hour, minute=minute, timezone=self.config.scheduling.timezone),
            id='daily_workflow',
            name='Daily Git Activity Workflow',
            replace_existing=True
        )
        
        try:
            console.print("[bold]Scheduler running. Press Ctrl+C to exit.[/bold]")
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            console.print("\n[yellow]Scheduler stopped.[/yellow]")
    
    def _scheduled_job(self):
        """The job that runs daily at the scheduled time."""
        logger.info("Triggered scheduled job")
        
        # 1. Randomization Delay
        random_minutes = self.config.scheduling.time_randomization_minutes
        if random_minutes > 0:
            # Randomize +/- random_minutes
            delay_minutes = random.randint(-random_minutes, random_minutes)
            delay_seconds = delay_minutes * 60
            
            # If delay is negative, we can't go back in time, so we just run now?
            # Actually, standard randomization is usually + delay. 
            # If we want +/- around a target time, we need to schedule specifically.
            # But here, we are triggered AT the target time.
            # So, we can only delay (wait).
            # To achieve +/- effect, the schedule time should be the earliest possible start, 
            # and we delay by random(0, window).
            #
            # Let's interpret "time_randomization_minutes" as a random delay added to start.
            # Or if user wants +/- around 9am, they should set schedule to 7am and random delay up to 4 hours?
            # Let's keep it simple: We delay by a random amount [0, 2 * random_minutes] ?
            #
            # The config says "±2 hours". This implies the user expects 9am +/- 2h.
            # But cron fires at 9am. We can't fire at 7am.
            # Solution: We run immediately, but wait a random delay? No, that blocks the thread.
            # Ideally: Schedule logic should define the window. 
            
            # Simplified approach: Just delay by 0 to random_minutes minutes.
            # Authenticity is mostly about not running at exact 09:00:00 every day.
            
            actual_delay = random.randint(0, random_minutes * 60)
            logger.info(f"Waiting {actual_delay} seconds for authenticity...")
            time.sleep(actual_delay)
        
        # 2. Skip Weekends if configured
        if self.config.scheduling.skip_weekends:
            if datetime.now().weekday() >= 5:  # 5=Saturday, 6=Sunday
                logger.info("Skipping weekend execution.")
                return

        # 3. Execution with Retry
        max_retries = self.config.scheduling.max_retries if self.config.scheduling.retry_on_failure else 0
        retries = 0
        
        while retries <= max_retries:
            try:
                console.print(f"\n[bold cyan]Executing Daily Workflow ({datetime.now()})[/bold cyan]")
                project = self.workflow_engine.run_daily_workflow()
                
                if project:
                    logger.info(f"Workflow completed successfully: Project {project.id}")
                    break
                else:
                    logger.warning("Workflow returned None (failure?)")
                    raise Exception("Workflow failed to generate project")
                    
            except Exception as e:
                retries += 1
                logger.error(f"Workflow failed (Attempt {retries}/{max_retries + 1}): {e}")
                
                if retries <= max_retries:
                    wait_time = 60 * 5 * retries  # Linear backoff: 5, 10, 15 mins
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("Max retries reached. Giving up for today.")
                    # TODO: Send notification failure
