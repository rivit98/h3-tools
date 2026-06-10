from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from db.models import Player, PlayerBase


async def get_player_by_id(db: AsyncSession, uid: int) -> PlayerBase | None:
    query = select(Player).where(Player.id == uid)
    player = await db.exec(query)
    return player.first()


async def get_player_by_name(db: AsyncSession, name: str) -> PlayerBase | None:
    query = select(Player).where(Player.name == name)
    player = await db.exec(query)
    return player.first()

