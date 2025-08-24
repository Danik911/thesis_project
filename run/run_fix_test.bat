@echo off
echo Running fixes test...
cd /d "C:\Users\anteb\Desktop\Courses\Projects\thesis_project"
set PYTHONPATH=%CD%\main
uv run python test_fixes.py
pause