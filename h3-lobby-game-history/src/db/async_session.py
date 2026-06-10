from typing import AsyncIterator

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from common import logger
from db import get_db_url

async_engine = create_async_engine(
    url=get_db_url(),
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSession(async_engine) as session:
        async with session.begin():
            try:
                yield session
            except Exception as e:
                logger.exception("get_db error")
                await session.rollback()
                raise
            finally:
                await session.close()
