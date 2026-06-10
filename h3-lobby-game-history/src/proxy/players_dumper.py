import pickle
from threading import Semaphore

from pwn import *

from common import logger
from packets.hooks import add_hook, prepare_message
from packets.rcv import RcvGetPlayersInfoResponse
from packets.snd import SndGetPlayersInfo
from utils import batched

DATA_DIR = "players_scrapped"


def save_callback(obj: RcvGetPlayersInfoResponse, sem: Semaphore):
    logger.info(f"Received GetPlayersInfoResponse with {obj.entries_num} entries")
    for player in obj.players:
        try:
            with open(f"{DATA_DIR}/{player.id}", "wb") as f:
                pickle.dump(player, f)

            logger.debug(player)
        except Exception as e:
            logger.error(e)

    sem.release()


def players_scrap_thread(sock):
    sleep(1)  # delay it a bit
    os.makedirs(DATA_DIR, exist_ok=True)

    sem = Semaphore()
    add_hook(RcvGetPlayersInfoResponse, lambda obj: save_callback(obj, sem))

    # server limits batch size :(
    # max 20 entries per query
    for ids in batched(range(0, 0x200000), 20):
        res = sem.acquire(timeout=5)
        if not res:
            logger.info(f"timeout exceeded: {packet}")
            sem.release()
            continue

        packet = SndGetPlayersInfo(
            entries_num=len(ids),
            player_ids=list(ids)
        )
        msg = prepare_message(packet)
        sock.send(msg)

    logger.info("DONE")

