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
if db_url.startswith("sqlite"):
    clean_path = db_url.replace("sqlite:////", "/").replace("sqlite:///", "")
    if clean_path and clean_path != ":memory:":
        try:
            parent_dir = Path(clean_path).parent
            parent_dir.mkdir(parents=True, exist_ok=True)
            # Test write access
            test_file = parent_dir / ".write_test"
            test_file.touch(exist_ok=True)
            test_file.unlink(missing_ok=True)
        except OSError:
            # Filesystem is read-only (e.g. AWS Lambda / Vercel), fallback to /tmp
            db_url = "sqlite:////tmp/agentguard.db"

engine = create_engine(db_url, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

_tables_created = False


def init_db() -> None:
    global _tables_created
    try:
        from agentguard.db import models  # noqa: F401

        Base.metadata.create_all(bind=engine)
        _tables_created = True
    except Exception as e:
        import sys
        print(f"Warning: Failed to create database tables: {e}", file=sys.stderr)


def get_db() -> Generator[Session, None, None]:
    global _tables_created
    if not _tables_created:
        init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
