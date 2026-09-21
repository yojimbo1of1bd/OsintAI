import asyncio
import logging
import os
import json
import urllib.parse
from datetime import datetime
import httpx

from app.database import SessionLocal
from app.models import Case, CaseContext, Finding, Image
from app.correlator import _run_maigret_scan

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "data", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Global dictionary to track active pipeline tasks and their status
active_pipelines: dict[int, dict] = {}

def get_pipeline_log_path(case_id: int) -> str:
    return os.path.join(LOG_DIR, f"pipeline_{case_id}.log")

def log_pipeline(case_id: int, message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}\n"
    with open(get_pipeline_log_path(case_id), "a", encoding="utf-8") as f:
        f.write(log_line)
    
    # Update memory status
    if case_id in active_pipelines:
        active_pipelines[case_id]["status"] = message

async def run_pipeline(case_id: int):
    log_pipeline(case_id, "Starting Auto-OSINT Pipeline...")
    db = SessionLocal()
    try:
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case or case.status != "active":
            log_pipeline(case_id, "Case is not active. Aborting pipeline.")
            return

        context = db.query(CaseContext).filter(CaseContext.case_id == case_id).first()
        if not context:
            log_pipeline(case_id, "No case context found. Aborting pipeline.")
            return

        # ---------------------------------------------------------
        # Step 1: Username Sweep
        # ---------------------------------------------------------
        if context.social_handles:
            handles = [h.strip() for h in context.social_handles.split(",") if h.strip()]
            for handle in handles:
                # Check case status before each slow step
                db.refresh(case)
                if case.status != "active":
                    log_pipeline(case_id, "Case paused. Stopping pipeline.")
                    return
                
                log_pipeline(case_id, f"Running username sweep for handle: {handle}")
                await _run_maigret_scan(case_id, handle)
        else:
            log_pipeline(case_id, "No social handles to sweep.")

        # ---------------------------------------------------------
        # Step 2: Public records enrichment
        # ---------------------------------------------------------
        db.refresh(case)
        if case.status != "active": return

        names_to_search = []
        if context.subject_name:
            names_to_search.append(context.subject_name)
        if context.known_aliases:
            names_to_search.extend([a.strip() for a in context.known_aliases.split(",") if a.strip()])
            
        if names_to_search:
            log_pipeline(case_id, f"Generating public records searches for {len(names_to_search)} names.")
            for name in names_to_search:
                encoded_name = urllib.parse.quote_plus(name)
                
                # PACER
                db.add(Finding(
                    case_id=case_id, category="Advanced Subject Info",
                    value=f"PACER Court Records Search: {name}",
                    source_url=f"https://pacer.uscourts.gov/find-case?name={encoded_name}",
                    notes="Auto-generated pipeline link. (Manual review required)", verified=False
                ))
                
                # Voter Records (Generic example)
                db.add(Finding(
                    case_id=case_id, category="Advanced Subject Info",
                    value=f"Voter Records Search: {name}",
                    source_url=f"https://www.voterrecords.com/voters/{encoded_name}/1",
                    notes="Auto-generated pipeline link. (Manual review required)", verified=False
                ))
                
                # FamilyTreeNow
                db.add(Finding(
                    case_id=case_id, category="Advanced Subject Info",
                    value=f"FamilyTreeNow Search: {name}",
                    source_url=f"https://www.familytreenow.com/search/genealogy/results?first={encoded_name}",
                    notes="Auto-generated pipeline link. (Manual review required)", verified=False
                ))
            
            db.commit()
        else:
            log_pipeline(case_id, "No names to search for public records.")

        # ---------------------------------------------------------
        # Step 3: Image batch processing
        # ---------------------------------------------------------
        db.refresh(case)
        if case.status != "active": return
        
        images = db.query(Image).filter(Image.case_id == case_id).all()
        if images:
            log_pipeline(case_id, f"Generating reverse-image-search links for {len(images)} images.")
            for img in images:
                # We assume images are locally hosted at /images/{img.filename}
                # But for reverse image search to work automatically, the URL must be public.
                # Since we are local, we just provide the search portal links.
                db.add(Finding(
                    case_id=case_id, category="Reverse Image Search",
                    value=f"Reverse image search portals for {img.filename}",
                    source_url="https://images.google.com/",
                    notes="Upload image manually to Google, Yandex, or PimEyes.", verified=False
                ))
            db.commit()
        else:
            log_pipeline(case_id, "No images found to process.")

        # ---------------------------------------------------------
        # Step 4: LLM synthesis
        # ---------------------------------------------------------
        db.refresh(case)
        if case.status != "active": return
        
        log_pipeline(case_id, "Running LLM synthesis on updated case data...")
        
        # Gather all findings
        findings = db.query(Finding).filter(Finding.case_id == case_id).all()
        findings_text = "\n".join([f"- [{f.category}] {f.value}" for f in findings])
        
        prompt = f"""You are an OSINT pipeline summarizer. 
Review the following automated findings for the case '{case.name}'.
Summarize what the automated pipeline uncovered, flag any contradictions, and suggest top manual follow-up actions.
Do NOT hallucinate. Only reference the data below.

FINDINGS:
{findings_text}
"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post("http://127.0.0.1:11434/api/generate", json={
                    "model": "qwen3:8b", # Or fallback to qwen2.5:7b if not present, assume user has it
                    "prompt": prompt,
                    "stream": False
                })
                response.raise_for_status()
                summary = response.json().get("response", "")
                
                db.add(Finding(
                    case_id=case_id, category="Pipeline Summary",
                    value="Pipeline Auto-Synthesis Complete",
                    source_url="local://pipeline",
                    notes=summary, verified=False
                ))
                db.commit()
                log_pipeline(case_id, "LLM synthesis completed successfully.")
        except Exception as e:
            log_pipeline(case_id, f"LLM synthesis failed: {e}")

        log_pipeline(case_id, "Pipeline complete.")

    except asyncio.CancelledError:
        log_pipeline(case_id, "Pipeline cancelled by user.")
    except Exception as e:
        log_pipeline(case_id, f"Pipeline encountered an error: {str(e)}")
    finally:
        db.close()
        if case_id in active_pipelines:
            active_pipelines[case_id]["is_running"] = False

def start_pipeline(case_id: int) -> bool:
    if case_id in active_pipelines and active_pipelines[case_id].get("is_running"):
        return False # Already running
    
    # clear log file
    open(get_pipeline_log_path(case_id), 'w').close()
    
    task = asyncio.create_task(run_pipeline(case_id))
    active_pipelines[case_id] = {
        "task": task,
        "is_running": True,
        "status": "Starting..."
    }
    return True

def get_pipeline_status(case_id: int) -> dict:
    state = active_pipelines.get(case_id, {"is_running": False, "status": "Not started"})
    
    log_content = ""
    log_path = get_pipeline_log_path(case_id)
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            log_content = f.read()
            
    return {
        "is_running": state["is_running"],
        "status": state["status"],
        "log": log_content
    }
