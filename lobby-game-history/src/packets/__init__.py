from packets.snd import *
from packets.rcv import *

msg_types: dict[int, Packet] = {
    0x33: RcvUserJoined,

    0x68: SndGetUserInfoRating,
    0x69: RcvUserInfoRating,

    0x74: SndGetUserInfoReputation,
    0x75: RcvUserInfoReputation,

    0x82: SndRegisterUser,
    0x83: SndLoginUser,

    0x89: SndRenameAccount,

    0x95: SndHeartbeat,

    0x97: SndGetPlayerGamesHistory,
    0x98: RcvGetPlayerGamesHistoryResponse,

    0x99: SndGetTemplatesInfo,
    0x9a: RcvGetTemplatesInfoResponse,

    0x9b: SndGetPlayersInfo,
    0x9c: RcvGetPlayersInfoResponse,
}

rev_msg_types = {v:k for k,v in msg_types.items()}