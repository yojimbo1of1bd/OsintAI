import asyncio
import logging
import os
import maigret
from maigret import search as maigret_search
from maigret.sites import MaigretDatabase

from app.database import SessionLocal
from app.models import Finding, Case

# Global dictionary to track active scans
active_scans: dict[int, asyncio.Task] = {}

def get_maigret_db():
    db_path = os.path.join(os.path.dirname(maigret.__file__), 'resources', 'data.json')
    db = MaigretDatabase().load_from_path(db_path)
    return db

async def _run_maigret_scan(case_id: int, username: str):
    logger = logging.getLogger("maigret")
    logger.setLevel(logging.WARNING)

    try:
        db = get_maigret_db()
        sites = db.ranked_sites_dict(top=500)
        
        # Explicitly clear-web only, disable Tor/I2P and AI by passing defaults/None
        # is_parsing_enabled=False to keep it fast
        results = await maigret_search(
            username=username,
            site_dict=sites,
            logger=logger,
            timeout=30,
            is_parsing_enabled=False,
            id_type="username",
            no_progressbar=True
        )
        
        db_session = SessionLocal()
        try:
            # Re-fetch case to ensure it hasn't been deleted or stopped during scan
            case = db_session.query(Case).filter(Case.id == case_id).first()
            if not case or case.status != "active":
                return # Scan was run but case is no longer active, discard results

            for site_name, result in results.items():
                if result["status"].is_found():
                    # Create a finding for each positive match
                    finding = Finding(
                        case_id=case_id,
                        category="username_correlation",
                        value=f"{username} on {site_name}",
                        source_url=result["url_user"],
                        notes="Discovered via Maigret correlation.",
                        verified=False
                    )
                    db_session.add(finding)
            db_session.commit()
        finally:
            db_session.close()

    except asyncio.CancelledError:
        # Scan was cancelled via pausing the case
        pass
    except Exception as e:
        logger.error(f"Scan error for case {case_id}: {e}")
    finally:
        # cleanup active_scans
        if case_id in active_scans:
            del active_scans[case_id]


def start_maigret_scan(case_id: int, username: str):
    # Cancel existing scan for this case if one is running
    cancel_scan(case_id)
    task = asyncio.create_task(_run_maigret_scan(case_id, username))
    active_scans[case_id] = task
    return task

def cancel_scan(case_id: int):
    if case_id in active_scans:
        active_scans[case_id].cancel()
        del active_scans[case_id]
