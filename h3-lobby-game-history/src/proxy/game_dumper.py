from pwn import *
from sqlalchemy import select

from serializer.types import MTime, U32
from db.models import Player
from db.sync_session import get_session
from common import logger
from packets.hooks import add_hook, prepare_message
from packets.snd import SndGetPlayerGamesHistory
from packets.rcv import RcvGetPlayerGamesHistoryResponse

DATA_DIR = "../games_scrapped"

sem = threading.Semaphore()
last_time = MTime(-1)
last_uid = -1


def save_callback(obj: RcvGetPlayerGamesHistoryResponse):
    global last_time, last_uid

    last_time = None
    if len(obj.games):
        ent = sorted(obj.games, key=lambda e: e.end_datetime)
        first = ent[0]
        last_time = first.end_datetime

        for game in obj.games:
            try:
                with open(f"{DATA_DIR}/{last_uid}--{game.game_id}", "wb") as f:
                    pickle.dump(game, f)
            except Exception as e:
                logger.error(e)

            logger.debug(game)

    sem.release()


def get_players():
    players = []
    with get_session() as session:
        for row in session.execute(select(Player.id).order_by(Player.id)):
            pid = row[0]
            players.append(pid)
    return players


def get_last_scrapped():
    uids = []
    for f in Path(DATA_DIR).iterdir():
        if not f.is_file(): continue

        uid, ts = f.name.split('--')
        uids.append(int(uid))

    uids = sorted(uids)
    try:
        return uids[-2]  # just to be sure
    except:
        return -1

def game_scrap_thread(sock):
    global last_time, last_uid
    global sem

    sleep(1)  # delay it a bit
    os.makedirs(DATA_DIR, exist_ok=True)
    add_hook(RcvGetPlayerGamesHistoryResponse, save_callback)

    players = get_players()
    last_scrapped = get_last_scrapped()

    players = list(filter(lambda id: id >= last_scrapped, players))
    for pid in players:
        last_time = MTime(-1)
        sem = threading.Semaphore()
        last_uid = pid

        while True:
            res = sem.acquire(timeout=5)
            if not res:
                logger.info("timeout exceeded")
                break

            if last_time is None:
                # this means that last request returned 0 games
                # break and check next player
                break

            packet = SndGetPlayerGamesHistory(
                uid=U32(pid),
                time=last_time
            )
            logger.info(packet)
            msg = prepare_message(packet)
            sock.send(msg)

    logger.info("DONE")
