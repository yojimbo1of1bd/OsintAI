import pytest
from app.routes.chat import build_system_prompt
from app.models import Case, CaseContext, Finding, Relationship
from app.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set up test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine_test = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine_test)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine_test)

def test_assistant_prompt_construction(db_session):
    # Setup data
    case = Case(id=1, name="Test Case", notes="Test Description", status="active")
    db_session.add(case)
    db_session.commit()
    
    context = CaseContext(
        case_id=case.id,
        subject_name="Test Subject",
        social_handles="testhandle1"
    )
    db_session.add(context)
    
    finding = Finding(case_id=case.id, category="Test", value="Test Finding", source_url="local", notes="Notes")
    db_session.add(finding)
    
    rel = Relationship(case_id=case.id, person_a="Test Subject", person_b="Friend", relation="associate", source_url="local")
    db_session.add(rel)
    db_session.commit()
    
    prompt = build_system_prompt(case.id, db_session)
    
    assert "Test Case" in prompt
    assert "Test Subject" in prompt
    assert "Test Finding" in prompt
    assert "Friend" in prompt
    assert "associate" in prompt
    assert "CRITICAL GUARDRAILS" in prompt
