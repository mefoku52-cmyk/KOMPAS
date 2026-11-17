from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config.settings import settings


def _is_sqlite(database_url: str) -> bool:
    return database_url.startswith("sqlite")


def _connect_args(database_url: str) -> dict:
    if _is_sqlite(database_url):
        return {"check_same_thread": False}
    args = {}
    if settings.db_statement_timeout_ms > 0:
        args["startup_params"] = {
            "options": f"-c statement_timeout={settings.db_statement_timeout_ms}"
        }
    return args


def _engine_kwargs(database_url: str) -> dict:
    kwargs = {
        "connect_args": _connect_args(database_url),
        "future": True,
    }
    if not _is_sqlite(database_url):
        kwargs.update(
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout_seconds,
            pool_recycle=settings.db_pool_recycle_seconds,
            pool_pre_ping=settings.db_pool_pre_ping,
        )
    return kwargs


engine = create_engine(settings.database_url, **_engine_kwargs(settings.database_url))

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True, class_=Session)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
