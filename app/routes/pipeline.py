from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models import Case, CaseContext
from app.pipeline import start_pipeline, get_pipeline_status

router = APIRouter(prefix="/cases", tags=["pipeline"])
logger = logging.getLogger(__name__)

@router.post("/{case_id}/pipeline/run")
async def run_pipeline_route(case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    if case.status != "active":
        raise HTTPException(status_code=400, detail="Cannot run pipeline on inactive case")
        
    context = db.query(CaseContext).filter(CaseContext.case_id == case_id).first()
    if not context:
        raise HTTPException(status_code=400, detail="Cannot run pipeline without seeding context first")

    success = start_pipeline(case_id)
    if not success:
        return JSONResponse(status_code=400, content={"message": "Pipeline is already running for this case"})
        
    return JSONResponse(status_code=202, content={"message": "Pipeline started"})

@router.get("/{case_id}/pipeline/status")
async def pipeline_status_route(case_id: int):
    status_data = get_pipeline_status(case_id)
    return JSONResponse(status_code=200, content=status_data)
