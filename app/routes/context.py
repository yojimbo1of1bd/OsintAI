from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import logging
import os

from app.database import get_db
from app.models import Case, CaseContext, Finding

router = APIRouter(prefix="/cases", tags=["context"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@router.get("/{case_id}/context", response_class=HTMLResponse)
async def view_context(request: Request, case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    context = db.query(CaseContext).filter(CaseContext.case_id == case_id).first()
    
    return templates.TemplateResponse("context_intake.html", {
        "request": request, 
        "case": case, 
        "context": context
    })

@router.post("/{case_id}/context")
async def save_context(
    case_id: int,
    subject_name: str = Form(""),
    known_aliases: str = Form(""),
    age_range: str = Form(""),
    last_known_location: str = Form(""),
    last_seen_date: str = Form(""),
    known_associates: str = Form(""),
    social_handles: str = Form(""),
    life_events: str = Form(""),
    physical_description: str = Form(""),
    additional_notes: str = Form(""),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    if case.status != "active":
        raise HTTPException(status_code=400, detail="Cannot edit context of an inactive case")

    context = db.query(CaseContext).filter(CaseContext.case_id == case_id).first()
    
    is_new = False
    if not context:
        context = CaseContext(case_id=case_id)
        is_new = True
        
    context.subject_name = subject_name.strip()
    context.known_aliases = known_aliases.strip()
    context.age_range = age_range.strip()
    context.last_known_location = last_known_location.strip()
    context.last_seen_date = last_seen_date.strip()
    context.known_associates = known_associates.strip()
    context.social_handles = social_handles.strip()
    context.life_events = life_events.strip()
    context.physical_description = physical_description.strip()
    context.additional_notes = additional_notes.strip()

    try:
        if is_new:
            db.add(context)
            
        # Auto-generate findings from structured fields if they are new or updated
        # Simple implementation: just create findings, let the user delete duplicates
        findings_to_add = []
        
        def add_finding_if_present(category, value, notes="Auto-generated from context"):
            if value:
                findings_to_add.append(Finding(
                    case_id=case_id,
                    category=category,
                    value=value,
                    source_url="Lodestar Context Intake",
                    notes=notes,
                    verified=False
                ))

        if social_handles.strip():
            for handle in [h.strip() for h in social_handles.split(",") if h.strip()]:
                add_finding_if_present("Basic Subject Info", handle, "Social handle auto-generated from context")
                
        if subject_name.strip():
            add_finding_if_present("Basic Subject Info", subject_name.strip(), "Name auto-generated from context")
            
        if known_aliases.strip():
            for alias in [a.strip() for a in known_aliases.split(",") if a.strip()]:
                add_finding_if_present("Basic Subject Info", alias, "Alias auto-generated from context")
                
        if last_known_location.strip():
            add_finding_if_present("Location", last_known_location.strip(), f"Last seen date: {last_seen_date.strip() if last_seen_date else 'Unknown'}")

        if findings_to_add:
            db.add_all(findings_to_add)

        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"Error saving context for case {case_id}: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred while saving context.")

    return RedirectResponse(url=f"/cases/{case_id}", status_code=303)
