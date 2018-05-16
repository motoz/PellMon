from Pellmonsrv.database import Getsetitem
from Scotteprotocol.transformations import minutes_to_time


def get_item(db):
    i = Getsetitem('timer_status', '-', getter = lambda item: get_item_value(db, item))
    i.longname = 'timer status'
    i.type = 'R'
    i.description = 'Inferred timer status'
    i.tags = ['Basic', 'Overview', 'Timer']
    return i

def get_item_value(db, item):
    current_time = from_time(db.get_value("time_minutes"))
    period = from_time(db.get_value("timer_heating_period"))
    starts = [from_time(db.get_value("timer_heating_start_%d" % i)) for i in range(1, 5)]
    return get_status_text(starts, period, current_time)

def from_time(s):
    return int(minutes_to_time().encode(s))

def to_time(minutes):
    return minutes_to_time().decode(minutes)

def get_status_text(starts, period, current_time):
    starts = sorted(filter(lambda x: x != 0, starts))
    if len(starts) == 0 or period == 0:
        return "Timer disabled"

    next_start = None
    for start in starts:
        if current_time > start and current_time < start + period:
            return "Stopping at %s" % to_time(start + period)
        if start > current_time:
            next_start = start
            break
    if next_start is None:
        next_start = starts[0]
    return "Starting at %s" % to_time(next_start)

