from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlmodel import Session

from common import logger
from db import get_db_url

engine = create_engine(
    url=get_db_url(),
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)


@contextmanager
def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        with session.begin():
            try:
                yield session
            except Exception as e:
                logger.exception("get_db error")
                session.rollback()
                raise
            finally:
                session.close()
