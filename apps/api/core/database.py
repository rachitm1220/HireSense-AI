from sqlmodel import SQLModel, create_engine, Session
from .config import settings

# Engine setup
engine = create_engine(settings.DATABASE_URL, echo=True)

def create_db_and_tables():
    # This automatically creates all tables defined by SQLModel classes.
    # No migrations needed during development!
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
