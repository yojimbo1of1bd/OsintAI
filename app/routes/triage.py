import json
import httpx
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Case, Finding, Relationship

router = APIRouter(prefix="/cases/{case_id}/triage", tags=["triage"])


@router.post("")
async def generate_triage_report(
    case_id: int,
    model: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Gather data
    findings = db.query(Finding).filter(Finding.case_id == case_id).all()
    relationships = db.query(Relationship).filter(Relationship.case_id == case_id).all()

    # Build prompt
    prompt_lines = [
        f"You are an expert OSINT investigator analyzing a missing persons case named '{case.name}'.",
        "Here are the findings and relationships we have gathered so far.",
        "Your task: Summarize the case, identify key takeaways, and critically flag any 'thin' or missing information categories (e.g., 'We have location info but no family connections', or 'No online footprint found').",
        "Keep the summary concise and professional. Output your analysis in Markdown format.",
        "\n### Findings:"
    ]

    if not findings:
        prompt_lines.append("No findings logged yet.")
    else:
        for f in findings:
            notes_str = f" - Notes: {f.notes}" if f.notes else ""
            prompt_lines.append(f"- [{f.category}] {f.value}{notes_str}")

    prompt_lines.append("\n### Relationships:")
    if not relationships:
        prompt_lines.append("No relationships logged yet.")
    else:
        for r in relationships:
            prompt_lines.append(f"- {r.person_a} is {r.relation} of {r.person_b}")

    prompt = "\n".join(prompt_lines)

    # Call Ollama
    ollama_url = "http://127.0.0.1:11434/api/generate"
    payload = {
        "model": model or "qwen2.5:7b",
        "prompt": prompt,
        "stream": False
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(ollama_url, json=payload)
            response.raise_for_status()
            result = response.json()
            return {"summary": result.get("response", "")}
    except httpx.ConnectError:
        return {"error": "Could not connect to Ollama. Is it running on localhost:11434?"}
    except Exception as e:
        return {"error": f"Error generating triage report: {str(e)}"}
