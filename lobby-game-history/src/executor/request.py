from dataclasses import dataclass
from typing import Optional, Annotated

from packets.pkt import Packet
from packets import msg_types
from serializer import serializer
from serializer.types import U16


@dataclass
class Request(Packet):
    resp_type: U16
    send_type: U16
    send_payload_len: U16
    send_payload: Annotated[bytes, 'send_payload_len']

    response: Optional[Packet] = None

    def has_response(self):
        return self.response is not None

    def to_packet(self) -> Packet:
        return serializer.parse(msg_types.get(self.send_type.v), self.send_payload)


@dataclass
class Requests(Packet):
    entries: U16
    requests: Annotated[list[Request], 'entries']


