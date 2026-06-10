from dataclasses import dataclass
from typing import Annotated

from executor.errors import Errors
from packets.pkt import Packet
from serializer import serializer
from serializer.types import U16


@dataclass
class RequestResponse(Packet):
    status_code: U16
    response_payload_len: U16
    response_payload: Annotated[bytes, 'response_payload_len']

    @staticmethod
    def make_error(status: Errors):
        return RequestResponse(
            status_code=U16(status.value),
            response_payload_len=U16(0),
            response_payload=b'',
        )

    @staticmethod
    def from_pkt(pkt: Packet):
        raw = serializer.serialize(pkt)
        return RequestResponse(
            status_code=U16(Errors.OK.value),
            response_payload_len=U16(len(raw)),
            response_payload=raw
        )

@dataclass
class RequestResponses(Packet):
    entries: U16
    responses: Annotated[list[RequestResponse], 'entries']
