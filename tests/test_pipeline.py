import pytest
import asyncio
from unittest.mock import patch, MagicMock
from app.pipeline import run_pipeline, start_pipeline, get_pipeline_status, active_pipelines
from app.models import Case, CaseContext
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

@pytest.mark.asyncio
@patch('app.pipeline.SessionLocal')
@patch('app.pipeline._run_maigret_scan')
@patch('app.pipeline.httpx.AsyncClient.post')
async def test_pipeline_execution(mock_post, mock_maigret, mock_session_local, db_session):
    # Setup mock session to return our test db session
    mock_session_local.return_value = db_session
    
    # Setup data
    case = Case(id=1, name="Pipeline Test", notes="Test", status="active")
    db_session.add(case)
    db_session.commit()
    
    context = CaseContext(
        case_id=case.id,
        subject_name="Test Subject",
        social_handles="testhandle1, testhandle2"
    )
    db_session.add(context)
    db_session.commit()
    
    # Mock LLM response
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Mocked LLM summary"}
    mock_response.raise_for_status = MagicMock()
    
    mock_post.return_value.__aenter__.return_value = mock_response
    
    # Clear active pipelines dict just in case
    active_pipelines.clear()
    
    # Run the pipeline
    await run_pipeline(case.id)
    
    # Verify maigret was called twice for the two handles
    assert mock_maigret.call_count == 2
    
    # Verify LLM was called
    assert mock_post.called

@pytest.mark.asyncio
@patch('app.pipeline.SessionLocal')
@patch('app.pipeline._run_maigret_scan')
async def test_pipeline_case_pause_interruption(mock_maigret, mock_session_local, db_session):
    # Setup mock session to return our test db session
    mock_session_local.return_value = db_session
    
    # Setup data
    case = Case(id=1, name="Pause Test", notes="Test", status="paused") # Set to paused initially to hit early abort
    db_session.add(case)
    db_session.commit()
    
    context = CaseContext(case_id=case.id, subject_name="Subject", social_handles="handle")
    db_session.add(context)
    db_session.commit()
    
    active_pipelines.clear()
    
    await run_pipeline(case.id)
    
    # Maigret should NOT be called because case is paused
    assert mock_maigret.call_count == 0
