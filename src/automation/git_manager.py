"""
Git Automation Manager
Handles local Git operations and GitHub remote integration.
"""

import os
import random
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import git
from github import Github, GithubException
from rich.console import Console

from src.database import Project, Commit

console = Console()

class GitManager:
    """Manages Git repositories and GitHub interactions."""
    
    def __init__(self, config):
        """
        Initialize Git manager.
        
        Args:
            config: System configuration
        """
        self.config = config
        self.github_client = None
        
        if config.github.token and config.github.token != "${GITHUB_TOKEN}":
            self.github_client = Github(config.github.token)
    
    def initialize_repo(self, project_dir: Path, project: Project) -> git.Repo:
        """
        Initialize a new local Git repository.
        
        Args:
            project_dir: Path to project directory
            project: Project metadata
            
        Returns:
            git.Repo object
        """
        try:
            repo = git.Repo.init(project_dir)
            
            # Configure user for this repo
            with repo.config_writer() as git_config:
                git_config.set_value("user", "name", self.config.github.username)
                # We assume email is configured globally or not strictly needed for auth if using token
                # But good practice to set it if known. For now, rely on global config or omitted.
            
            # Create .gitignore if it doesn't exist (CodeGenerator should have created it, but double check)
            if not (project_dir / ".gitignore").exists():
                (project_dir / ".gitignore").write_text("__pycache__/\n*.pyc\nvenv/\n.env\n.DS_Store")
            
            return repo
        except Exception as e:
            console.print(f"[red]Failed to initialize Git repo:[/red] {e}")
            raise

    def create_commits(self, repo: git.Repo, project_dir: Path, commits_plan: List[str], project: Project) -> List[Commit]:
        """
        Create commits based on the plan.
        
        Args:
            repo: Git repo object
            project_dir: Path to project directory
            commits_plan: List of commit messages
            project: Project database object
            
        Returns:
            List of created Commit objects (not yet saved to DB)
        """
        created_commits = []
        
        # Stage all files
        repo.git.add(A=True)
        
        # If we have multiple commits planned, we might want to simulate progressive work.
        # However, since CodeGenerator creates all files at once, we can't easily split "real" file states.
        # Strategy:
        # 1. Verification/Setup commit: .gitignore, README, config files
        # 2. Implementation commit: Source code
        # 3. Tests/Docs commit: Tests and other docs
        #
        # For simplicity in this version, we will create empty commits or just one big commit 
        # split logically if we could, but 'git add' adds everything.
        # 
        # Better approach for authenticity: 
        # We will create ONE main commit with the actual code, 
        # but if we want multiple, we'd need to stage specific files.
        #
        # Let's try to be smart:
        # Commit 1: Config & Docs (README, requirements, .gitignore)
        # Commit 2: Code (src/, main.py)
        # Commit 3: Tests (tests/)
        
        files_to_commit = [f for f in project_dir.rglob("*") if f.is_file() and not f.name.startswith(".git")]
        
        # Reset everything first to stage selectively
        repo.git.reset()
        
        # Categorize files
        config_docs = []
        source_code = []
        tests = []
        
        for file_path in files_to_commit:
            rel_path = file_path.relative_to(project_dir)
            path_str = str(rel_path).lower()
            
            if "test" in path_str:
                tests.append(str(rel_path))
            elif any(x in path_str for x in ["readme", "requirements", "license", "config", ".gitignore", "changelog"]):
                config_docs.append(str(rel_path))
            else:
                source_code.append(str(rel_path))
        
        commit_groups = []
        
        if self.config.automation.commit_strategy == "detailed":
            # Detailed strategy: Break down into more granular commits
            
            # Group 1: Config & Structure
            if config_docs:
                commit_groups.append({
                    "files": config_docs,
                    "msg": next((m for m in commits_plan if "chore" in m or "init" in m), "chore: initial project structure")
                })
            
            # Group 2: Core Logic (Split source code)
            if source_code:
                # Split source code into two commits if possible
                mid = len(source_code) // 2
                if mid > 0:
                    commit_groups.append({
                        "files": source_code[:mid],
                        "msg": next((m for m in commits_plan if "feat" in m), "feat: implement core functionality")
                    })
                    commit_groups.append({
                        "files": source_code[mid:],
                        "msg": next((m for m in commits_plan if "refactor" in m or "fix" in m), "refactor: optimize implementation")
                    })
                else:
                    commit_groups.append({
                        "files": source_code,
                        "msg": next((m for m in commits_plan if "feat" in m), "feat: implement core functionality")
                    })
                
            # Group 3: Tests
            if tests:
                commit_groups.append({
                    "files": tests,
                    "msg": next((m for m in commits_plan if "test" in m), "test: add unit tests")
                })

        else:
            # Smart/Single Strategy (Default)
            # Group 1: Config & Docs
            if config_docs:
                commit_groups.append({
                    "files": config_docs,
                    "msg": next((m for m in commits_plan if "chore" in m or "init" in m), "chore: initial project structure")
                })
                
            # Group 2: Source Code
            if source_code:
                commit_groups.append({
                    "files": source_code,
                    "msg": next((m for m in commits_plan if "feat" in m), "feat: implement core functionality")
                })
                
            # Group 3: Tests
            if tests:
                commit_groups.append({
                    "files": tests,
                    "msg": next((m for m in commits_plan if "test" in m), "test: add unit tests")
                })
            
        # Execute commits
        for group in commit_groups:
            if not group["files"]:
                continue
                
            for f in group["files"]:
                repo.git.add(f)
            
            # Commit
            try:
                # Add time jitter? For now, nice and simple.
                repo.index.commit(group["msg"])
                head_commit = repo.head.commit
                
                # Record commit object
                db_commit = Commit(
                    project_id=project.id,
                    commit_hash=head_commit.hexsha,
                    commit_message=group["msg"],
                    commit_type=group["msg"].split(':')[0] if ':' in group["msg"] else "other",
                    files_changed=group["files"],
                    additions=stats_for_files(project_dir, group["files"]),  # Simplified
                    author_name=self.config.github.username,
                    committed_at=datetime.utcnow()
                )
                created_commits.append(db_commit)
                
            except Exception as e:
                console.print(f"[yellow]Warning during commit:[/yellow] {e}")
        
        return created_commits

    def create_remote_repo(self, project: Project) -> Optional[str]:
        """
        Create a remote GitHub repository.
        
        Args:
            project: Project data
            
        Returns:
            Clone URL of the new repo, or None if failed
        """
        if not self.github_client:
            console.print("[yellow]GitHub token not configured. Skipping remote creation.[/yellow]")
            return None
            
        try:
            user = self.github_client.get_user()
            
            # Sanitize name
            repo_name = project.title.lower().replace(" ", "-").replace("_", "-")
            
            # Check if exists (optional, create_repo might fail)
            # We'll just try to create it
            
            repo = user.create_repo(
                name=repo_name,
                description=project.description,
                private=project.is_private,
                has_issues=True,
                has_wiki=False,
                has_projects=False
            )
            
            console.print(f"[green]Created remote repository:[/green] {repo.html_url}")
            return repo.clone_url
            
        except GithubException as e:
            if e.status == 422: # Already exists
                console.print(f"[yellow]Repository {project.title} already exists on GitHub.[/yellow]")
                # Try to get the existing URL? 
                # For now return None to avoid overwriting or errors
                return None
            else:
                console.print(f"[red]GitHub API Error:[/red] {e}")
                raise

    def push_to_remote(self, repo: git.Repo, remote_url: str):
        """
        Push local changes to remote.
        
        Args:
            repo: Local git repo
            remote_url: Remote URL
        """
        try:
            # Check if remote exists
            if "origin" in [r.name for r in repo.remotes]:
                origin = repo.remote("origin")
                origin.set_url(remote_url)
            else:
                origin = repo.create_remote("origin", remote_url)
            
            # Push
            # Note: This might require auth based on the URL format
            # If using HTTPS with token, URL should be https://<token>@github.com/...
            
            if "https://" in remote_url and "@" not in remote_url and self.config.github.token:
                auth_url = remote_url.replace("https://", f"https://{self.config.github.token}@")
                origin.set_url(auth_url)
                
            origin.push(refspec="master:master") # or main:main
            # Handle default branch naming (main vs master)
            # Usually 'master' in gitpython default init, but let's check
            
            current_branch = repo.active_branch.name
            origin.push(refspec=f"{current_branch}:{current_branch}")
            
            console.print("[green]Successfully pushed to GitHub![/green]")
            
        except Exception as e:
            console.print(f"[red]Failed to push to remote:[/red] {e}")
            raise


def stats_for_files(base_path: Path, files: List[str]) -> int:
    """Estimate lines of code for stats."""
    count = 0
    for f in files:
        try:
            count += len((base_path / f).read_text(encoding='utf-8', errors='ignore').splitlines())
        except:
            pass
    return count
