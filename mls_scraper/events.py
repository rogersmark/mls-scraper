

class BaseEvent(object):

    time = 0
    team = None


class Goal(BaseEvent):

    player = None
    assisted_by = []


class Booking(BaseEvent):

    player = None
    card_color = None
    reason = None


class Substitution(BaseEvent):

    player_on = None
    player_off = None
