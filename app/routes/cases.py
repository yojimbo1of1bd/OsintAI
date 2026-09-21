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

from app.database import get_db
from app.models import Case, Finding

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
        
    return templates.TemplateResponse(
        request=request,
        name="case_detail.html",
        context={"case": case},
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
    case = Case(name=name.strip(), notes=notes.strip())
    db.add(case)
    db.commit()
    return RedirectResponse(url="/cases", status_code=303)


@router.post("/{case_id}/pause")
async def pause_case(case_id: int, db: Session = Depends(get_db)):
    """Pause an active case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if case and case.status == "active":
        case.status = "paused"
        db.commit()
    return RedirectResponse(url="/cases", status_code=303)


@router.post("/{case_id}/resume")
async def resume_case(case_id: int, db: Session = Depends(get_db)):
    """Resume a paused case back to active."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if case and case.status == "paused":
        case.status = "active"
        db.commit()
    return RedirectResponse(url="/cases", status_code=303)


@router.post("/{case_id}/stop")
async def stop_case(case_id: int, db: Session = Depends(get_db)):
    """Stop a case (terminal — can only delete after this)."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if case and case.status in ("active", "paused"):
        case.status = "stopped"
        db.commit()
    return RedirectResponse(url="/cases", status_code=303)


@router.post("/{case_id}/delete")
async def delete_case(case_id: int, db: Session = Depends(get_db)):
    """Permanently delete a case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if case:
        db.delete(case)
        db.commit()
    return RedirectResponse(url="/cases", status_code=303)
