

class Team(object):

    name = None
    players = []
    keepers = []
    stats = {}

    def __init__(self, name=None, players=None, keepers=None, stats=None):
        self.name = name
        self.players = self.players if self.players else []
        self.keepers = self.keepers if self.keepers else []
        self.stats = self.stats if self.stats else {}

    def __unicode__(self):
        return u'%s' % self.name

    def __str__(self):
        return self.__unicode__()
