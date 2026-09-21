"""
Lodestar — Findings routes.

Module 2 from DESIGN_AND_SCOPE.md §7:
  Finding Logger — the core manual-entry workflow everything else feeds into.

Routes:
  POST /cases/{case_id}/findings/create    — add a new finding to a case
  POST /cases/{case_id}/findings/{id}/delete — delete a single finding
"""

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Case, Finding

router = APIRouter(prefix="/cases/{case_id}/findings", tags=["findings"])


@router.post("/create")
async def create_finding(
    case_id: int,
    category: str = Form(...),
    value: str = Form(...),
    source_url: str = Form(...),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    """Add a new manual finding to a case. Defaults to verified=True."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    finding = Finding(
        case_id=case_id,
        category=category.strip(),
        value=value.strip(),
        source_url=source_url.strip(),
        notes=notes.strip(),
        verified=True  # Manual entries are considered verified by the user
    )
    db.add(finding)
    db.commit()
    
    return RedirectResponse(url=f"/cases/{case_id}", status_code=303)


@router.post("/{finding_id}/delete")
async def delete_finding(
    case_id: int, 
    finding_id: int, 
    db: Session = Depends(get_db)
):
    """Permanently delete a finding."""
    # Ensure finding belongs to the case
    finding = db.query(Finding).filter(
        Finding.id == finding_id, 
        Finding.case_id == case_id
    ).first()
    
    if finding:
        db.delete(finding)
        db.commit()
        
    return RedirectResponse(url=f"/cases/{case_id}", status_code=303)
