# Intelligent GitHub Activity Generator System

An automated, AI-powered system that generates meaningful GitHub projects and contributions to accelerate career growth for Computer Science students.

## 🎯 Purpose

Instead of random commits or empty activity, this system creates **genuine, portfolio-ready projects** that:
- Build real technical skills (AI/ML, Full-stack, System Design, Security/Blockchain)
- Maintain consistent GitHub activity
- Progress from beginner to advanced difficulty
- Include proper documentation, tests, and best practices

## ✨ Features

- **AI-Powered Project Generation**: Uses GPT-4 or local LLMs to create unique project ideas
- **Intelligent Skill Tracking**: Monitors your growth across multiple technical domains
- **Smart Commit Strategy**: Creates authentic-looking commits (not spam)
- **Quality Enforcement**: Ensures every project meets minimum standards
- **Automated Scheduling**: Runs daily with time randomization for authenticity
- **Progress Analytics**: Tracks skill proficiency and project difficulty progression

## 📋 Prerequisites

- Python 3.11 or higher
- Git installed and configured
- GitHub account with personal access token
- OpenAI API key (or Ollama for local LLM)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
cd github-activity-system

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/Mac

# Edit .env and add your credentials:
# - GITHUB_TOKEN (from GitHub Settings → Developer Settings → Personal Access Tokens)
# - GITHUB_USERNAME
# - OPENAI_API_KEY (or configure Ollama in config.yaml)
```

Edit `config.yaml` to customize:
- Skill focus areas (AI/ML, full-stack, system design, security)
- Daily execution time
- Automation mode (auto/review/manual)
- Quality thresholds

### 3. Initialize System

```bash
# Initialize database and directories
python main.py init

# Verify configuration
python main.py configure
```

### 4. Test Run

```bash
# Generate a project locally (without pushing to GitHub)
python main.py run --dry-run

# Check the generated project in the 'generated_projects/' directory
```

### 5. Start Automation

```bash
# For daily automated execution
python main.py schedule

# Or run manually anytime
python main.py run
```

# Or run manually anytime
python main.py run
```

### 6. Windows Task Scheduler ("Cron Job")

To run the generator automatically in the background (like a cron job):

1.  Open **Task Scheduler** on Windows.
2.  Click **Create Basic Task**.
3.  Name it "GitHub Activity Generator".
4.  Trigger: **Daily** at your preferred time (e.g., 09:00 AM).
5.  Action: **Start a program**.
6.  Program/script: Browse and select the `run_daily.bat` file in this folder.
7.  Finish.

## 📊 Commands

| Command | Description |
|---------|-------------|
| `python main.py init` | Initialize database and directories |
| `python main.py configure` | Check and validate configuration |
| `python main.py run` | Execute workflow immediately |
| `python main.py run --dry-run` | Generate locally without pushing |
| `python main.py schedule` | Start daily scheduler |
| `python main.py status` | View statistics and recent activity |
| `python main.py dashboard` | Interactive progress dashboard |
| `python main.py reset` | Reset database (deletes all data) |

## 🏗️ System Architecture

```
┌─────────────────┐
│ Daily Scheduler │
└────────┬────────┘
         │
         v
┌─────────────────────┐
│ Project Planner     │ ← Analyzes skill gaps
│ (AI-powered)        │
└────────┬────────────┘
         │
         v
┌─────────────────────┐
│ Code Generator      │ ← Creates project structure
│ (LLM-based)         │   and starter code
└────────┬────────────┘
         │
         v
┌─────────────────────┐
│ Documentation       │ ← Generates README,
│ Generator           │   commit messages
└────────┬────────────┘
         │
         v
┌─────────────────────┐
│ Git Automation      │ ← Creates commits,
│ Engine              │   pushes to GitHub
└────────┬────────────┘
         │
         v
┌─────────────────────┐
│ Skill Tracker       │ ← Updates proficiency
│ & Analytics         │   scores
└─────────────────────┘
```

## 📁 Project Structure

```
github-activity-system/
├── main.py                 # CLI entry point
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create from .env.example)
│
├── src/                    # Source code
│   ├── config_manager.py   # Configuration management
│   ├── database.py         # Database models
│   ├── planning/           # Project planning modules
│   ├── generation/         # Code generation
│   ├── automation/         # Git & GitHub automation
│   ├── tracking/           # Analytics & tracking
│   └── orchestration/      # Workflow orchestration
│
├── templates/              # Project templates
│   ├── ai_ml/
│   ├── full_stack/
│   ├── system_design/
│   └── security_blockchain/
│
├── data/                   # Generated at runtime
│   ├── activity_tracker.db
│   └── logs/
│
└── generated_projects/     # Local project generation
```

## 🎓 Skill Categories

### AI/ML (35%)
- Machine Learning
- Deep Learning
- Natural Language Processing
- Computer Vision
- MLOps

### Full-Stack Development (30%)
- Backend (FastAPI, Django, Express)
- Frontend (React, Next.js)
- REST APIs
- Database Design

### System Design (20%)
- Distributed Systems
- Caching Strategies
- Message Queues
- Microservices
- Load Balancing

### Security/Blockchain (15%)
- Authentication & Authorization
- Encryption
- Web Security
- Smart Contracts
- Security Auditing

## 🔒 Authenticity Features

To avoid appearing as bot activity:
- **Time Randomization**: Commits at slightly different times (±2 hours)
- **Quality Thresholds**: Minimum 100 LOC, documentation, tests required
- **Varied Commit Messages**: Semantic commit messages with context
- **Smart Commit Strategy**: 1-3 meaningful commits per project
- **Review Mode**: Optional human approval before push
- **Technology Diversity**: Prevents same tech/category on consecutive days

## 📈 Progress Tracking

The system tracks:
- ✅ **Skill Proficiency**: 0-100 score for each skill
- ✅ **Technology Coverage**: Which frameworks/languages used
- ✅ **Difficulty Progression**: Ensures gradual advancement
- ✅ **Contribution Streak**: Daily activity monitoring
- ✅ **Portfolio Quality Score**: Overall portfolio readiness

## 🤝 Contributing

This is a personal career development tool, but improvements are welcome!

## 📄 License

MIT License - feel free to use and modify for your own career growth.

## 👤 Author

**Meet Nakum**
- B.Tech in Computer Science (Jain University, 2021-2025)
- M.Tech in AI & Data Science (DBS Global University, 2025-2027)

## 🙏 Acknowledgments

Built to demonstrate:
- AI integration capabilities
- Software engineering best practices
- Commitment to continuous learning
- Portfolio-building strategies

---

**Note**: This system is designed for genuine skill development. Use responsibly and ensure all generated code is understood and can be explained in interviews.
