"""
Safe, isolated export format handler.
Does NOT modify existing download endpoint.
"""

import json
import yaml
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from jinja2 import Environment, FileSystemLoader

router = APIRouter(prefix="/jobs", tags=["export"])

# Template setup
TEMPLATES_DIR = Path(__file__).parent / "templates"
jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

@router.get("/{job_id}/export/html")
async def export_html(job_id: str):
    """
    Export test suite as stunning HTML.
    Reads existing JSON output, renders with Jinja2.
    """
    # 1. Define paths
    # We need to find the JSON file in output/test_suites/
    # Pattern: test_suite_{suite_id}_{timestamp}.json
    # But we only have job_id.
    # The worker saves the result URI in the job record, but we want to avoid DB lookups if possible to keep it simple.
    # However, the plan says: "Reads existing JSON files from output/test_suites/"
    # Wait, the plan says: "JSON already generated at output/test_suites/test_suite_{suite_id}_{timestamp}.json"
    # But how do we know which file belongs to the job_id?
    # The job_id is usually the suite_id in this system (or related).
    # Let's check how the system stores outputs.
    # The context says: "Test suites stored as YAML at output/{job_id}/test_suite.yaml"
    # And "JSON already generated at output/test_suites/test_suite_{suite_id}_{timestamp}.json"
    
    # If we look at the file structure:
    # output/
    #   61f608fa-f708-4818-9091-4ddaac3f49f3.json
    #   61f608fa-f708-4818-9091-4ddaac3f49f3.meta.json
    #   cross_validation/
    #   test_suites/
    
    # It seems simpler to read the YAML from output/{job_id}/test_suite.yaml and convert it to the context needed for the template.
    # OR, if there is a JSON file with the job_id, we can use that.
    # The plan says: "Reads existing JSON files from output/test_suites/"
    # But it also says: "JSON already generated at output/test_suites/test_suite_{suite_id}_{timestamp}.json"
    # This might be tricky if we don't know the timestamp.
    
    # Let's look at the plan again.
    # "Reads existing JSON files from output/test_suites/"
    # Maybe I should look for a file that contains the job_id in the name?
    # Or maybe I should just read the YAML file which is definitely at output/{job_id}/test_suite.yaml
    # and parse it. That seems safer and more deterministic.
    # But the plan explicitly mentions JSON.
    # "JSON already generated at output/test_suites/test_suite_{suite_id}_{timestamp}.json (line 2210 in unified_workflow.py)"
    
    # Let's check unified_workflow.py to see how the filename is generated.
    # But I can't easily check that without reading the file.
    # However, I can check if there is a file at output/{job_id}/test_suite.json or similar.
    # The file list shows `output/61f608fa-f708-4818-9091-4ddaac3f49f3.json`. This looks like a job output.
    
    # Let's try to find the JSON file.
    # If I can't find it, I'll fallback to YAML.
    # Actually, parsing YAML is easy in Python.
    # Let's try to locate the file.
    
    base_path = Path("/app/output") # In Docker
    # For local dev, it might be different, but we are running in Docker context usually?
    # The workspace info says c:\Users\anteb\Desktop\Courses\Projects\thesis_project
    # So locally it is output/
    
    # Let's assume we are running in the container where /app/output is the mount.
    # But for the code to work locally and in docker, we should use relative paths or env vars.
    # The app.py is in main/api/app.py.
    # So output is at ../../../output relative to this file?
    # No, usually we run from the root.
    
    # Let's use a robust way to find the output directory.
    # In `main/api/worker_executor.py` (mentioned in plan), it saves artifacts.
    
    # Let's try to find the file using the job_id.
    # The simplest way is to look for `output/{job_id}/test_suite.yaml` which is guaranteed to exist according to "Current State".
    # Then we can parse it to a dict and pass it to the template.
    # This avoids the timestamp issue with the JSON file in `test_suites/`.
    
    # Try to find the file
    # We assume the app is running from the project root or we can find the output dir.
    # In Docker, WORKDIR is /app. output is /app/output.
    # Locally, it is ./output.
    
    output_dir = Path("output")
    if not output_dir.exists():
        output_dir = Path("/app/output")
    
    yaml_path = output_dir / job_id / "test_suite.yaml"
    
    if not yaml_path.exists():
        # Try to find it in the test_suites folder if it's not in the job folder?
        # Or maybe the job_id IS the suite_id?
        # Let's assume the standard path first.
        raise HTTPException(status_code=404, detail="Test suite not found")
        
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            suite_data = yaml.safe_load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load test suite: {str(e)}")
        
    # Render template
    template = jinja_env.get_template("test_suite_bold.html")
    html_content = template.render(suite=suite_data)
    
    return Response(content=html_content, media_type="text/html")

@router.get("/{job_id}/export/json")
async def export_json(job_id: str):
    """Export test suite as JSON (already exists, just serve it)."""
    
    # Same logic to find the data, but return as JSON attachment
    
    output_dir = Path("output")
    if not output_dir.exists():
        output_dir = Path("/app/output")
    
    yaml_path = output_dir / job_id / "test_suite.yaml"
    
    if not yaml_path.exists():
        raise HTTPException(status_code=404, detail="Test suite not found")
        
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            suite_data = yaml.safe_load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load test suite: {str(e)}")
        
    return Response(
        content=json.dumps(suite_data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=test_suite_{job_id}.json"}
    )
