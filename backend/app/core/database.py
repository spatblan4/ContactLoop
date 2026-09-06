from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def _create_engine():
    url = settings.sqlalchemy_url
    if url.startswith("sqlite"):
        path = url.removeprefix("sqlite:///")
        if path and path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url)


engine = _create_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def database_mode() -> str:
    return "postgres" if engine.dialect.name == "postgresql" else "sqlite"


def init_db() -> None:
    from app.models import Base

    Base.metadata.create_all(engine)
