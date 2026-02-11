# Automation & Strategy Guide

## Automation Strategy
The system is designed to run autonomously to build a consistent GitHub contribution graph.

### Modes
1.  **Auto (`mode: auto`)**:
    - Runs daily at scheduled time.
    - Generates project -> Commits -> Pushes to GitHub.
    - No user intervention required.
    - *Best for: Maintaining streaks.*
    
2.  **Review (`mode: review`)**:
    - Generates project -> Commits locally.
    - Pauses for user confirmation before pushing.
    - *Best for: Quality control.*

3.  **Manual (`mode: manual`)**:
    - Only runs when triggered via CLI (`python main.py run`).
    - *Best for: On-demand portfolio building.*

## Configuration Guide (`config.yaml`)

### AI Settings
```yaml
ai:
  provider: "ollama"  # or "openai"
  model: "llama3.2"   # local model
  api_key: "..."      # if using openai
```

### GitHub Settings
```yaml
github:
  username: "your-username"
  repository_strategy: "new_repo"  # new_repo (recommended) or monorepo
  default_visibility: "public"
```

### Scheduling
```yaml
scheduling:
  enabled: true
  time: "09:00"       # 24h format
  time_randomization_minutes: 60  # Varies start time to look natural
```

## Example Weekly Pipeline
A typical week of automated activity:

- **Monday**: Python Script (Data Processing) - *Focus: Pandas*
- **Tuesday**: React Component (Frontend) - *Focus: UI/UX*
- **Wednesday**: API Endpoint (Backend) - *Focus: FastAPI*
- **Thursday**: CSS Art / Animation - *Focus: creative coding*
- **Friday**: Utility Tool (CLI) - *Focus: System automation*
- **Saturday**: *Likely Skip* (weekend randomization)
- **Sunday**: Machine Learning Model (Basic) - *Focus: scikit-learn*
