from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .database import Base
from core.settings import settings

DATABASE_URL = settings.app.database_url

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
