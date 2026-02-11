# System Architecture

## Overview
The **GitHub Activity Generator** is an intelligent, automated system designed to help developers build a robust portfolio and maintain an active GitHub presence. It combines AI-driven code generation, automated Git workflows, and comprehensive skill tracking.

## Core Components

### 1. Project Planning Engine (`src/planning`)
- **Role**: Brain of the system.
- **Function**: Analyzes user's skill gaps and generates novel project ideas.
- **Key Modules**:
    - `ProjectPlanner`: Orchestrates idea generation.
    - `SkillMapper`: Maps project requirements to user skills.

### 2. Code Generation Engine (`src/generation`)
- **Role**: Creative engine.
- **Function**: Generates actual code, documentation, and file structures.
- **Key Modules**:
    - `CodeGenerator`: Creates project files.
    - `DocGenerator`: Writes READMEs and commit messages.
    - `AIProvider`: Abstraction layer for LLMs (Ollama/OpenAI).

### 3. Automation Layer (`src/automation`)
- **Role**: Execution arm.
- **Function**: Handles Git operations and scheduling.
- **Key Modules**:
    - `GitManager`: Initialization, commits, pushes.
    - `DailyScheduler`: Cron-like task scheduling.

### 4. Tracking & Analytics (`src/tracking`, `src/database.py`)
- **Role**: Memory and feedback loop.
- **Function**: Stores project history, tracks skill proficiency, and grants achievements.
- **Key Modules**:
    - `AnalyticsEngine`: Calculates stats and streaks.
    - `Dashboard`: Visualizes progress in the terminal.

## Data Flow

1.  **Trigger**: Scheduler or Manual CLI command initiates the workflow.
2.  **Planning**: Planner queries tracking DB for weak skills -> Generates Idea.
3.  **Generation**: Code Generator prompts AI for file structure -> Creating files.
4.  **Documentation**: Doc Generator writes README and commit messages.
5.  **Version Control**: Git Manager commits changes locally (and pushes if configured).
6.  **Tracking**: DB updates with new project, XP, and potential achievements.

## Tech Stack
- **Language**: Python 3.11+
- **CLI**: Typer, Rich
- **Database**: SQLite (SQLAlchemy ORM)
- **AI**: Ollama (Llama 3.2) / OpenAI API
- **Scheduling**: APScheduler
