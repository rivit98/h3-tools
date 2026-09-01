from datetime import datetime

from sqlalchemy import func, DateTime, Column
from sqlmodel import SQLModel, Field, Relationship


class PlayerBase(SQLModel):
    id: int = Field(primary_key=True, unique=True)
    name: str = Field()

    def __str__(self):
        return f"{self.id} - {self.name}"


class Player(PlayerBase, table=True):
    __tablename__ = "player"

    time: datetime = Field(sa_column=Column(DateTime, server_default=func.now(), onupdate=func.current_timestamp(), nullable=False))


class Template(SQLModel, table=True):
    __tablename__ = "template"

    id: int = Field(primary_key=True, unique=True)
    name: str = Field()


class PlayerGameInfo(SQLModel, table=True):
    __tablename__ = "player_game_info"

    id: int = Field(primary_key=True, unique=True)
    player_id: int = Field(foreign_key='player.id')
    game_id: int = Field(foreign_key='game.id')
    game: 'Game' = Relationship(back_populates="players")

    color: int = Field()
    town: int = Field()
    hero: int = Field()

    color2: int = Field()
    town2: int = Field()
    hero2: int = Field()

    rating_before: int = Field()
    rating_after: int = Field()


class Game(SQLModel, table=True):
    __tablename__ = "game"

    id: int = Field(primary_key=True, unique=True)
    template_id: int = Field(foreign_key='template.id')
    game_result: int = Field()
    restarts: int = Field()
    start_datetime: datetime = Field(DateTime)
    end_datetime: datetime = Field(DateTime)

    players: list["PlayerGameInfo"] = Relationship(back_populates='game')
