@echo off
cd /d "C:\Users\anteb\Desktop\Courses\Projects\thesis_project\main"
echo Running critical fixes validation test...
uv run python test_critical_timeout_fixes.py
pause