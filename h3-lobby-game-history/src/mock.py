from executor.request import Request, Requests
from packets import SndGetPlayersInfo, rev_msg_types, RcvGetPlayersInfoResponse
from serializer.types import U32, U16
import asyncio

request = SndGetPlayersInfo(U32(4), [U32(i) for i in range(1, 5)])
ser = request.serialize()
request2 = Request(
    resp_type=U16(rev_msg_types.get(RcvGetPlayersInfoResponse)),
    send_type=U16(rev_msg_types.get(type(request))),
    send_payload=ser,
    send_payload_len=U16(len(ser))
)
a = U16(4)
a += 2
print(a)

async def main():
    reader, writer = await asyncio.open_connection("localhost", 6846)
    writer.write(Requests(
        entries=U16(1),
        requests=[request2]
    ).serialize())
    await writer.drain()

    resp = await reader.read(0x1000)
    print(resp)

    writer.close()
    await writer.wait_closed()


if __name__ == '__main__':
    asyncio.run(main())