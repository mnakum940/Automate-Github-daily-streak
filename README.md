# Intelligent GitHub Activity Generator System

![Version](https://img.shields.io/badge/version-1.0.0-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Status](https://img.shields.io/badge/status-active-success)

An automated, AI-powered system that generates meaningful GitHub projects and contributions to accelerate career growth for Computer Science students.

## 🎯 Purpose

Instead of random commits or empty activity, this system creates **genuine, portfolio-ready projects** that:
- Build real technical skills (AI/ML, Full-stack, System Design, Security/Blockchain).
- Maintain consistent GitHub activity.
- Progress from beginner to advanced difficulty.
- Include proper documentation, tests, and best practices.

## ✨ Features

- **🧠 AI-Powered Planning**: Uses LLMs (Ollama/OpenAI) to generate unique, novel project ideas based on your skill gaps.
- **🏗️ Smart Architecture**: Automatically designs professional file structures (2-Factor Analysis) and writes production-ready code.
- **🐳 Docker Integration**: Every generated project comes with a `Dockerfile` and `docker-compose.yml`.
- **🏆 Gamification**: Earn XP, streaks, and unlock achievements (e.g., "Code Warrior", "Hello World").
- **📄 Resume Generator**: Auto-generates a markdown resume based on your completed projects.
- **📊 Interactive Dashboard**: Visualizes your progress, skill proficiency, and activity stats in the terminal.
- **🤖 Git Automation**: Handles `git init`, semantic commits, and remote pushes automatically.

## 📋 Prerequisites

- **Python 3.11+**
- **Git** installed and configured
- **GitHub Account** (with Personal Access Token)
- **Ollama** (for local LLM) or **OpenAI API Key**

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/github-activity-system.git
cd github-activity-system

# Create virtual environment
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Create .env file
copy .env.example .env

# Edit .env with your credentials:
# GITHUB_TOKEN=ghp_...
# GITHUB_USERNAME=...
```

### 3. Initialize System

```bash
python main.py init
python main.py configure
```

### 4. Generate Your First Project

```bash
# Run locally (dry-run) to see what content is generated
python main.py run --dry-run
```

## 📊 Commands

| Command | Description |
| :--- | :--- |
| `python main.py init` | Initialize database and create necessary directories. |
| `python main.py configure` | Validate configuration and environment variables. |
| `python main.py run` | **Generate a new project** (Planning -> Code -> Git Commit -> Push). |
| `python main.py run --dry-run` | Generate project locally without pushing to GitHub. |
| `python main.py resume` | **Generate a resume** based on your project history. |
| `python main.py status` | View current statistics, level, and recent activity. |
| `python main.py dashboard` | Open the interactive terminal dashboard. |
| `python main.py schedule` | Start the daily automation scheduler. |
| `python main.py reset` | **Reset the system** (clears database and projects). |

## 🏗️ System Architecture

1.  **Project Planner**: Analyzes your skill profile and suggests a new project.
2.  **Code Generator**: Uses AI to design the file structure and write code.
3.  **Documentation Engine**: Generates professional README and commit messages.
4.  **Git Manager**: Initializes repo, commits changes, and pushes to remote.
5.  **Tracker**: Updates your XP, skills, and achievements database.

## 📁 Project Structure

```
github-activity-system/
├── src/
│   ├── planning/       # AI Project Planning
│   ├── generation/     # Code & Doc Generation
│   ├── automation/     # Git & Scheduling
│   ├── tracking/       # Analytics & DB
│   └── reporting/      # Resume Generator
├── data/               # SQLite Database
├── docs/               # System Documentation
└── generated_projects/ # Where your projects live
```

## 🎓 Skill Tracks

The system rotates through these domains to build a T-shaped profile:
- **AI/ML**: PyTorch, TensorFlow, OpenCV, NLP
- **Full-Stack**: React, FastAPI, Node.js, Django
- **System Design**: Microservices, Docker, Redis
- **Security**: Cryptography, Auth, Blockchain

## 🤝 Contributing

This is a personal tool for career growth, but improvements are welcome!

## 📄 License

MIT License.

## 👤 Author

**Meet Nakum**
- B.Tech in Computer Science (Jain University, 2021-2025)
- M.Tech in AI & Data Science (DBS Global University, 2025-2027)

---
*Built with Python, Typer, Rich, and LLMs.*
