from team import Team


class GameStatSet(object):

    home_team = None
    away_team = None
    stat_url = None
    goals = []
    disciplinary_events = []
    game_date = None
    subs = []

    def __init__(self, stat_url=None, home_team=None, away_team=None):
        self.stat_url = stat_url
        self.stat_html = None
        self.home_team = home_team if home_team else Team()
        self.away_team = away_team if away_team else Team()
