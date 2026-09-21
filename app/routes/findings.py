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
import logging

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
    
    try:
        db.add(finding)
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"Error creating finding: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred while creating finding.")
    
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
        try:
            db.delete(finding)
            db.commit()
        except Exception as e:
            db.rollback()
            logging.error(f"Error deleting finding {finding_id}: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred while deleting finding.")
        
    return RedirectResponse(url=f"/cases/{case_id}", status_code=303)

from app.correlator import start_maigret_scan

@router.post("/scan")
async def scan_username(
    case_id: int,
    username: str = Form(...),
    db: Session = Depends(get_db)
):
    """Start a background Maigret scan for a username."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case or case.status != "active":
        raise HTTPException(status_code=400, detail="Case must be active to run scans")
        
    start_maigret_scan(case_id, username.strip())
    return RedirectResponse(url=f"/cases/{case_id}", status_code=303)


@router.post("/{finding_id}/verify")
async def verify_finding(
    case_id: int, 
    finding_id: int, 
    db: Session = Depends(get_db)
):
    """Mark an unverified finding as verified."""
    finding = db.query(Finding).filter(
        Finding.id == finding_id, 
        Finding.case_id == case_id
    ).first()
    
    if finding and not finding.verified:
        try:
            finding.verified = True
            db.commit()
        except Exception as e:
            db.rollback()
            logging.error(f"Error verifying finding {finding_id}: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred while verifying finding.")
        
    return RedirectResponse(url=f"/cases/{case_id}", status_code=303)
