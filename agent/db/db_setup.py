import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# Database URL
DB_PATH = os.getenv("SQLITE_DB_PATH", "./data/agents.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine with appropriate arguments
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# Create SessionLocal factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_database() -> None:
    """Create all tables in the database."""
    try:
        Base.metadata.create_all(bind=engine)
        print("Database and tables created successfully.")
    except Exception as e:
        print(f"An error occurred while creating the database: {e}")

def get_db():
    """Dependency to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    create_database()
