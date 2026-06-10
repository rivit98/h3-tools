from contextlib import nullcontext

import struct

from common import logger
# from packets import msg_types, fake_login
from proxy.h3_socket import Socket, Server
import asyncio
from pwn import u16

from serializer import serializer

from config import config


#  API <-------- coro <-------- game
#  API ------->  coro --------> game




class Proxy:
    def __init__(self, account, local_ip=None):
        logger.debug(f"Creating Proxy object for account: {account}")
        self.account = account
        self.api_sock = Socket(config.lobby.host, config.lobby.port)

        # if we have local game instance running, we need to act as a game lobby server
        self.game_sock = Server(local_ip, config.lobby.port)

    async def run_proxy(self):
        logger.info(f"Running proxy")

        async with self.game_sock if self.game_sock else nullcontext():
            async with self.api_sock:
                receiver = asyncio.create_task(self.recv_task())
                forwarder = asyncio.create_task(self.send_task())

                await forwarder
                # if we are done with sending, just close receiver
                receiver.cancel()

                logger.info("run_proxy completed")

    async def recv_task(self):
        """
        Receives from API, forwards to game
        """

        # TODO: refactor this to automatically detect packets needed - Q: what about packet reordering?
        buf = bytearray()
        expected_len = 0

        while True:
            data = await self.api_sock.recv(0x1000)
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
                if not expected_len and dataclass.packets_needed() > 1:
                    expected_len = msg_len - len(data)
                    # print(f"expected_len: {expected_len}")
                    continue

                try:
                    packet = serializer.parse(dataclass, data[4:])
                    if packet.print_enabled():
                        logger.info(f'RECV: {packet}')

                    fire_hooks(packet)
                except struct.error as e:
                    logger.info(f'raw data was {data}')
                    logger.exception("msg decode exception")

            else:
                logger.info(f'RECV({len(data)}): [len {msg_len:#x}] [type {msg_type - 0x33:#x}] {data}')

            expected_len = 0
            buf.clear()

            await self.game_sock.send_raw(data)

    async def send_task(self):
        """
        Receives from game, forwards to API
        """

        # reads from game sock, forwards to h3lobby
        while True:
            data = await self.game_sock.recv(0x1000)
            if not data: continue

            msg_len = u16(data[:2])
            msg_type = u16(data[2:4])

            if data[:4] == b'\xfd\x00\x83\x00':
                # patch login message
                global fake_login
                data = fake_login
                fake_login = data.replace(b'EYZV31V2VW-W7754360EYLC', b'AYZV31V2VW-W7754360EYLA')  # change hwid
                data = fake_login

            dataclass = msg_types.get(msg_type)
            if dataclass:
                packet = serializer.parse(dataclass, data[4:])
                if packet.print_enabled():
                    logger.info(f'SEND: {packet}')

                fire_hooks(packet)
            else:
                msg_type = u16(data[2:4]) - 0x33
                logger.info(f'SEND({len(data)}): [len {msg_len:#x}] [type {msg_type:#x}] {data}')

            await self.api_sock.send_raw(data)


