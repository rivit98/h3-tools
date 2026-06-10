from dataclasses import dataclass
from typing import Annotated

from packets.pkt import Packet
from serializer.types import U32, U8, I32, U16, MTime, I8


@dataclass
class GameHistoryEntryPlayer(Packet):
    uid: U32
    color2: U8
    town2: I8
    hero2: I32
    color1: I8
    town1: U8
    hero1: I32
    gap1: Annotated[bytes, 0x5]
    password: Annotated[bytes, 0x10 + 1]
    rating_before: U32
    rating_after: U32

@dataclass
class GameHistoryEntry(Packet):
    game_id: U32
    template_id: I32
    gap0: Annotated[bytes, 3]
    game_result: U16
    restarts: U16
    if_ranked_then_not_0: U32
    start_datetime: MTime
    end_datetime: MTime
    players: Annotated[list[GameHistoryEntryPlayer], 2]

@dataclass
class RcvUserInfoRating(Packet):
    uid: U32
    rating: U32

@dataclass
class RcvUserInfoReputation(Packet):
    uid: U32
    reputation: I32

@dataclass
class RcvUserJoined(Packet):
    c: U16
    d: U16
    uid: U32
    rating: U32
    reputation: I32
    nick: Annotated[bytes, 0x10]
    gap1: Annotated[bytes, 0x2]
    perms: U16
    flags: U16
    gap2: Annotated[bytes, 0x4]

    @staticmethod
    def print_enabled():
        return False

@dataclass
class RcvGetPlayerGamesHistoryResponse(Packet):
    a: U32
    entries_num: U32
    c: I32
    games: Annotated[list[GameHistoryEntry], 'entries_num']

    @staticmethod
    def packets_needed():
        return 2

@dataclass
class TemplateInfo(Packet):
    id: U32
    name: Annotated[bytes, 65]  # FIXME: this is not true, but it looks like template name len is not static

@dataclass
class RcvGetTemplatesInfoResponse(Packet):
    entries_num: U32
    templates: Annotated[list[TemplateInfo], 'entries_num']

@dataclass
class PlayerInfo(Packet):
    id: U32
    gap: Annotated[bytes, 2]
    nick: Annotated[bytes, 17]  # looks like buffer is not zeroed fully

@dataclass
class RcvGetPlayersInfoResponse(Packet):
    entries_num: U32
    players: Annotated[list[PlayerInfo], 'entries_num']


