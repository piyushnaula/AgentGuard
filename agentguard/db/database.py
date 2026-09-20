from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from agentguard.core.config import get_settings


class Base(DeclarativeBase):
    pass


from pathlib import Path

settings = get_settings()
db_url = settings.effective_database_url
connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

# Ensure local sqlite database directory exists if path is specified
if db_url.startswith("sqlite:////") or db_url.startswith("sqlite:///"):
    clean_path = db_url.replace("sqlite:////", "/").replace("sqlite:///", "")
    if clean_path and clean_path != ":memory:":
        Path(clean_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(db_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

_tables_created = False


def init_db() -> None:
    global _tables_created
    from agentguard.db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _tables_created = True


def get_db() -> Generator[Session, None, None]:
    global _tables_created
    if not _tables_created:
        init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
