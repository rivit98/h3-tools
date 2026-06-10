from proxy.h3_socket import Socket


import asyncio
from asyncio import StreamReader, StreamWriter

from common import logger
from config import config
from executor.lobby_api_client import LobbyAPIClient
from executor.request import Requests
from executor.request_executor import RequestExecutor
from serializer import serializer

from executor.accountpool import AccountPool

account_pool = AccountPool(config)


def client_connected(reader: StreamReader, writer: StreamWriter):
    client_id = writer.get_extra_info('peername')
    logger.info(f'Client connected {client_id}')
    task = asyncio.ensure_future(client_task(client_id, reader, writer))

    # def cleanup(future):
    #     logger.info(f"Cleanup {client_id}")
    #     # TODO: check if needed
    #     writer.close()
    #
    # task.add_done_callback(cleanup)

async def client_task(client_id, reader: StreamReader, writer: StreamWriter):
    # TODO: return request invalid in case of failure
    try:
        request = await reader.read(0x1000)
        logger.debug(f'Received request from {client_id}: {request}')
        if not request:
            raise Exception(f"No data read from {client_id}")
    except Exception:
        logger.exception(f'Unable to read request from {client_id}')
        return

    available_account = await account_pool.get_available()
    logger.debug(f'Available account for client {client_id}: {available_account}')

    try:
        incoming = serializer.parse(Requests, request)
        api_socket = Socket(config.lobby.host, config.lobby.port)
        lobby_client = LobbyAPIClient(api_socket, config, available_account)
        executor = RequestExecutor(lobby_client)
        responses = await executor.execute_many(incoming.requests)

        logger.debug(f'Sending response to {client_id}: {responses}')
        writer.write(responses.serialize())
        await writer.drain()
    except Exception:
        logger.exception(f"Unable to send response to {client_id}")
    finally:
        writer.close()
        await account_pool.return_back(available_account)

async def executor_main(port):
    logger.info("Executor start")

    server = await asyncio.start_server(
        client_connected,
        host='localhost',
        port=port,
    )

    async with server:
        await server.serve_forever()

    logger.info("Executor exit")
