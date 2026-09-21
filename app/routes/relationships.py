from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Case, Relationship

router = APIRouter(prefix="/cases/{case_id}/relationships", tags=["relationships"])


@router.post("/create")
async def create_relationship(
    case_id: int,
    person_a: str = Form(...),
    relation: str = Form(...),
    person_b: str = Form(...),
    source_url: str = Form(...),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    relationship = Relationship(
        case_id=case_id,
        person_a=person_a.strip(),
        relation=relation.strip(),
        person_b=person_b.strip(),
        source_url=source_url.strip()
    )
    db.add(relationship)
    db.commit()
    
    return RedirectResponse(url=f"/cases/{case_id}", status_code=303)


@router.post("/{relationship_id}/delete")
async def delete_relationship(
    case_id: int, 
    relationship_id: int, 
    db: Session = Depends(get_db)
):
    relationship = db.query(Relationship).filter(
        Relationship.id == relationship_id, 
        Relationship.case_id == case_id
    ).first()
    
    if relationship:
        db.delete(relationship)
        db.commit()
                
    return RedirectResponse(url=f"/cases/{case_id}", status_code=303)
