"""
Lodestar — Case Manager routes.

Module 1 from DESIGN_AND_SCOPE.md §7:
  Create / pause / stop / delete a case. Every other module checks
  case status first, so pausing actually halts in-flight work.

Routes:
  GET  /cases              — list all cases + create form (HTML page)
  POST /cases/create       — create a new case
  POST /cases/{id}/pause   — pause an active case
  POST /cases/{id}/resume  — resume a paused case
  POST /cases/{id}/stop    — stop a case (terminal)
  POST /cases/{id}/delete  — delete a case permanently
"""

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os
import logging

from app.database import get_db
from app.models import Case, Finding
from app.correlator import cancel_scan

router = APIRouter(prefix="/cases", tags=["cases"])

# Templates — project root is 3 levels up from app/routes/cases.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@router.get("")
async def list_cases(request: Request, db: Session = Depends(get_db)):
    """List all cases with create/action controls."""
    cases = db.query(Case).order_by(Case.created_at.desc()).all()
    return templates.TemplateResponse(
        request=request,
        name="cases.html",
        context={"cases": cases},
    )


@router.get("/{case_id}")
async def case_detail(request: Request, case_id: int, db: Session = Depends(get_db)):
    """View details and findings for a specific case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    # Get available scripts
    scripts_dir = os.path.join(BASE_DIR, "scripts")
    available_scripts = []
    if os.path.exists(scripts_dir):
        available_scripts = [f for f in os.listdir(scripts_dir) if f.endswith(".py") or f.endswith(".sh") or f.endswith(".bat")]
        
    # Get run logs for this case
    logs_dir = os.path.join(BASE_DIR, "data", "logs")
    case_logs = []
    if os.path.exists(logs_dir):
        prefix = f"case_{case_id}_"
        case_logs = sorted([f for f in os.listdir(logs_dir) if f.startswith(prefix)], reverse=True)
        
    return templates.TemplateResponse(
        request=request,
        name="case_detail.html",
        context={
            "case": case,
            "available_scripts": available_scripts,
            "case_logs": case_logs
        },
    )


# ---------------------------------------------------------------------------
# Actions (all redirect back to the case list)
# ---------------------------------------------------------------------------

@router.post("/create")
async def create_case(
    name: str = Form(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    """Create a new case with status='active'."""
    try:
        case = Case(name=name.strip(), notes=notes.strip())
        db.add(case)
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating case: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred while creating case.")
        
    return RedirectResponse(url="/cases", status_code=303)


@router.post("/{case_id}/pause")
async def pause_case(case_id: int, db: Session = Depends(get_db)):
    """Pause an active case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if case and case.status == "active":
        try:
            case.status = "paused"
            db.commit()
            cancel_scan(case_id)
        except Exception as e:
            db.rollback()
            logging.error(f"Error pausing case {case_id}: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred while pausing case.")
            
    return RedirectResponse(url="/cases", status_code=303)


@router.post("/{case_id}/resume")
async def resume_case(case_id: int, db: Session = Depends(get_db)):
    """Resume a paused case back to active."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if case and case.status == "paused":
        try:
            case.status = "active"
            db.commit()
        except Exception as e:
            db.rollback()
            logging.error(f"Error resuming case {case_id}: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred while resuming case.")
            
    return RedirectResponse(url="/cases", status_code=303)


@router.post("/{case_id}/stop")
async def stop_case(case_id: int, db: Session = Depends(get_db)):
    """Stop a case (terminal — can only delete after this)."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if case and case.status in ("active", "paused"):
        try:
            case.status = "stopped"
            db.commit()
            cancel_scan(case_id)
        except Exception as e:
            db.rollback()
            logging.error(f"Error stopping case {case_id}: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred while stopping case.")
            
    return RedirectResponse(url="/cases", status_code=303)


@router.post("/{case_id}/delete")
async def delete_case(case_id: int, db: Session = Depends(get_db)):
    """Permanently delete a case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if case:
        try:
            db.delete(case)
            db.commit()
        except Exception as e:
            db.rollback()
            logging.error(f"Error deleting case {case_id}: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred while deleting case.")
            
    return RedirectResponse(url="/cases", status_code=303)
