import asyncio
import struct

from pwn import u16

from common import logger
from config import Config
from executor.account import Account
from packets import msg_types
from executor.request import Request
from packets.pkt import Packet
from packets.hooks import HookManager
from packets.snd import SndHeartbeat
from proxy.consts import fake_login
from proxy.h3_socket import Socket
from serializer import serializer


class LobbyAPIClient:
    """
    Class used for communicating with the lobby API
    """

    def __init__(self, api_socket: Socket, config: Config, account: Account):
        self.account = account
        self.api_sock = api_socket
        self.hook_manager = HookManager()
        self.response_timeout = config.lobby_api_client.request_timeout
        self.heartbeat_task = None
        self.receiver_task = None

    async def heartbeat(self):
        while True:
            await self.api_sock.send_pkt(SndHeartbeat())
            await asyncio.sleep(30)

    async def login(self):
        logger.info(f"Logging as {self.account}")
        # TODO(rev): login user using account
        # pkt = SndLoginUser()
        # self.api_sock.send_pkt(pkt)
        await self.api_sock.send_raw(fake_login)

    async def __aenter__(self):
        await self.login()
        self.receiver_task = asyncio.ensure_future(self.recv())
        self.heartbeat_task = asyncio.ensure_future(self.heartbeat())
        return self

    async def __aexit__(self, *args, **kwargs):
        self.heartbeat_task.cancel()
        self.receiver_task.cancel()

    async def execute_request(self, request: Request):
        """
        Sends request to the lobby.
        """

        logger.info(f"Execute request")

        response_received = asyncio.Event()

        def response_callback(obj: Packet):
            request.response = obj
            response_received.set()

        # install hook for expected response message type
        hook_idx = self.hook_manager.install_hook(
            request.resp_type,
            response_callback
        )

        # send a message
        snd_pkt = request.to_packet()
        await self.api_sock.send_pkt(snd_pkt)

        # check if response was received in the expected time
        try:
            await asyncio.wait_for(response_received.wait(), self.response_timeout)
        except TimeoutError as ex:
            logger.error(f"Request timed out: {snd_pkt.name()}")
            raise ex
        finally:
            # remove installed hook
            self.hook_manager.remove_hook_by_idx(hook_idx)
            logger.info("Request finished")

        return request.response

    async def recv(self):
        """
        Receives from API, forwards to game
        """

        logger.info("Starting recv task")
        # TODO: refactor this to automatically detect packets needed - Q: what about packet reordering?
        # TODO: cleanup for simple use case
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

                    self.hook_manager.fire_hooks(packet)
                except struct.error as e:
                    logger.info(f'raw data was {data}')
                    logger.exception("msg decode exception")
            # else:
                # logger.info(f'RECV({len(data)}): [len {msg_len:#x}] [type {msg_type - 0x33:#x}] {data}')

            expected_len = 0
            buf.clear()