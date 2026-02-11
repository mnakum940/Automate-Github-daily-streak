# Module Design Specifications

## 1. Project Project Planner (`src/planning/project_planner.py`)
- **Responsibility**: Generate valid, novel project ideas.
- **Inputs**: Current user skills, project history.
- **Process**:
    1.  Fetch low-proficiency skills from DB.
    2.  Prompt AI for 3 project ideas involving those skills.
    3.  Select best idea and validate "novelty" (check against past projects).
- **Outputs**: `ProjectBrief` object.

## 2. Code Generator (`src/generation/code_generator.py`)
- **Responsibility**: Create file system artifacts.
- **Inputs**: `ProjectBrief`.
- **Process**:
    1.  **Smart Structure**: Ask AI for optimal file layout (JSON).
    2.  **2-Factor Validation**: Ask AI to verify structure for missing files.
    3.  **Generation**: Loop through files, prompting AI for content (or using templates).
- **Outputs**: Physical files on disk.

## 3. Git Manager (`src/automation/git_manager.py`)
- **Responsibility**: Handle version control.
- **Inputs**: Project directory, list of commit messages.
- **Process**:
    1.  `git init`
    2.  `git add .`
    3.  `git commit -m "Initial commit"`
    4.  Create subsequent commits for simulated history.
    5.  `git push` (if remote configured).
- **Outputs**: Git repository with history.

## 4. Resume Generator (`src/reporting/resume_generator.py`)
- **Responsibility**: Create portfolio documents.
- **Inputs**: Full database (Projects, Skills, Achievements).
- **Process**:
    1.  Aggregate finished projects and top skills.
    2.  Prompt AI to write professional descriptions for each project.
    3.  Render Markdown document.
- **Outputs**: `output/resumes/resume_YYYYMMDD.md`
