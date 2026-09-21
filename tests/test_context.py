import pytest
from app.database import SessionLocal, Base, engine
from app.models import Case, CaseContext

# Create a fresh database for testing (in-memory SQLite is best if we configure it, but here we'll use a test db or just rollback)
# For simplicity, we can create a temporary file or use the existing test setup if any.
# Let's override the database with an in-memory one for tests.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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

def test_create_case_context(db_session):
    # 1. Create case
    case = Case(name="Test Case", notes="Test Description", status="active")
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    
    # 2. Create Context
    context = CaseContext(
        case_id=case.id,
        subject_name="John Doe",
        known_aliases="J.D.",
        social_handles="johndoe123",
        last_known_location="New York, NY"
    )
    db_session.add(context)
    db_session.commit()
    db_session.refresh(context)
    
    # 3. Read
    fetched = db_session.query(CaseContext).filter_by(case_id=case.id).first()
    assert fetched is not None
    assert fetched.subject_name == "John Doe"
    
    # 4. Update
    fetched.subject_name = "Jane Doe"
    db_session.commit()
    
    fetched_again = db_session.query(CaseContext).filter_by(case_id=case.id).first()
    assert fetched_again.subject_name == "Jane Doe"
    
    # 5. Delete (cascade check or manual delete)
    db_session.delete(fetched_again)
    db_session.commit()
    
    deleted = db_session.query(CaseContext).filter_by(case_id=case.id).first()
    assert deleted is None
