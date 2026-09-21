import requests
import sys
import os

# Ensure app is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = "http://127.0.0.1:8420"

print("--- Testing Lodestar Phase 2 ---")

# Create a case
resp = requests.post(f"{BASE_URL}/cases/create", data={"name": "Phase 2 Test Case", "notes": "Test notes"}, allow_redirects=False)
print("Create case redirect status:", resp.status_code)

# Query DB
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Case, Finding

engine = create_engine(f"sqlite:///data/lodestar.db")
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

case = db.query(Case).filter(Case.name == "Phase 2 Test Case").order_by(Case.id.desc()).first()
print(f"Created Case ID: {case.id}")

# Create finding
resp = requests.post(
    f"{BASE_URL}/cases/{case.id}/findings/create",
    data={
        "category": "Basic Subject Info",
        "value": "johndoe test",
        "source_url": "https://example.com/johndoe",
        "notes": "Test finding"
    },
    allow_redirects=False
)
print("Create finding redirect status:", resp.status_code)

findings = db.query(Finding).filter(Finding.case_id == case.id).all()
print("Findings count in DB:", len(findings))
if findings:
    print("Finding value:", findings[0].value)
    print("Finding verified:", findings[0].verified)

# Delete finding
if findings:
    resp = requests.post(f"{BASE_URL}/cases/{case.id}/findings/{findings[0].id}/delete", allow_redirects=False)
    print("Delete finding redirect status:", resp.status_code)

findings_after = db.query(Finding).filter(Finding.case_id == case.id).all()
print("Findings count after delete:", len(findings_after))

# Delete case to cleanup
resp = requests.post(f"{BASE_URL}/cases/{case.id}/delete", allow_redirects=False)
print("Delete case redirect status:", resp.status_code)
