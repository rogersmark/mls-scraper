

class BasePlayer(object):

    first_name = None
    last_name = None
    number = None
    position = None
    shots = 0
    minutes = 0
    assists = 0
    fouls_commited = 0
    fs = 0 # Seriously MLS, y u no tell me what this is?

    def __unicode__(self):
        return u'%s %s' % (self.first_name, self.last_name)

    def __str__(self):
        return self.__unicode__()

    def __init__(self, stats_dict):
        self._parse_name(stats_dict['Player'])
        self.number = stats_dict['#']
        self.minutes = stats_dict['MIN']
        self.fouls_commited = stats_dict['FC']
        self.fs = stats_dict['FS']

        # Subs tend to be missing these numbers
        # Does a subs subclass make sense? Seems unlikely
        self.position = stats_dict.get('POS', 'S')
        self.shots = stats_dict.get('SHT', 0)
        self.assists = stats_dict.get('A', 0)

    def _parse_name(self, name):
        ''' Takes a player name and generates first/last names '''
        player_name = name.split()
        if len(player_name) == 1:
            self.first_name = self.last_name = player_name[0]
        else:
            self.first_name = player_name[0]
            self.last_name = player_name[1]

    @property
    def name(self):
        return u'%s %s' % (self.first_name, self.last_name)


class Player(BasePlayer):

    goals = 0
    shots_on_goal = 0
    corners = 0
    offsides = 0

    def __init__(self, stats_dict):
        super(Player, self).__init__(stats_dict)
        self.goals = stats_dict['G']
        self.shots_on_goal = stats_dict['SOG']
        self.corners = stats_dict['CK']
        self.offsides = stats_dict['OF']


class Keeper(BasePlayer):

    saves = 0
    goals_against = 0

    def __init__(self, stats_dict):
        super(Keeper, self).__init__(stats_dict)
        self.saves = stats_dict['SV']
        self.goals_against = stats_dict['GA']
