import re
import sys
import itertools
import logging
from datetime import datetime
from optparse import OptionParser

import requests
from BeautifulSoup import BeautifulSoup


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

    def __init__(self, stat_url=None, home_team=None,
                 away_team=None, logger=None, log_level=logging.INFO):
        self.stat_url = stat_url
        self.stat_html = None
        self.home_team = home_team if home_team else Team()
        self.away_team = away_team if away_team else Team()
        self.logger = logger
        if not self.logger:
            logging.basicConfig(
                filename='scraper.log',
                level=log_level
            )
            self.logger = logging
        if self.stat_url:
            self._load_stat_html()
            self._generate_stats()

    def _load_stat_html(self):
        try:
            resp = requests.get(self.stat_url)
            if resp.url.endswith('recap'):
                self.stat_url = resp.url.replace('recap', 'stats')
                resp = requests.get(self.stat_url)
        except requests.RequestException:
            self.logger.exception("Unable to load URL")
            raise

        if not resp.status_code == 200:
            self.logger.error('Improper status code: %s', resp.status_code)
            raise requests.RequestException(
                'MLS returned a %s status code' % resp.status_code)

        self.stat_html = BeautifulSoup(resp.content)

    def _process_header(self):
        ''' Process the home/away-team-title divs '''
        self.home_team.name = self.stat_html.find(
            'div', {'class': 'home-team-title'}).text
        self.away_team.name = self.stat_html.find(
            'div', {'class': 'away-team-title'}).text
        time_str = '%s %s' % (
            self.stat_html.find('div', {'class': 'game-data-date'}).text,
            self.stat_html.find(
                'div', {'class': 'game-data-timezone'}).text.split()[0]
        )
        self.game_date = datetime.strptime(time_str, '%B %d, %Y %I:%M%p')

    def _process_team_stats(self):
        ''' Process the Team Stats table with the "stats-game" id '''
        stats_table = self.stat_html.find(id='stats-game')
        stats_row = stats_table.findNext('tr').findNext('tr')
        home_stats = {}
        away_stats = {}
        while stats_row:
            stat_title = stats_row.findChildren()[1].text
            home_stats[stat_title] = stats_row.findChildren()[0].text
            away_stats[stat_title] = stats_row.findChildren()[-1].text
            stats_row = stats_row.findNext('tr')

        self.home_team.stats = home_stats
        self.away_team.stats = away_stats

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
                # dirty hack to get card colors
                try:
                    class_name = child.findChild().attrMap.get('class')
                    if class_name in (
                            'timeline-red', 'timeline-yellow',
                            'timeline-second-yellow'):
                        player['card_color'] = class_name.split('-')[-1]
                except AttributeError:
                    pass

                if not child.text:
                    # Skip empty rows, increment offset to account for empties
                    offset += 1
                    continue

                try:
                    player[stat_key[count - offset]] = child.text
                except IndexError:
                    # See these occasionally, still tracking the cause
                    self.logger.info('IndexError in _parse_stat_table')
                    self.logger.info('Index count: %s', count)
                    self.logger.info('Key: %s' % stat_key)

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
            self.logger.error('Unable to parse starters')

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
            self.logger.error('Unable to parse keepers')

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
            self.logger.error('Unable to parse subs')

        home_subs = self._parse_stat_table(home_table)
        away_subs = self._parse_stat_table(away_table)

        self.home_team.players.extend(home_subs)
        self.away_team.players.extend(away_subs)

        self._process_subs_list()

    def _process_subs_list(self):
        ''' Generates a list of substitution "events" from the HTML
            in the game and attaches it to each team in the game.

            Substitution event:
            { "player_off": <player name>,
              "player_on":  <player name>,
              "minute": <int>}'''

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
            self.logger.error('Unable to parse subs')

        self.home_team.subs = self._process_subs_list_table(home_table)
        self.away_team.subs = self._process_subs_list_table(away_table)

    def _process_subs_list_table(self, table):
        children = table.findChildren("tr")
        subs = []
        for idx in xrange(1, len(children), 2):
            off_row = children[idx]
            on_row = children[idx + 1]

            off_player = off_row.findChildren()[3].text
            on_player = on_row.findChildren()[3].text

            # If a player played 30 minutes, sub is at 31st minute for example
            sub_minute = int(off_row.findChildren()[4].text) + 1

            sub_info = {
                "player_off": off_player,
                "player_on": on_player,
                "minute": sub_minute}
            subs.append(sub_info)

        return subs

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
        self.logger.info('Starting to process %s', self.stat_url)
        self._process_header()
        self.logger.info('Processed headers')
        self._process_team_stats()
        self.logger.info('Processed team stats')
        self._process_starters()
        self.logger.info('Processed starters')
        self._process_keepers()
        self.logger.info('Processed keepers')
        self._process_subs()
        self.logger.info('Processed subs')
        self._process_goals()
        self.logger.info('Processed goals')
        self._process_disciplinary_actions()
        self.logger.info('Processed bookings')

    def __unicode__(self):
        return u'%s - %s' % (self.home_team, self.away_team)

    def __str__(self):
        return self.__unicode__()


def main(urls):
    for url in urls:
        match = GameStatSet(url)
        print match.home_team.players
        print match.home_team.subs
        print match.away_team.players
        print match.away_team.subs
        print match.goals
        print match.disciplinary_events
        print match


if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    sys.exit(main(args))
