import asyncio
from asyncio import StreamReader, StreamWriter

from pwnlib.util.packing import flat
from pwn import p16

from packets import rev_msg_types
from packets.pkt import Packet


class Socket:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.reader: StreamReader = None
        self.writer: StreamWriter = None

    async def __aenter__(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        return self

    async def __aexit__(self, *args, **kwargs):
        self.writer.close()
        await self.writer.wait_closed()

    async def recv(self, n):
        return await self.reader.read(n)

    async def send_raw(self, payload):
        self.writer.write(payload)
        await self.writer.drain()

    async def send_pkt(self, pkt: Packet):
        payload = self.prepare_message(pkt)
        await self.send_raw(payload)

    def prepare_message(self, pkt: Packet):
        bin_data = pkt.serialize()
        pkt_id = rev_msg_types.get(type(pkt))
        raw_data = flat(
            p16(
                2                # pkt length
                + 2              # msg type
                + len(bin_data)  # pkt content
            ),
            p16(pkt_id),
            bin_data
        )
        return raw_data


class Server(Socket):
    def __init__(self, host, port):
        super().__init__(host, port)
        self.is_connected = False
        self.writer = None
        self.reader = None
        self.server = asyncio.start_server(
                    self.client_connected,
                    self.host,
                    self.port,
                    reuse_address=True,
                    start_serving=False
                )
        self.server_task = None

    def close(self):
        self.server.close()
        self.server_task.cancel()
        self.is_connected = False
        self.writer = None
        self.reader = None

    def client_connected(self, reader: StreamReader, writer: StreamWriter):
        if self.is_connected:
            writer.close()
            self.is_connected = False
            return

        self.is_connected = True
        self.writer = writer
        self.reader = reader

    async def __aenter__(self):
        # start server in the background
        self.server_task = asyncio.create_task(self.server.start_serving())
        return self

    async def __aexit__(self):
        self.close()

