import os
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, Boolean, String, Text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm import DeclarativeBase

POSTGRES_URL = os.getenv("POSTGRES_URL")
engine = create_engine(POSTGRES_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)


# sqlalchemy 2.0 convention
class Base(DeclarativeBase):
    pass


# Use async session in prod
def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def time_now_iso() -> str:
    return datetime.now().isoformat()


class DocumentModel(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(Text)
    in_vector_db = Column(Boolean, default=False)
    created_at = Column(String, default=time_now_iso)
    updated_at = Column(String, default=time_now_iso, onupdate=time_now_iso)
