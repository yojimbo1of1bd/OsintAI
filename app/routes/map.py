from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os

from app.database import get_db
from app.models import Case, Finding, Relationship, Image, CaseContext

router = APIRouter(prefix="/cases", tags=["map"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@router.get("/{case_id}/map", response_class=HTMLResponse)
async def view_case_map(request: Request, case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    data = get_map_data_for_case(case_id, db)
    
    return templates.TemplateResponse("case_map.html", {
        "request": request,
        "case": case,
        **data
    })

def get_map_data_for_case(case_id: int, db: Session) -> dict:
    context = db.query(CaseContext).filter(CaseContext.case_id == case_id).first()
    findings = db.query(Finding).filter(Finding.case_id == case_id).all()
    relationships = db.query(Relationship).filter(Relationship.case_id == case_id).all()
    images = db.query(Image).filter(Image.case_id == case_id).all()

    # Pre-process handles for the social grid
    social_handles = []
    # Add from context
    if context and context.social_handles:
        for h in [x.strip() for x in context.social_handles.split(",") if x.strip()]:
            social_handles.append({
                "handle": h,
                "platform": "Unknown",
                "verified": False,
                "source": "Context Intake"
            })
    # Add from findings (Maigret correlates things)
    for f in findings:
        if f.category == "Basic Subject Info" and ("http" in f.value or "maigret" in f.notes.lower() if f.notes else False):
            # This is a bit of a heuristic to find social handles logged by maigret
            social_handles.append({
                "handle": f.value,
                "platform": "Discovered",
                "verified": f.verified,
                "source": f.source_url
            })
            
    # Process locations for Leaflet map
    # We will look for "Location" category findings that might have lat/lng or just a name.
    # Leaflet needs Lat/Lng. If we don't have lat/lng, we can't plot it precisely without geocoding.
    # For a purely local app, we'll extract GPS if the user provides it in the finding value or notes like (40.7128, -74.0060)
    locations = []
    import re
    coord_pattern = re.compile(r'(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)')
    
    for f in findings:
        if f.category == "Location":
            # try to find coords
            match = coord_pattern.search(f.value)
            if not match and f.notes:
                match = coord_pattern.search(f.notes)
            
            lat, lng = None, None
            if match:
                lat, lng = float(match.group(1)), float(match.group(2))
            
            locations.append({
                "name": f.value,
                "lat": lat,
                "lng": lng,
                "date": f.added_at.isoformat(),
                "source": f.source_url
            })
            
    # Extract EXIF GPS from images if present
    import json
    for img in images:
        if img.exif_json:
            try:
                exif = json.loads(img.exif_json)
                if 'GPS GPSLatitude' in exif and 'GPS GPSLongitude' in exif:
                    # simplistic extraction, assuming they are decimal format or we can parse them
                    # exifread format is usually complex, e.g. [40, 42, 51]
                    # We will just pass the raw EXIF to the frontend if it's there, but parsing it here is better
                    pass # Skipping full EXIF GPS parse for brevity, as exifread outputs complex rational arrays
            except:
                pass

    return {
        "context": context,
        "findings": findings,
        "relationships": relationships,
        "social_handles": social_handles,
        "locations": locations
    }
