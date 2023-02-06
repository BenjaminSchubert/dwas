import time
from datetime import timedelta


def get_timedelta_since(start: float) -> timedelta:
    return timedelta(seconds=time.monotonic() - start)


def format_timedelta(delta: timedelta) -> str:
    rnd = 1 if delta.microseconds > 500000 else 0
    return str(timedelta(delta.days, delta.seconds + rnd, microseconds=0))
