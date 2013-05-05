

class Team(object):

    name = None
    starters = []
    keepers = []
    subs = []
    stats = {}
    formation = None

    def __init__(self, name=None, starters=None, keepers=None,
                 subs=None, stats=None):
        self.name = name
        self.starters = starters if starters else []
        self.keepers = keepers if keepers else []
        self.stats = stats if stats else {}
        self.subs = subs if subs else []

    def __unicode__(self):
        return u'%s' % self.name

    def __str__(self):
        return self.__unicode__()

    @property
    def players(self):
        return self.starters + self.keepers + self.subs
