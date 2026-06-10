from db import get_session
from common import logger


def batched(iterable, n=1):
    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]

def save_datapoints(data_points):
    logger.info(f"Saving {len(data_points)} datapoints")
    with get_session() as session:
        session.add_all(data_points)
        session.commit()

