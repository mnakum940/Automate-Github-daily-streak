"""
Configuration Manager
Handles loading, validation, and access to system configuration.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


class GitHubConfig(BaseModel):
    """GitHub configuration settings."""
    username: str
    token: str
    repository_strategy: str = Field(default="separate", pattern="^(separate|monorepo)$")
    default_visibility: str = Field(default="public", pattern="^(public|private)$")
    repository_prefix: str = "auto-"
    use_topics: bool = True
    create_issues: bool = False


class AIConfig(BaseModel):
    """AI/LLM configuration settings."""
    provider: str = Field(pattern="^(openai|ollama)$")
    model: str
    api_key: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=3000, ge=100, le=10000)
    timeout: int = Field(default=60, ge=10, le=300)


class SkillsConfig(BaseModel):
    """Skills tracking and progression configuration."""
    focus_areas: Dict[str, int]
    progression: Dict[str, Any]
    technology_preferences: Dict[str, List[str]]
    
    @validator('focus_areas')
    def validate_focus_areas_total(cls, v):
        total = sum(v.values())
        if total != 100:
            raise ValueError(f"Focus areas must sum to 100%, got {total}%")
        return v


class SchedulingConfig(BaseModel):
    """Task scheduling configuration."""
    enabled: bool = True
    time: str
    timezone: str = "Asia/Kolkata"
    time_randomization_minutes: int = Field(default=120, ge=0, le=360)
    skip_weekends: bool = False
    retry_on_failure: bool = True
    max_retries: int = Field(default=3, ge=1, le=10)


class AutomationConfig(BaseModel):
    """Automation behavior configuration."""
    mode: str = Field(pattern="^(auto|review|manual)$")
    commit_strategy: str = Field(pattern="^(single|smart|detailed)$")
    push_immediately: bool = True
    create_branch: bool = False
    auto_merge: bool = False
    delete_branch_after_merge: bool = True


class QualityConfig(BaseModel):
    """Code quality requirements configuration."""
    min_lines_of_code: int = Field(default=100, ge=10)
    require_readme: bool = True
    require_tests: bool = True
    require_documentation: bool = True
    min_documentation_coverage: int = Field(default=70, ge=0, le=100)
    code_complexity_threshold: int = Field(default=15, ge=5, le=50)
    enforce_code_style: bool = True
    run_linters: bool = True


class NotificationsConfig(BaseModel):
    """Notifications configuration."""
    enabled: bool = False
    email: Optional[str] = None
    send_daily_summary: bool = True
    send_weekly_report: bool = True
    send_on_error: bool = True
    notification_time: str = "20:00"


class DatabaseConfig(BaseModel):
    """Database configuration."""
    path: str = "data/activity_tracker.db"
    backup_enabled: bool = True
    backup_frequency: str = Field(pattern="^(daily|weekly|monthly)$")
    backup_path: str = "data/backups/"


class ProjectsConfig(BaseModel):
    """Project generation configuration."""
    output_directory: str = "generated_projects"
    keep_local_copies: bool = True
    max_simultaneous_projects: int = Field(default=1, ge=1, le=5)
    project_lifetime_days: int = Field(default=7, ge=1, le=30)


class DiversityConfig(BaseModel):
    """Project diversity configuration."""
    prevent_same_tech_consecutive: bool = True
    prevent_same_category_consecutive: bool = True
    rotation_cycle_days: int = Field(default=7, ge=3, le=30)


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR)$")
    file_path: str = "data/logs/activity_generator.log"
    console_output: bool = True
    rich_formatting: bool = True


class SystemConfig(BaseModel):
    """Complete system configuration."""
    github: GitHubConfig
    ai: AIConfig
    skills: SkillsConfig
    scheduling: SchedulingConfig
    automation: AutomationConfig
    quality: QualityConfig
    notifications: NotificationsConfig
    database: DatabaseConfig
    projects: ProjectsConfig
    diversity: DiversityConfig
    logging: LoggingConfig


class ConfigManager:
    """Manages system configuration loading and access."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = Path(config_path)
        self._config: Optional[SystemConfig] = None
        self._load_environment()
        
    def _load_environment(self):
        """Load environment variables from .env file."""
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)
    
    def _substitute_env_vars(self, data: Any) -> Any:
        """
        Recursively substitute environment variables in configuration.
        
        Args:
            data: Configuration data (dict, list, or primitive)
            
        Returns:
            Data with environment variables substituted
        """
        if isinstance(data, dict):
            return {k: self._substitute_env_vars(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._substitute_env_vars(item) for item in data]
        elif isinstance(data, str):
            # Replace ${VAR_NAME} with environment variable value
            if data.startswith("${") and data.endswith("}"):
                var_name = data[2:-1]
                return os.getenv(var_name, data)
            return data
        else:
            return data
    
    def load_config(self) -> SystemConfig:
        """
        Load and validate configuration from YAML file.
        
        Returns:
            SystemConfig: Validated system configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If configuration is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        # Load YAML file
        with open(self.config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)
        
        # Substitute environment variables
        config_data = self._substitute_env_vars(raw_config)
        
        # Special handling for GitHub username from env if not in config
        if not config_data.get('github', {}).get('username'):
            github_username = os.getenv('GITHUB_USERNAME')
            if github_username:
                config_data.setdefault('github', {})['username'] = github_username
        
        # Validate and create config object
        try:
            self._config = SystemConfig(**config_data)
            return self._config
        except Exception as e:
            raise ValueError(f"Invalid configuration: {e}")
    
    @property
    def config(self) -> SystemConfig:
        """
        Get the loaded configuration.
        
        Returns:
            SystemConfig: The system configuration
            
        Raises:
            RuntimeError: If configuration hasn't been loaded yet
        """
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        return self._config
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot-notation path.
        
        Args:
            key_path: Dot-separated path to config value (e.g., "github.username")
            default: Default value if key not found
            
        Returns:
            The configuration value or default
            
        Example:
            >>> config_manager.get("ai.model")
            "gpt-4"
        """
        try:
            value = self.config
            for key in key_path.split('.'):
                if hasattr(value, key):
                    value = getattr(value, key)
                elif isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            return value
        except Exception:
            return default
    
    def validate_required_env_vars(self) -> bool:
        """
        Validate that all required environment variables are set.
        
        Returns:
            bool: True if all required vars are set
            
        Raises:
            EnvironmentError: If required environment variables are missing
        """
        required_vars = []
        
        # Check based on configuration
        if not self.config.github.token:
            required_vars.append("GITHUB_TOKEN")
        
        if not self.config.github.username:
            required_vars.append("GITHUB_USERNAME")
        
        if self.config.ai.provider == "openai" and not self.config.ai.api_key:
            required_vars.append("OPENAI_API_KEY")
        
        if self.config.notifications.enabled and not self.config.notifications.email:
            required_vars.append("NOTIFICATION_EMAIL")
        
        if required_vars:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(required_vars)}\n"
                f"Please set them in your .env file or environment."
            )
        
        return True
    
    def create_directories(self):
        """Create necessary directories based on configuration."""
        directories = [
            self.config.database.path,
            self.config.database.backup_path,
            self.config.logging.file_path,
            self.config.projects.output_directory,
        ]
        
        for path_str in directories:
            path = Path(path_str)
            # If it's a file path, create parent directory
            if '.' in path.name:
                path.parent.mkdir(parents=True, exist_ok=True)
            else:
                path.mkdir(parents=True, exist_ok=True)


# Singleton instance
_config_manager_instance: Optional[ConfigManager] = None


def get_config_manager(config_path: str = "config.yaml") -> ConfigManager:
    """
    Get the singleton ConfigManager instance.
    
    Args:
        config_path: Path to configuration file (only used on first call)
        
    Returns:
        ConfigManager: The configuration manager instance
    """
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = ConfigManager(config_path)
    return _config_manager_instance
