import os
import json
import uuid
import exifread
from fastapi import APIRouter, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Case, Image

router = APIRouter(prefix="/cases/{case_id}/images", tags=["images"])

def extract_exif(file_path: str) -> str:
    try:
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            exif_data = {}
            for tag in tags.keys():
                if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
                    exif_data[tag] = str(tags[tag])
            return json.dumps(exif_data)
    except Exception as e:
        return json.dumps({"error": str(e)})

@router.post("/upload")
async def upload_image(
    case_id: int,
    source_url: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    case_dir = os.path.join("data", "images", str(case_id))
    os.makedirs(case_dir, exist_ok=True)
    
    # Generate a safe filename
    ext = os.path.splitext(file.filename)[1]
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(case_dir, safe_filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    exif_json = extract_exif(file_path)
    
    db_image = Image(
        case_id=case_id,
        path=file_path,
        source_url=source_url.strip(),
        exif_json=exif_json
    )
    db.add(db_image)
    db.commit()
    
    return RedirectResponse(url=f"/cases/{case_id}", status_code=303)

@router.post("/{image_id}/delete")
async def delete_image(
    case_id: int, 
    image_id: int, 
    db: Session = Depends(get_db)
):
    image = db.query(Image).filter(
        Image.id == image_id, 
        Image.case_id == case_id
    ).first()
    
    if image:
        db.delete(image)
        db.commit()
        if os.path.exists(image.path):
            try:
                os.remove(image.path)
            except Exception:
                pass
                
    return RedirectResponse(url=f"/cases/{case_id}", status_code=303)
