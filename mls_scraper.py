import re
import sys
import itertools
from optparse import OptionParser

import requests
from BeautifulSoup import BeautifulSoup


class Team(object):

    name = None
    players = []
    keepers = []
    stats = {}

    def __init__(self, name=None, players=[], keepers=[], stats={}):
        self.name = name
        self.players = players
        self.keepers = keepers
        self.stats = stats

    def __unicode__(self):
        return u'%s' % self.name

    def __str__(self):
        return self.__unicode__()


class GameStatSet(object):

    home_team = None
    away_team = None
    stat_url = None
    goals = []
    disciplinary_events = []
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
        'NY': 'New York Red Bulls',
        'NE': 'New England Revolution',
        'PHI': 'Philadelphia Union',
        'POR': 'Portland Timbers',
        'RSL': 'Real Salt Lake',
        'SEA': 'Seattle Sounders',
        'SJ': 'San Jose Earthquakes',
        'SKC': 'Sporting Kansas City',
        'TOR': 'Toronto FC',
        'VAN': 'Vancouver Whitecaps FC',
    }

    def __init__(self, stat_url, home_team=None, away_team=None):
        self.stat_url = stat_url
        self.stat_html = None
        self.home_team = home_team if home_team else Team()
        self.away_team = away_team if away_team else Team()
        self._load_stat_html()
        self._generate_stats()

    def _load_stat_html(self):
        try:
            resp = requests.get(self.stat_url)
        except requests.RequestException:
            print "Unable to load URL"
            raise

        if not resp.status_code == 200:
            print "Improper status code: %s" % resp.status_code

        self.stat_html = BeautifulSoup(resp.content)

    def _process_header(self):
        ''' Process the home/away-team-title divs '''
        self.home_team.name = self.stat_html.find(
            'div', {'class': 'home-team-title'}).text
        self.away_team.name = self.stat_html.find(
            'div', {'class': 'away-team-title'}).text

    def _process_team_stats(self):
        ''' Process the Team Stats table with the "stats-game" id '''
        stats_table = self.stat_html.find(id='stats-game')
        stats_row = stats_table.findNext('tr').findNext('tr')
        while stats_row:
            stat_title = stats_row.findChildren()[1].text
            self.home_team.stats[stat_title] = stats_row.findChildren()[0].text
            self.away_team.stats[stat_title] = stats_row.findChildren()[-1].text
            stats_row = stats_row.findNext('tr')

    def _parse_stat_table(self, table):
        ''' Takes a stats table, and processes its children '''
        children = table.findChildren('tr')
        stat_header = children[0]
        stat_key = [x.text for x in stat_header.findChildren() if x.text]
        stats = []
        player_rows = children[1:]
        for player_row in player_rows:
            if player_row.findChildren('div', {'class': 'pos-arrow'}):
                # We already got them in the starter table
                continue

            player = {}
            offset = 0
            for count, child in enumerate(player_row.findChildren()):
                if not child.text:
                    # Skip empty rows, increment offset to account for empties
                    offset += 1
                    continue
                try:
                    player[stat_key[count - offset]] = child.text
                except IndexError:
                    print count
                    print len(stat_key)

            stats.append(player)
            player_row = player_row.findNext('tr')

        return stats

    def _process_starters(self):
        ''' Snags the two (two tables with the same ID, for shame MLS, for
        shame) tables with the id of "stats-starters"
        '''
        home_table = None
        away_table = None
        for table in self.stat_html.findAll(id='stats-starters'):
            if any(re.search(
                    'home', x) for x in itertools.chain(*table.attrs)):
                home_table = table
            elif any(re.search(
                    'away', x) for x in itertools.chain(*table.attrs)):
                away_table = table

        if not away_table and not home_table:
            print 'Unable to parse starters'

        self.home_team.players = self._parse_stat_table(home_table)
        self.away_team.players = self._parse_stat_table(away_table)

    def _process_keepers(self):
        ''' Snags the two (two tables with the same ID, for shame MLS, for
        shame) tables with the id of "stats-goalkeeper"
        '''
        home_table = None
        away_table = None
        for table in self.stat_html.findAll(id='stats-goalkeeper'):
            if any(re.search(
                    'home', x) for x in itertools.chain(*table.attrs)):
                home_table = table
            elif any(re.search(
                    'away', x) for x in itertools.chain(*table.attrs)):
                away_table = table

        if not away_table and not home_table:
            print 'Unable to parse starters'

        home_keepers = self._parse_stat_table(home_table)
        away_keepers = self._parse_stat_table(away_table)
        self.home_team.keepers = home_keepers
        self.away_team.keepers = away_keepers

    def _process_subs(self):
        ''' Snags the two (two tables with the same ID, for shame MLS, for
        shame) tables with the id of "stats-subs"
        '''
        home_table = None
        away_table = None
        for table in self.stat_html.findAll(id='stats-subs'):
            if any(re.search(
                    'home', x) for x in itertools.chain(*table.attrs)):
                home_table = table
            elif any(re.search(
                    'away', x) for x in itertools.chain(*table.attrs)):
                away_table = table

        if not away_table and not home_table:
            print 'Unable to parse starters'

        home_subs = self._parse_stat_table(home_table)
        away_subs = self._parse_stat_table(away_table)
        self.home_team.players.extend(home_subs)
        self.away_team.keepers.extend(away_subs)

    def _process_goals(self):
        ''' Process the Goals div which has an id of "goals" '''
        goals_div = self.stat_html.find('div', {'id': 'goals'})
        goals = self._parse_stat_table(goals_div)
        self.goals = goals

    def _process_disciplinary_actions(self):
        disciplinary_div = self.stat_html.find('div', {'id': 'disciplinary'})
        events = self._parse_stat_table(disciplinary_div)
        self.disciplinary_events = events

    def _generate_stats(self):
        print "processing header"
        self._process_header()
        print "processing team stats"
        self._process_team_stats()
        print "processing starters"
        self._process_starters()
        print "processing keepers"
        self._process_keepers()
        print "processing subs"
        self._process_subs()
        print "process goals"
        self._process_goals()
        print "processing disciplinary actions"
        self._process_disciplinary_actions()
        print "finished processing %s" % self.stat_url

    def __unicode__(self):
        return u'%s - %s' % (self.home_team, self.away_team)

    def __str__(self):
        return self.__unicode__()


def main(urls):
    for url in urls:
        match = GameStatSet(url)
        print match.home_team.players
        print match.away_team.players
        print match.goals
        print match.disciplinary_events
        print match


if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    sys.exit(main(args))
