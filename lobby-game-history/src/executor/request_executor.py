from typing import Iterable

from executor.errors import Errors
from executor.lobby_api_client import LobbyAPIClient
from executor.request import Request
from executor.response import RequestResponse, RequestResponses
from serializer.types import U16


class RequestExecutor:
    """
    Executes requests in context of given account
    """

    def __init__(self, api_client: LobbyAPIClient):
        self.proxy = api_client

    async def execute_many(self, requests: Iterable[Request]) -> RequestResponses:
        responses = []
        async with self.proxy.api_sock, self.proxy as proxy:
            mark_as_not_executed = False
            for request in requests:
                if mark_as_not_executed:
                    responses.append(RequestResponse.make_error(Errors.PREVIOUS_REQUEST_FAILED))
                    continue

                try:
                    response_pkt = await proxy.execute_request(request)
                    responses.append(RequestResponse.from_pkt(response_pkt))
                except TimeoutError:
                    responses.append(RequestResponse.make_error(Errors.TIMEOUT_EXCEEDED))

        return RequestResponses(U16(len(responses)), responses)

    async def execute(self, request: Request) -> RequestResponse:
        responses = await self.execute_many([request])
        return responses.responses[0]
