from typing import Annotated
from dataclasses import dataclass

from packets.pkt import Packet
from serializer.types import U32, MTime, U8

# TODO: bytes type should be Ptype

@dataclass
class SndGetUserInfoRating(Packet):
    uid: U32

@dataclass
class SndGetUserInfoReputation(Packet):
    uid: U32

@dataclass
class SndLoginUser(Packet):
    nick: Annotated[bytes, 0x10+1]
    password: Annotated[bytes, 0x1A+1]
    sth_from_opts: Annotated[bytes, 0xc0]
    b1: U8
    const: Annotated[bytes, 0x4]
    sth0: Annotated[bytes, 0x4]
    sth1: Annotated[bytes, 0x4]


@dataclass
class SndHeartbeat(Packet):
    pass

@dataclass
class SndGetPlayerGamesHistory(Packet):
    uid: U32
    time: MTime  # end time, gets 20 games before this time

@dataclass
class SndGetTemplatesInfo(Packet):
    entries_num: U32
    template_ids: Annotated[list[U32], 'entries_num']

@dataclass
class SndGetPlayersInfo(Packet):
    entries_num: U32
    player_ids: Annotated[list[U32], 'entries_num']

@dataclass
class SndRenameAccount(Packet):
    nick: Annotated[bytes, 0x10+1]
    password: Annotated[bytes, 0x1A+1]
    sth_from_opts: Annotated[bytes, 0xc0]
    b1: U8
    const: Annotated[bytes, 0x4]
    sth0: Annotated[bytes, 0x4]
    sth1: Annotated[bytes, 0x4]
    new_nick: Annotated[bytes, 0x10+1]


@dataclass
class SndRegisterUser(Packet):
    nick: Annotated[bytes, 0x10+1]
    password: Annotated[bytes, 0x1A+1]
    email: Annotated[bytes, 0x81+1]
    sth_from_opts: Annotated[bytes, 0xc0]
    const: Annotated[bytes, 0x4]

    def __post_init__(self):
        # TODO: fixme
        # TODO: xor nick, password, email
        xor_byte = 75

        new_nick = bytearray(b'\x00' * len(self.nick))
        for idx, b in enumerate(reversed(list(self.nick))):
            tmp = b
            b ^= xor_byte
            xor_byte = tmp
            new_nick[idx] = (idx % 7 + 35) + b

        self.nick = bytes(new_nick)


