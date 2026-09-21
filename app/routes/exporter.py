import csv
import io
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Case, Finding, Relationship

router = APIRouter(prefix="/cases/{case_id}/export", tags=["exporter"])


@router.get("/csv")
def export_csv(case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    findings = db.query(Finding).filter(Finding.case_id == case_id).all()
    relationships = db.query(Relationship).filter(Relationship.case_id == case_id).all()

    # We use an in-memory string buffer to hold the CSV data
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write Findings header
    writer.writerow(["Type", "Category", "Value", "Source URL", "Explanation/Notes", "Verified"])
    
    for f in findings:
        source_url = f.source_url if f.source_url else "[MISSING SOURCE_URL]"
        writer.writerow(["Finding", f.category, f.value, source_url, f.notes, f.verified])
        
    # Write a separator if we have both
    if findings and relationships:
        writer.writerow([])
        
    # Write Relationships
    if relationships:
        writer.writerow(["Type", "Person A", "Relation", "Person B", "Source URL", "Added At"])
        for r in relationships:
            source_url = r.source_url if r.source_url else "[MISSING SOURCE_URL]"
            writer.writerow(["Relationship", r.person_a, r.relation, r.person_b, source_url, r.added_at.strftime("%Y-%m-%d %H:%M")])
            
    # Reset buffer pointer
    output.seek(0)
    
    # Format a safe filename
    filename = f"export_{case.id}_{case.name.replace(' ', '_')}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/txt")
def export_txt(case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    findings = db.query(Finding).filter(Finding.case_id == case_id).all()
    relationships = db.query(Relationship).filter(Relationship.case_id == case_id).all()

    lines = []
    lines.append(f"CASE REPORT: {case.name}")
    lines.append(f"Status: {case.status}")
    lines.append(f"Created At: {case.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("=" * 40)
    
    if case.notes:
        lines.append(f"Notes:\n{case.notes}")
        lines.append("-" * 40)
        
    lines.append("\n### FINDINGS ###")
    if not findings:
        lines.append("No findings recorded.")
    else:
        for i, f in enumerate(findings, 1):
            source_url = f.source_url if f.source_url else "[MISSING SOURCE_URL]"
            verified = "VERIFIED" if f.verified else "UNVERIFIED"
            lines.append(f"\n{i}. [{f.category}] {f.value} ({verified})")
            lines.append(f"   Source: {source_url}")
            if f.notes:
                lines.append(f"   Notes: {f.notes}")
                
    lines.append("\n### RELATIONSHIPS ###")
    if not relationships:
        lines.append("No relationships recorded.")
    else:
        for i, r in enumerate(relationships, 1):
            source_url = r.source_url if r.source_url else "[MISSING SOURCE_URL]"
            lines.append(f"\n{i}. {r.person_a} --[{r.relation}]--> {r.person_b}")
            lines.append(f"   Source: {source_url}")
            
    content = "\n".join(lines)
    
    filename = f"export_{case.id}_{case.name.replace(' ', '_')}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.txt"
    
    return PlainTextResponse(
        content=content,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
