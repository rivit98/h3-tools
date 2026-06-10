from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter
from sqlmodel.ext.asyncio.session import AsyncSession

from db.methods import get_player_by_id
from db.models import PlayerBase
from db.async_session import get_session

api_router = APIRouter()


@api_router.get('/players/{uid}', response_model=PlayerBase)
async def players(uid: int, db: AsyncSession = Depends(get_session)):
    player = await get_player_by_id(db, uid)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    return player
