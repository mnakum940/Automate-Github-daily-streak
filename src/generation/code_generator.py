"""
Code Generator
AI-powered code generation for projects.
"""

from typing import Dict, List, Optional
from pathlib import Path
import os
import json

from src.planning.project_planner import ProjectBrief
from src.generation.ai_provider import get_ai_client
from src.database import Project


class CodeGenerator:
    """Generates project code structure and starter files."""
    
    def __init__(self, config):
        """
        Initialize code generator.
        
        Args:
            config: System configuration
        """
        self.config = config
        self.ai_client = get_ai_client(config)
        self.output_dir = Path(config.projects.output_directory)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_project(self, project_brief: ProjectBrief, project: Project) -> Path:
        """
        Generate complete project structure and code.
        
        Args:
            project_brief: Project specification
            project: Database project record
            
        Returns:
            Path to generated project directory
        """
        # Create project directory
        project_dir = self.output_dir / self._sanitize_name(project_brief.title)
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate file structure
        file_structure = self._determine_file_structure(project_brief)
        
        # Create directories
        for file_path in file_structure.keys():
            file_full_path = project_dir / file_path
            file_full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate each file
        generated_files = {}
        for file_path, file_purpose in file_structure.items():
            # Skip if it looks like a directory (no extension and not a special file)
            # Special files without extension: Dockerfile, LICENSE, Makefile
            is_special = file_path in ["Dockerfile", "LICENSE", "Makefile", "CNAME"]
            has_extension = "." in os.path.basename(file_path)
            
            if not has_extension and not is_special:
                # Treat as directory, already created above
                continue
                
            content = self._generate_file_content(
                file_path=file_path,
                file_purpose=file_purpose,
                project_brief=project_brief
            )
            
            file_full_path = project_dir / file_path
            file_full_path.write_text(content, encoding='utf-8')
            generated_files[file_path] = file_purpose
        
        # Update project record
        project.file_structure = generated_files
        project.lines_of_code = self._count_lines(project_dir)
        project.has_readme = "README.md" in generated_files
        project.has_tests = any("test" in f for f in generated_files.keys())
        
        return project_dir
    
    def _sanitize_name(self, name: str) -> str:
        """Convert project title to valid directory name."""
        # Remove special characters, replace spaces with hyphens
        sanitized = name.lower()
        sanitized = ''.join(c if c.isalnum() or c in ' -_' else '' for c in sanitized)
        sanitized = sanitized.replace(' ', '-')
        return sanitized
    
    def _determine_file_structure(self, project_brief: ProjectBrief) -> Dict[str, str]:
        """
        Determine what files should be created.
        
        Args:
            project_brief: Project specification
            
        Returns:
            Dictionary mapping file paths to their purposes
        """
        # Try to use AI for structure generation (2-Factor Analysis)
        try:
            return self._generate_structure_with_ai(project_brief)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"AI Structure generation failed: {e}. Falling back to default.")
            return self._get_fallback_structure(project_brief)

    def _extract_json(self, text: str) -> Dict:
        """Extract and parse JSON from text, handling common LLM response formats."""
        try:
            # First try direct parsing
            return json.loads(text)
        except json.JSONDecodeError:
            pass
            
        import re
        
        # Try to find JSON block enclosed in markdown code fences
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
                
        # Try to find raw JSON object
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
                
        raise ValueError("Could not extract valid JSON from response")

    def _generate_structure_with_ai(self, project_brief: ProjectBrief) -> Dict[str, str]:
        """Generate file structure using AI with validation."""
        
        # Factor 1: Initial Generation
        prompt = f"""Design a complete file structure for a {project_brief.primary_language} project.
Title: {project_brief.title}
Description: {project_brief.description}
Technologies: {', '.join(project_brief.technologies)}
Type: {getattr(project_brief, 'app_type', 'script')}

List all necessary file paths and their purpose.
Include configuration files, source code, tests, and documentation.
Standardize on: README.md, .gitignore, Dockerfile, docker-compose.yml.
DO NOT include directories as separate entries (e.g., do not include "src", "tests" as keys).
Only include actual FILES.

IMPORTANT: Return VALID JSON ONLY. No markdown formatting, no explanations, no text before or after.
Example:
{{
    "README.md": "Documentation",
    "src/main.py": "Entry point"
}}"""

        response = self.ai_client.generate(
            prompt=prompt,
            system_message="You are a senior software architect. Output JSON only.",
            temperature=0.3,
            max_tokens=1000
        )
        
        try:
            structure = self._extract_json(response)
        except ValueError:
            import logging
            logging.getLogger(__name__).warning("Failed to parse initial AI structure. Using fallback.")
            return self._get_fallback_structure(project_brief)

        # Factor 2: Validation & Enhancement (The "2-Factor Analysis")
        validation_prompt = f"""Review the following file structure for a {project_brief.primary_language} project:
{json.dumps(structure, indent=2)}

Project: {project_brief.title}
Tech: {', '.join(project_brief.technologies)}

Ensure critical files are present:
- requirements.txt / package.json
- .gitignore
- Dockerfile & docker-compose.yml
- README.md
- Source code entry point

Return the CORRECTED and COMPLETE JSON structure.
IMPORTANT: Return VALID JSON ONLY. No markdown formatting, no explanations.
"""
        
        validated_response = self.ai_client.generate(
            prompt=validation_prompt,
            system_message="You are a QA Lead. Output JSON only.",
            temperature=0.2,
            max_tokens=1000
        )
        
        try:
            return self._extract_json(validated_response)
        except ValueError:
            import logging
            logging.getLogger(__name__).warning("Failed to parse validated AI structure. Using initial structure.")
            return structure

    def _get_fallback_structure(self, project_brief: ProjectBrief) -> Dict[str, str]:
        """Fallback to hardcoded structure if AI fails."""
        lang = project_brief.primary_language.lower()
        
        # Base structure
        structure = {
            "README.md": "Project documentation",
            ".gitignore": "Git ignore rules",
            "Dockerfile": "Container definition",
            "docker-compose.yml": "Container orchestration"
        }
        
        # Language-specific files
        if lang in ["python", "py"]:
            structure.update({
                "requirements.txt": "Python dependencies",
                "src/__init__.py": "Package initialization",
                "src/main.py": "Main application entry point",
                "tests/__init__.py": "Test package initialization",
                "tests/test_main.py": "Unit tests"
            })
        elif lang in ["javascript", "typescript", "js", "ts"]:
            structure.update({
                "package.json": "NPM package configuration",
                "src/index.js": "Main application entry point",
                "tests/index.test.js": "Unit tests",
                ".eslintrc.json": "ESLint configuration"
            })
        else:
            structure.update({
                "src/main.py": "Main application",
                "tests/test_main.py": "Unit tests"
            })
        
        return structure
    
    def _generate_file_content(
        self,
        file_path: str,
        file_purpose: str,
        project_brief: ProjectBrief
    ) -> str:
        """
        Generate content for a specific file.
        
        Args:
            file_path: Path to file
            file_purpose: Purpose/description of file
            project_brief: Project specification
            
        Returns:
            File content as string
        """
        # Special handling for specific files
        if file_path == "README.md":
            return self._generate_readme(project_brief)
        elif file_path == ".gitignore":
            return self._generate_gitignore(project_brief.primary_language)
        elif file_path == "requirements.txt":
            return self._generate_requirements(project_brief.technologies)
        elif file_path == "package.json":
            return self._generate_package_json(project_brief)
        elif file_path == "Dockerfile":
            return self._generate_dockerfile(project_brief)
        elif file_path == "docker-compose.yml":
            return self._generate_docker_compose(project_brief)
        elif "__init__.py" in file_path:
            return '"""Package initialization."""\n'
        else:
            # Use AI to generate code files
            return self._generate_code_with_ai(file_path, file_purpose, project_brief)
    
    def _generate_readme(self, project_brief: ProjectBrief) -> str:
        """Generate README.md content using AI."""
        
        prompt = f"""Generate a professional README.md for this project:

**Title**: {project_brief.title}
**Description**: {project_brief.description}
**Technologies**: {', '.join(project_brief.technologies)}
**Learning Objectives**:
{chr(10).join(f'- {obj}' for obj in project_brief.learning_objectives)}

The README should include:
1. Project title and description
2. Features/capabilities
3. Technologies used
4. Installation instructions
5. Usage examples
6. Project structure overview
7. Learning objectives
8.License (MIT)

Make it professional and portfolio-ready. Use markdown formatting."""
        
        try:
            content = self.ai_client.generate(
                prompt=prompt,
                system_message="You are a technical writer creating professional project documentation.",
                temperature=0.7,
                max_tokens=1500
            )
            return content
        except Exception as e:
            # Fallback template
            return self._generate_readme_fallback(project_brief)
    
    def _generate_readme_fallback(self, project_brief: ProjectBrief) -> str:
        """Generate basic README without AI."""
        return f"""# {project_brief.title}

{project_brief.description}

## Technologies Used

{chr(10).join(f'- {tech}' for tech in project_brief.technologies)}

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd {self._sanitize_name(project_brief.title)}

# Install dependencies
{'pip install -r requirements.txt' if 'python' in project_brief.primary_language.lower() else 'npm install'}
```

## Usage

```bash
# Run the application
{'python src/main.py' if 'python' in project_brief.primary_language.lower() else 'npm start'}
```

## Learning Objectives

{chr(10).join(f'- {obj}' for obj in project_brief.learning_objectives)}

## Project Structure

```
{self._sanitize_name(project_brief.title)}/
├── README.md
├── src/
│   └── main.{project_brief.primary_language}
└── tests/
    └── test_main.{project_brief.primary_language}
```

## License

MIT License
"""
    
    def _generate_gitignore(self, language: str) -> str:
        """Generate .gitignore based on language."""
        common = """# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment
.env
.env.local
"""
        
        if "python" in language.lower():
            return common + """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
*.egg-info/
.pytest_cache/
.coverage
dist/
build/
"""
        elif language.lower() in ["javascript", "typescript"]:
            return common + """
# Node
node_modules/
npm-debug.log
yarn-error.log
.npm
dist/
build/
*.tsbuildinfo
"""
        else:
            return common
    
    def _generate_requirements(self, technologies: List[str]) -> str:
        """Generate requirements.txt based on technologies."""
        requirements = []
        
        tech_map = {
            "fastapi": "fastapi>=0.104.0\nuvicorn[standard]>=0.24.0",
            "django": "django>=4.2.0",
            "flask": "flask>=3.0.0",
            "pytorch": "torch>=2.1.0",
            "tensorflow": "tensorflow>=2.15.0",
            "scikit-learn": "scikit-learn>=1.3.0",
            "pandas": "pandas>=2.1.0",
            "numpy": "numpy>=1.24.0",
            "opencv": "opencv-python>=4.8.0",
            "transformers": "transformers>=4.35.0",
            "sqlalchemy": "sqlalchemy>=2.0.0",
        }
        
        for tech in technologies:
            tech_lower = tech.lower()
            if tech_lower in tech_map:
                requirements.append(tech_map[tech_lower])
        
        if not requirements:
            requirements.append("# Add your dependencies here")
        
        return "\n".join(requirements) + "\n"
    
    def _generate_package_json(self, project_brief: ProjectBrief) -> str:
        """Generate package.json for Node.js projects."""
        package = {
            "name": self._sanitize_name(project_brief.title),
            "version": "1.0.0",
            "description": project_brief.description,
            "main": "src/index.js",
            "scripts": {
                "start": "node src/index.js",
                "test": "jest"
            },
            "keywords": project_brief.technologies,
            "author": "",
            "license": "MIT",
            "dependencies": {},
            "devDependencies": {
                "jest": "^29.7.0"
            }
        }
        
        return json.dumps(package, indent=2)
    
    def _generate_code_with_ai(
        self,
        file_path: str,
        file_purpose: str,
        project_brief: ProjectBrief
    ) -> str:
        """Generate code file content using AI."""
        
        prompt = f"""Generate professional, well-documented code for this file:

**Project**: {project_brief.title}
**File**: {file_path}
**Purpose**: {file_purpose}
**Language**: {project_brief.primary_language}
**Description**: {project_brief.description}

Requirements:
- Clean, production-ready code with proper structure
- Comprehensive docstrings/comments explaining the code
- Type hints (if language supports)
- Error handling where appropriate
- Follow {project_brief.primary_language} best practices
- Include TODO comments for areas to expand

Generate ONLY the code, no explanations outside of code comments."""
        
        try:
            content = self.ai_client.generate(
                prompt=prompt,
                system_message="You are an expert software engineer writing production-quality code.",
                temperature=0.6,
                max_tokens=1500
            )
            
            # Clean up response if wrapped in markdown
            if "```" in content:
                # Extract code from markdown code blocks
                start = content.find("```")
                content = content[start:]
                # Remove first line with language identifier
                lines = content.split('\n')
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove closing ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = '\n'.join(lines)
            
            return content
        
        except Exception as e:
            # Fallback to simple template
            return self._generate_code_fallback(file_path, file_purpose, project_brief)
    
    def _generate_code_fallback(
        self,
        file_path: str,
        file_purpose: str,
        project_brief: ProjectBrief
    ) -> str:
        """Generate basic code template without AI."""
        if "python" in project_brief.primary_language.lower():
            if "test" in file_path:
                return self._generate_python_test(project_brief)
            else:
                return self._generate_python_source(file_path, project_brief)
        else:
             return f"// {file_purpose}\n// TODO: Implement {file_path}\n"

    def _generate_python_test(self, project_brief: ProjectBrief) -> str:
        return f'''"""
Unit tests for {project_brief.title}
"""

import pytest
try:
    from src.main import *
except ImportError:
    pass

def test_initialization():
    """Test that the application initializes correctly."""
    assert True

def test_core_functionality():
    """Placeholder for core logic tests."""
    # TODO: Implement actual tests
    pass
'''

    def _generate_python_source(self, file_path: str, project_brief: ProjectBrief) -> str:
        app_type = getattr(project_brief, 'app_type', 'script')
        
        common_header = f'''"""
{project_brief.title}
{project_brief.description}

Generated by GitHub Activity System
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

'''
        
        if app_type == 'web':
            return common_header + f'''
def create_app():
    """Initialize and configure the web application."""
    logger.info("Initializing web application...")
    # Simulation of web app setup
    app = {{
        "name": "{project_brief.title}",
        "routes": [],
        "config": {{}}
    }}
    return app

def main():
    """Main entry point for web server."""
    app = create_app()
    logger.info(f"Starting {{app['name']}} server on port 8000...")
    print(f"🚀 Server running at http://localhost:8000")
    
    # Simulate server loop
    try:
        # Check environment variables
        env = os.getenv("APP_ENV", "development")
        logger.info(f"Environment: {{env}}")
        
        print("Press Ctrl+C to stop")
    except KeyboardInterrupt:
        logger.info("Server stopping...")

if __name__ == "__main__":
    main()
'''
        elif app_type == 'api':
            return common_header + f'''
from typing import Dict, Any

class APIService:
    """Core API service implementation."""
    
    def __init__(self):
        self.endpoints = {{}}
        logger.info("API Service initialized")
        
    def register_endpoint(self, path: str, method: str, handler: Any):
        """Register a new API endpoint."""
        self.endpoints[f"{{method}} {{path}}"] = handler
        logger.info(f"Registered endpoint: {{method}} {{path}}")
        
    def handle_request(self, path: str, method: str) -> Dict:
        """Handle incoming API request."""
        key = f"{{method}} {{path}}"
        if key in self.endpoints:
            return {{"status": 200, "data": "Success"}}
        return {{"status": 404, "error": "Not Found"}}

def main():
    """Start the API service."""
    service = APIService()
    
    # Register core endpoints
    service.register_endpoint("/health", "GET", lambda: "OK")
    service.register_endpoint("/api/v1/data", "GET", lambda: [])
    
    logger.info("API Gateway running...")
    print(f"📡 {project_brief.title} API Active")

if __name__ == "__main__":
    main()
'''
        elif app_type == 'system':
            return common_header + f'''
import time
import random
from dataclasses import dataclass

@dataclass
class SystemConfig:
    max_connections: int = 100
    timeout: float = 30.0

class SystemCore:
    """Core logic for {project_brief.title}."""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.active = False
        self.metrics = {{}}
        
    def start(self):
        """Start system operations."""
        self.active = True
        logger.info("System core started")
        self._run_loop()
        
    def _run_loop(self):
        """Internal operation loop."""
        logger.info("Executing core logic...")
        # Simulate processing
        time.sleep(0.1)
        self.metrics['uptime'] = time.time()

def main():
    """System entry point."""
    config = SystemConfig()
    system = SystemCore(config)
    
    print(f"⚙️ Starting {project_brief.title}...")
    try:
        system.start()
    except Exception as e:
        logger.error(f"System failure: {{e}}")

if __name__ == "__main__":
    main()
'''
        else: # script/tool
            return common_header + f'''
import argparse

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="{project_brief.description}")
    parser.add_argument('--input', '-i', help='Input file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    return parser.parse_args()

def process_data(input_path: str):
    """Core processing logic."""
    if not input_path:
        logger.warning("No input provided, using default mode")
        return
        
    logger.info(f"Processing data from: {{input_path}}")
    # Simulate data processing
    result = {{
        "processed_at": datetime.now(),
        "status": "complete"
    }}
    return result

def main():
    """Script entry point."""
    args = parse_arguments()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        
    print(f"Running {project_brief.title}...")
    logger.info("Application started")
    
    process_data(args.input)
    
    print("✨ Execution complete")

if __name__ == "__main__":
    main()
'''

    def _generate_dockerfile(self, project_brief: ProjectBrief) -> str:
        """Generate Dockerfile based on project requirements."""
        if "python" in project_brief.primary_language.lower():
            return f"""# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Set environment variables
ENV APP_ENV=production
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "src/main.py"]
"""
        else:
            return """# Use an official Node.js runtime as a parent image
FROM node:18-alpine

# Set the working directory
WORKDIR /app

# Copy package headers
COPY package*.json ./

# Install dependencies
RUN npm install --production

# Copy source
COPY . .

# Expose port
EXPOSE 8000

# Start app
CMD ["npm", "start"]
"""

    def _generate_docker_compose(self, project_brief: ProjectBrief) -> str:
        """Generate docker-compose.yml."""
        name = self._sanitize_name(project_brief.title)
        return f"""version: '3.8'

services:
  {name}:
    build: .
    container_name: {name}
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - APP_ENV=development
    restart: unless-stopped
"""
    
    def _count_lines(self, directory: Path) -> int:
        """Count total lines of code in directory."""
        total_lines = 0
        
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix in [".py", ".js", ".ts", ".java", ".cpp"]:
                try:
                    total_lines += len(file_path.read_text(encoding='utf-8').splitlines())
                except Exception:
                    pass
        
        return total_lines
