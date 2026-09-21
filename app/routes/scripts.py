"""
Lodestar — Custom Script Runner routes.

Module 8 from DESIGN_AND_SCOPE.md:
  Scripts only launch from a fixed `scripts/` folder; running requires a confirm
  click; stdout/stderr piped to a per-run log; case-status check before allowing.
"""

from fastapi import APIRouter, Depends, Form, HTTPException, BackgroundTasks
from fastapi.responses import RedirectResponse, PlainTextResponse
from sqlalchemy.orm import Session
import os
import sys
import time
import subprocess
import logging
from datetime import datetime

from app.database import get_db
from app.models import Case

router = APIRouter(prefix="/cases", tags=["scripts"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
LOGS_DIR = os.path.join(BASE_DIR, "data", "logs")

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)


def run_script_background(case_id: int, script_name: str, script_path: str):
    """Run a script in a background process and pipe output to a log file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"case_{case_id}_{os.path.splitext(script_name)[0]}_{timestamp}.log"
    log_path = os.path.join(LOGS_DIR, log_filename)
    
    python_exe = sys.executable
    
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"--- Running {script_name} for Case {case_id} ---\n")
            f.write(f"Started at: {datetime.now().isoformat()}\n\n")
            
            # Run the script, capturing stdout and stderr into the log file
            process = subprocess.Popen(
                [python_exe, script_path],
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd=BASE_DIR
            )
            process.wait()
            
            f.write(f"\n--- Script Finished ---\n")
            f.write(f"Exit code: {process.returncode}\n")
            f.write(f"Finished at: {datetime.now().isoformat()}\n")
            
    except Exception as e:
        logging.error(f"Failed to run script {script_name} for case {case_id}: {e}")
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\nERROR: Failed to run script. {e}\n")
        except Exception:
            pass


@router.post("/{case_id}/scripts/run")
async def run_script(
    case_id: int, 
    script_name: str = Form(...), 
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Validate and run a script from the scripts directory."""
    # Ensure case exists and is active
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    if case.status != "active":
        raise HTTPException(status_code=400, detail="Scripts can only be run on active cases")
        
    # Prevent directory traversal attacks
    if ".." in script_name or "/" in script_name or "\\" in script_name:
        raise HTTPException(status_code=400, detail="Invalid script name")
        
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    
    # Verify script exists in the exact directory
    if not os.path.isfile(script_path) or os.path.dirname(os.path.abspath(script_path)) != os.path.abspath(SCRIPTS_DIR):
        raise HTTPException(status_code=404, detail="Script not found")
        
    # Kick off background task
    background_tasks.add_task(run_script_background, case_id, script_name, script_path)
    
    return RedirectResponse(url=f"/cases/{case_id}", status_code=303)


@router.get("/{case_id}/scripts/logs/{log_filename}")
async def view_script_log(case_id: int, log_filename: str):
    """View the raw text of a script run log."""
    # Prevent directory traversal attacks
    if ".." in log_filename or "/" in log_filename or "\\" in log_filename:
        raise HTTPException(status_code=400, detail="Invalid log filename")
        
    log_path = os.path.join(LOGS_DIR, log_filename)
    
    if not os.path.isfile(log_path):
        raise HTTPException(status_code=404, detail="Log file not found")
        
    # Extra check: ensure it matches the case ID format to prevent viewing other cases' logs
    if not log_filename.startswith(f"case_{case_id}_"):
        raise HTTPException(status_code=403, detail="Access denied to this log file")
        
    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    return PlainTextResponse(content)
