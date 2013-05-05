

class BaseEvent(object):

    time = 0
    team = None


class Goal(BaseEvent):

    player = None
    assisted_by = []


class Booking(BaseEvent):

    pass


class Substitution(BaseEvent):

    pass
