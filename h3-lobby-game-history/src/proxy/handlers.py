import struct

from pwn import *

from packets import msg_types
from proxy.consts import fake_login
# from consts import fake_login
from serializer import serializer
# from game_dumper import game_scrap_thread
from common import logger

USERNAME = 'luq4321'
PASSWORD = 'asdf'


def controlled_send(sock):
    # login
    print(fake_login)
    sock.send(fake_login)
    print('fake_login')

    # heartbeat = Thread(target=heartbeat_thread, args=(sock, ))
    # heartbeat.start()

    # scrapper = Thread(target=players_scrap_thread, args=(sock, ))
    # scrapper.start()

    # game_scrapper = Thread(target=game_scrap_thread, args=(sock, ))
    # game_scrapper.start()

    # heartbeat.join()


#  API <-------- thread <-------- game
#  API ------->  thread --------> game

def send_th(recv_from, send_to):
    if recv_from is None:
        controlled_send(send_to)
        return

    # reads from game sock, forwards to h3lobby
    while True:
        data = recv_from.recv(0x1000, timeout=1)
        if not data: continue

        msg_len = u16(data[:2])
        msg_type = u16(data[2:4])

        if data[:4] == b'\xfd\x00\x83\x00':
            # patch login message
            data = fake_login
            fake_login = data.replace(b'EYZV31V2VW-W7754360EYLC', b'AYZV31V2VW-W7754360EYLA') # change hwid
            data = fake_login
            print(data)

        dataclass = msg_types.get(msg_type)
        if dataclass:
            packet = serializer.parse(dataclass, data[4:])
            if packet.print_enabled():
                logger.info(f'SEND: {packet}')

            # fire_hooks(packet)
        else:
            msg_type = u16(data[2:4]) - 0x33
            logger.info(f'SEND({len(data)}): [len {msg_len:#x}] [type {msg_type:#x}] {data}')

        send_to.send(data)


def recv_th(recv_from, send_to):
    buf = bytearray()
    expected_len = 0

    while True:
        data = recv_from.recv(0x1000, timeout=1)
        if not data: continue

        if expected_len:
            expected_len -= len(data)
            # print(f"expected_len dec: {expected_len} {len(data)}")

        buf.extend(data)
        if expected_len > 0:
            # print(f"not enough, continue")
            continue

        data = bytes(buf)
        msg_len = u16(data[:2])
        msg_type = u16(data[2:4])

        dataclass = msg_types.get(msg_type)
        if dataclass:
            # if type is known, we know how many data/packets we need
            if not expected_len and hasattr(dataclass, 'packets_needed'):
                expected_len = msg_len - len(data)
                # print(f"expected_len: {expected_len}")
                continue

            try:
                packet = serializer.parse(dataclass, data[4:])
                if packet.print_enabled():
                    logger.info(f'RECV: {packet}')

                # fire_hooks(packet)
            except struct.error as e:
                logger.info(f'raw data was {data}')
                logger.exception("msg decode exception")

        else:
            logger.info(f'RECV({len(data)}): [len {msg_len:#x}] [type {msg_type - 0x33:#x}] {data}')

        expected_len = 0
        buf.clear()

        if send_to:
            send_to.send(data)
