__author__ = 'nosoyyo'
__version__ = '2c37e'

from time import time
from functools import reduce
from datetime import datetime


def fromTimeStamp(timestamp: float = None, d=True, t=True) -> str:

    timestamp = timestamp or time()

    if not isinstance(timestamp, float):
        timestamp = float(timestamp)
    since = datetime.fromtimestamp(timestamp)
    _date = f'{since.year}.{since.month:02}.{since.day:02}'
    _time = f'{since.hour:02}:{since.minute:02}:{since.second:02}'

    if d and t:
        return _date, _time
    elif not t:
        return _date
    elif not d:
        return _time


def timeQuantization(q):
    q = float(q)
    if q < 60:
        return 0, 0, 0, int(q)
    elif 60 <= q < 3600:
        mins = int(q/60)
        a, b, c, sec = timeQuantization(q - mins * 60)
        return 0, 0, mins, int(sec)
    elif 3600 <= q < 3600 * 24:
        hours = int(q / 3600)
        a, b, mins, sec = timeQuantization(q - hours * 3600)
        return 0, hours, mins, sec
    elif q >= 3600 * 24:
        days = int(q / (3600 * 24))
        a, hours, mins, sec = timeQuantization(q - days * 3600 * 24)
        return days, hours, mins, sec


def fancyTQ(seconds):
    d, h, m, s = timeQuantization(seconds)
    result = []
    if d:
        result.append(f'{d} days')
    if h:
        result.append(f'{h} hours')
    if m:
        result.append(f'{m} mins')
    if s:
        result.append(f'{s} seconds')

    return reduce(lambda x, y: f'{x} {y}', result) + '.'
