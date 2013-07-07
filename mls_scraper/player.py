

class BasePlayer(object):

    first_name = None
    last_name = None
    number = None
    position = None
    shots = 0
    minutes = 0
    assists = 0
    fouls_commited = 0
    fouls_suffered = 0

    def __unicode__(self):
        return u'%s %s' % (self.first_name, self.last_name)

    def __str__(self):
        return self.__unicode__()

    def __init__(self, stats_dict=None):
        if stats_dict:
            self.first_name, self.last_name = self.parse_name(
                stats_dict['Player'])
            self.number = stats_dict['#']
            self.minutes = stats_dict['MIN']
            self.fouls_commited = stats_dict['FC']
            self.fouls_suffered = stats_dict['FS']

            # Subs tend to be missing these numbers
            # Does a subs subclass make sense? Seems unlikely
            self.position = stats_dict.get('POS', 'S')
            self.shots = stats_dict.get('SHT', 0)
            self.assists = stats_dict.get('A', 0)

    @classmethod
    def parse_name(cls, name):
        ''' Takes a player name and generates first/last names '''
        player_name = name.split()
        if len(player_name) == 1:
            first_name = last_name = player_name[0]
        else:
            first_name = player_name[0]
            last_name = player_name[1]

        return first_name, last_name

    @property
    def name(self):
        return u'%s %s' % (self.first_name, self.last_name)


class Player(BasePlayer):

    goals = 0
    shots_on_goal = 0
    corners = 0
    offsides = 0

    def __init__(self, stats_dict=None):
        super(Player, self).__init__(stats_dict)
        if stats_dict:
            self.goals = stats_dict['G']
            self.shots_on_goal = stats_dict['SOG']
            self.corners = stats_dict['CK']
            self.offsides = stats_dict['OFF']


class Keeper(BasePlayer):

    saves = 0
    goals_against = 0

    def __init__(self, stats_dict=None):
        super(Keeper, self).__init__(stats_dict)
        if stats_dict:
            self.saves = stats_dict['SV']
            self.goals_against = stats_dict['GA']
