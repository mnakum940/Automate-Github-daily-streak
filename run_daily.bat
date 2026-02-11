@echo off
:: GitHub Activity Generator - Daily Automation Script
:: This script can be scheduled in Windows Task Scheduler to run daily.

:: Navigate to project directory
cd /d "d:\Apni marzi\Daily Github\github-activity-system"

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Run the generator
:: --force ensures it runs even if it thinks it already ran today (optional)
python main.py run --force

:: Deactivate
deactivate
