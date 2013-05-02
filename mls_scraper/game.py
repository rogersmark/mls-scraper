from team import Team


class GameStatSet(object):

    home_team = None
    away_team = None
    stat_url = None
    goals = []
    disciplinary_events = []
    game_date = None
    abbreviation_map = {
        'CHI': 'Chicago Fire',
        'CHV': 'Chivas USA',
        'CLB': 'Columbus Crew',
        'COL': 'Colorado Rapids',
        'DAL': 'FC Dallas',
        'DC': 'D.C. United',
        'HOU': 'Houston Dynamo',
        'LA': 'LA Galaxy',
        'MON': 'Montreal Impact',
        'MTL': 'Montreal Impact', # Sometimes its MON, others its MTL
        'NY': 'New York Red Bulls',
        'NE': 'New England Revolution',
        'PHI': 'Philadelphia Union',
        'POR': 'Portland Timbers',
        'RSL': 'Real Salt Lake',
        'SEA': 'Seattle Sounders FC',
        'SJ': 'San Jose Earthquakes',
        'SKC': 'Sporting Kansas City',
        'KC': 'Sporting Kansas City', # Sometimes its KC, others its SKC
        'TOR': 'Toronto FC',
        'VAN': 'Vancouver Whitecaps FC',
    }

    def __init__(self, stat_url=None, home_team=None, away_team=None):
        self.stat_url = stat_url
        self.stat_html = None
        self.home_team = home_team if home_team else Team()
        self.away_team = away_team if away_team else Team()
