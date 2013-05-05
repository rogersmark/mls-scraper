

class Formation(object):

    players = None

    def __init__(self, players=None):
        self.players = players if players else []

    @property
    def formation(self):
        return '-'.join([str(len(x)) for x in self.players][1:])
