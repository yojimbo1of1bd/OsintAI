import pytest
from app.routes.map import get_map_data_for_case
from app.models import Case, Relationship
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

def test_map_data_serialization(db_session):
    case = Case(name="Test Case", notes="Test Description", status="active")
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    
    rel = Relationship(case_id=case.id, person_a="Alice", person_b="Bob", relation="friend", source_url="local")
    db_session.add(rel)
    db_session.commit()
    
    data = get_map_data_for_case(case.id, db_session)
    
    # We test that the relationships are pulled properly
    relationships = data["relationships"]
    assert len(relationships) == 1
    assert relationships[0].person_a == "Alice"
    assert relationships[0].person_b == "Bob"
    assert relationships[0].relation == "friend"
