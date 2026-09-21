import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import os
import logging

from app.database import get_db
from app.models import Case, Finding, Relationship, CaseContext

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cases", tags=["chat"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

@router.get("/{case_id}/chat", response_class=HTMLResponse)
async def view_chat(request: Request, case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    return templates.TemplateResponse("case_chat.html", {
        "request": request, 
        "case": case
    })

def build_system_prompt(case_id: int, db: Session) -> str:
    case = db.query(Case).filter(Case.id == case_id).first()
    context = db.query(CaseContext).filter(CaseContext.case_id == case_id).first()
    findings = db.query(Finding).filter(Finding.case_id == case_id).all()
    relationships = db.query(Relationship).filter(Relationship.case_id == case_id).all()

    prompt_lines = [
        f"You are Lodestar, an expert OSINT investigator and analytical assistant for a missing persons case named '{case.name}'.",
        "Your role is to synthesize data, identify patterns, suggest investigative avenues, and answer questions based strictly on the provided case data.",
        "CRITICAL GUARDRAILS:",
        "- You are operating in a passive-OSINT context (e.g., Trace Labs CTF).",
        "- NEVER advise logging in, friending, following, or actively contacting the subject, family, or friends.",
        "- DO NOT suggest bypassing authentication, rate limits, or scraping ToS-restricted sites (like Facebook or Instagram).",
        "- If asked to do something that violates these rules, decline and explain why.",
        "\n--- CASE CONTEXT ---"
    ]

    if context:
        if context.subject_name: prompt_lines.append(f"Subject Name: {context.subject_name}")
        if context.known_aliases: prompt_lines.append(f"Aliases: {context.known_aliases}")
        if context.age_range: prompt_lines.append(f"Age: {context.age_range}")
        if context.last_known_location: prompt_lines.append(f"Last Known Location: {context.last_known_location}")
        if context.last_seen_date: prompt_lines.append(f"Last Seen: {context.last_seen_date}")
        if context.physical_description: prompt_lines.append(f"Physical Desc: {context.physical_description}")
        if context.social_handles: prompt_lines.append(f"Social Handles: {context.social_handles}")
        if context.known_associates: prompt_lines.append(f"Known Associates: {context.known_associates}")
        if context.life_events: prompt_lines.append(f"Life Events: {context.life_events}")
        if context.additional_notes: prompt_lines.append(f"Notes: {context.additional_notes}")
    else:
        prompt_lines.append("No context seeded.")

    prompt_lines.append("\n--- FINDINGS ---")
    if findings:
        for f in findings:
            notes = f" (Notes: {f.notes})" if f.notes else ""
            prompt_lines.append(f"[{f.category}] {f.value}{notes}")
    else:
        prompt_lines.append("No findings recorded.")

    prompt_lines.append("\n--- RELATIONSHIPS ---")
    if relationships:
        for r in relationships:
            prompt_lines.append(f"{r.person_a} -> {r.person_b} ({r.relation})")
    else:
        prompt_lines.append("No relationships recorded.")

    return "\n".join(prompt_lines)


@router.post("/{case_id}/chat/message")
async def send_chat_message(
    case_id: int,
    messages: list = Body(..., embed=True),
    model: str = Body(default="qwen3:8b", embed=True),
    db: Session = Depends(get_db)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Inject system prompt at the beginning of the messages array
    system_prompt = build_system_prompt(case_id, db)
    
    ollama_messages = [{"role": "system", "content": system_prompt}] + messages

    ollama_url = "http://127.0.0.1:11434/api/chat"
    payload = {
        "model": model,
        "messages": ollama_messages,
        "stream": False
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(ollama_url, json=payload)
            response.raise_for_status()
            result = response.json()
            return {"message": result.get("message", {}).get("content", "")}
    except httpx.ConnectError:
        return JSONResponse(status_code=503, content={"error": "Could not connect to Ollama. Is it running on localhost:11434?"})
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return JSONResponse(status_code=500, content={"error": f"Error communicating with AI: {str(e)}"})
