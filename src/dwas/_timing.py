import time
from datetime import timedelta


def get_timedelta_since(start: float) -> timedelta:
    return timedelta(seconds=time.monotonic() - start)
