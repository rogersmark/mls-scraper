import re
import logging
import itertools
from datetime import datetime
from abc import ABCMeta, abstractmethod

import requests
from BeautifulSoup import BeautifulSoup

import player
import events
from game import GameStatSet
from formation import Formation
from mls_scraper.common import ABBREVIATION_MAP


class StatsParser(object):
    __metaclass__ = ABCMeta

    stat_url = None
    logger = None
    stat_html = None

    def _generate_stats(self):
        ''' Executes the various methods to grab all of the stats, should
        stay pretty consistent from parser to parser
        '''
        self._load_stat_html()
        self.get_general_info()
        self.get_team_stats()
        self.get_players()
        self.get_events()
        self.get_formations()

    @abstractmethod
    def _load_stat_html(self):
        ''' Abstract method for loading and generating the stat_html
        for the parser
        '''

    @abstractmethod
    def _get_home_team_name(self):
        ''' Abstact method to Retrieve home team name '''

    @abstractmethod
    def _get_away_team_name(self):
        ''' Abstract method Retrieve away team name '''

    @abstractmethod
    def _get_game_start_time(self):
        ''' Abstract method to retrieve and store game start time as a
        datetime object
        '''

    def get_general_info(self):
        ''' Retrieves team names and start time '''
        self._get_home_team_name()
        self._get_away_team_name()
        self._get_game_start_time()

    @abstractmethod
    def get_team_stats(self):
        ''' Abstract method responsible for generating the statistics of the
        match. Stats we're looking for here are possession, shots, etc.

        TODO: Create a true Stats class to store this info on instead of the
        somewhat loose dict approach
        '''

    @abstractmethod
    def _get_starters(self):
        ''' Abstract method responsible for grabbing the starters for a
        match.
        '''

    @abstractmethod
    def _get_keepers(self):
        ''' See get_starters -- Likely to be very similar '''

    @abstractmethod
    def _get_substitutions(self):
        ''' See get_starters -- Likely to be very similar '''

    def get_players(self):
        self._get_starters()
        self._get_keepers()
        self._get_substitutions()

    @abstractmethod
    def _get_goals(self):
        ''' Abstract method for retrieving goal events. '''

    @abstractmethod
    def _get_bookings(self):
        ''' Abstract method for retrieving bookings. '''

    @abstractmethod
    def _get_substitution_events(self):
        ''' Abstract method for retrieving substituation events '''

    def get_events(self):
        self._get_substitution_events()
        self._get_goals()
        self._get_bookings()

    @abstractmethod
    def get_formations(self):
        ''' Abstract method for retrieving formation information '''


class MLSStatsParser(StatsParser):

    def __init__(self, stat_url, generate_stats=True, logger=None,
                 log_level=logging.DEBUG):
        self.stat_url = stat_url
        self.logger = logger
        self.stat_html = None
        self.logger = logger
        if not self.logger:
            logging.basicConfig(
                filename='scraper.log',
                level=log_level
            )
            self.logger = logging
        self.game = GameStatSet(self.stat_url)
        if generate_stats:
            self._generate_stats()

    def _parse_stat_table(self, table, outer_skip_func=None,
                          inner_parse_func=None):
        ''' Takes a stats table, and processes its children.

        Provides the option for an outer and inner parse function to be passed
        in. The various tables at MLS are incredibly similar, and by passing
        in these methods, we can get the flexibility we need without
        duplicating a bunch of code.

        Currently the outer_skip_func needs to return a boolean-ish var. If
        it's True, we'll skip the row. If it's false, we'll continue to process

        The inner_parse_func is only used for tracking booking events right
        now. The idea there is to let it modify the dictionary we're creating,
        and optionally skip the row as well. Thus it expects a tuple to be
        returned, first being a dict, the second a bool.

        In the end, this feels less hacky than the previous approach, but am
        open to suggestions
        '''
        children = table.findChildren('tr')
        stat_header = children[0]
        stat_key = [x.text for x in stat_header.findChildren() if x.text]
        stats = []
        player_rows = children[1:]
        for player_row in player_rows:
            if outer_skip_func and outer_skip_func(player_row):
                continue

            player_dict = {}
            offset = 0
            for count, child in enumerate(player_row.findChildren()):
                if inner_parse_func:
                    result_dict, skip = inner_parse_func(count, child)
                    player_dict.update(result_dict)

                    if skip:
                        continue

                if not child.text:
                    # Skip empty rows, increment offset to account for empties
                    offset += 1
                    continue

                try:
                    player_dict[stat_key[count - offset]] = child.text
                except IndexError:
                    # See these occasionally, still tracking the cause
                    self.logger.info('IndexError in _parse_stat_table')
                    self.logger.info('Index count: %s', count)
                    self.logger.info('Key: %s' % stat_key)

            stats.append(player_dict)
            player_row = player_row.findNext('tr')

        return stats

    def _load_stat_html(self):
        ''' Tries to load the stat_url. If the URL ends with "recap" it means
        MLS redirected us there for a variety of reasons. In those instances,
        we force our way back to the stats page.
        '''
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

    def _get_home_team_name(self):
        ''' Retrieves home team name and stores it '''
        self.game.home_team.name = self.stat_html.find(
            'div', {'class': 'home-team-title'}).text

    def _get_away_team_name(self):
        ''' Retrieves away team name and stores it '''
        self.game.away_team.name = self.stat_html.find(
            'div', {'class': 'away-team-title'}).text

    def _get_game_start_time(self):
        ''' Retrieves and stores game start time '''
        time_str = '%s %s' % (
            self.stat_html.find('div', {'class': 'game-data-date'}).text,
            self.stat_html.find(
                'div', {'class': 'game-data-timezone'}).text.split()[0]
        )
        self.game.game_date = datetime.strptime(time_str, '%B %d, %Y %I:%M%p')

    def get_team_stats(self):
        ''' Retrieves and stores all the main game stats, such as possession,
        shots on goal, and so on.
        '''
        stats_table = self.stat_html.find(id='stats-game')
        stats_row = stats_table.findNext('tr').findNext('tr')
        home_stats = {}
        away_stats = {}
        while stats_row:
            stat_title = stats_row.findChildren()[1].text
            home_stats[stat_title] = stats_row.findChildren()[0].text
            away_stats[stat_title] = stats_row.findChildren()[-1].text
            stats_row = stats_row.findNext('tr')

        self.game.home_team.stats = home_stats
        self.game.away_team.stats = away_stats

    def _get_starters(self):
        ''' Finds the home/away tables for starters and parses them out '''
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

        self.game.home_team.starters = [
            player.Player(x) for x in self._parse_stat_table(home_table)]
        self.game.away_team.starters = [
            player.Player(x) for x in self._parse_stat_table(away_table)]

    def _get_keepers(self):
        ''' Finds the home/away table for keepers and parses them out '''
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

        home_keepers = [
            player.Keeper(x) for x in self._parse_stat_table(home_table)]
        away_keepers = [
            player.Keeper(x) for x in self._parse_stat_table(away_table)]
        self.game.home_team.keepers = home_keepers
        self.game.away_team.keepers = away_keepers

    def _get_substitutions(self):
        ''' Finds the home/away table for subs and parses them out. Also
        provides a "skip_starters" method to _parse_stat_table for skipping
        starters.
        '''
        def skip_starters(player_row):
            return player_row.findChildren('div', {'class': 'pos-arrow'})

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

        home_subs = [
            player.Player(x) for x in self._parse_stat_table(
                home_table, skip_starters)
        ]
        away_subs = [
            player.Player(x) for x in self._parse_stat_table(
                away_table, skip_starters)
        ]

        self.game.home_team.subs = home_subs
        self.game.away_team.subs = away_subs

    def _process_subs_list_table(self, table):
        children = table.findChildren("tr")
        subs = []
        for idx in xrange(1, len(children), 2):
            sub = events.Substitution()
            if 'home' in table.attrMap['class']:
                sub.team = self.game.home_team
            else:
                sub.team = self.game.away_team

            off_row = children[idx]
            on_row = children[idx + 1]
            off_player = '%s %s' % player.BasePlayer.parse_name(
                off_row.findChildren()[3].text)
            on_player = '%s %s' % player.BasePlayer.parse_name(
                on_row.findChildren()[3].text)
            # If a player played 30 minutes, sub is at 31st minute for example
            sub_minute = int(off_row.findChildren()[4].text) + 1
            sub.time = sub_minute
            for player_obj in sub.team.players:
                if player_obj.name == off_player:
                    sub.player_off = player_obj
                elif player_obj.name == on_player:
                    sub.player_on = player_obj

            subs.append(sub)

        return subs

    def _get_substitution_events(self):
        ''' Generates a list of substitution "events" from the HTML
            in the game and attaches it to each team in the game.

            Substitution event:
            { "player_off": <player name>,
              "player_on":  <player name>,
              "minute": <int>}
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

        home_subs = self._process_subs_list_table(home_table)
        away_subs = self._process_subs_list_table(away_table)
        self.game.subs = home_subs + away_subs

    def _parse_goal_dict(self, goal_dict):
        ''' Parses a goal dictionary and returns a Goal object '''
        goal = events.Goal()
        team_name = ABBREVIATION_MAP[goal_dict['Club']]
        goal.time = int(goal_dict['Time'].rstrip("'"))
        if team_name == self.game.home_team.name:
            goal.team = self.game.home_team
        else:
            goal.team = self.game.away_team

        player_name = '%s %s' % player.BasePlayer.parse_name(
            goal_dict['Player'])
        if re.search('(OG)', goal_dict['Player']):
            goal.own_goal = True
        for player_obj in goal.team.players:
            if player_obj.name == player_name:
                goal.player = player_obj
                break

        assists = []
        for player_info in goal_dict.get('(Assisted by)', '').split(','):
            if not player_info:
                continue
            player_name = '%s %s' % player.BasePlayer.parse_name(
                player_info.lstrip('(').rstrip(')'))
            for player_obj in goal.team.players:
                if player_obj.name == player_name:
                    assists.append(player_obj)

        goal.assisted_by = assists
        return goal

    def _get_goals(self):
        ''' Grabs the goals from the stats and stores them '''
        goals_div = self.stat_html.find('div', {'id': 'goals'})
        goals_dict = self._parse_stat_table(goals_div)
        goals = []
        for goal in goals_dict:
            goals.append(self._parse_goal_dict(goal))

        self.game.goals = goals

    def _parse_booking_dict(self, booking_dict):
        ''' Parses a booking dictionary and returns a Booking object '''
        booking = events.Booking()
        team_name = ABBREVIATION_MAP[booking_dict['Club']]
        booking.time = int(booking_dict['Time'].rstrip("'"))
        if team_name == self.game.home_team.name:
            booking.team = self.game.home_team
        else:
            booking.team = self.game.away_team

        player_name = '%s %s' % player.BasePlayer.parse_name(
            booking_dict['Player'])
        for player_obj in booking.team.players:
            if player_obj.name == player_name:
                booking.player = player_obj
                break

        booking.reason = booking_dict['Reason']
        booking.card_color = booking_dict['card_color']
        return booking

    def _get_bookings(self):
        ''' Grabs the booking events from the stats and stores them. Also
        provides a get_card_color inner parsing function to _parse_stat_table
        so that we can determine the card color
        '''
        def get_card_color(count, child):
            player = {}
            try:
                class_name = child.findChild().attrMap.get('class')
                if class_name in (
                        'timeline-red', 'timeline-yellow',
                        'timeline-second-yellow'):
                    player['card_color'] = class_name.split('-')[-1]
            except AttributeError:
                pass

            return player, False

        disciplinary_div = self.stat_html.find('div', {'id': 'disciplinary'})
        events = self._parse_stat_table(
            disciplinary_div,
            inner_parse_func=get_card_color
        )
        self.game.disciplinary_events = [
            self._parse_booking_dict(x) for x in events
        ]

    def _get_formation_contents(self, l, formatter=lambda s: s):
        """Fetch the contents from a soup object."""

        if not hasattr(l, 'contents'):
            s = l
        else:
            s = ""

            for e in l.contents:
                s += self._get_formation_contents(e)
        return formatter(s.strip())

    def _process_formation(self, soup, home=False):
        strip_leading_digits = lambda s: re.match("\d*(.*)", s).groups()[0].strip()
        extract_player = lambda tag: strip_leading_digits(
            self._get_formation_contents(tag))
        extract_line = lambda l: [extract_player(e) for e in l if extract_player(e)]

        if home:
            team = self.game.home_team
        else:
            team = self.game.away_team

        lines = soup.findAll('div')
        formation = []
        for line in lines[:-1]:
            form_line = extract_line(line)
            player_list = []
            for item in form_line:
                player_name = '%s %s' % player.BasePlayer.parse_name(item)
                for player_obj in team.players:
                    if player_name == player_obj.name:
                        player_list.append(player_obj)

            formation.append(player_list)

        formation.reverse()
        return formation

    def _parse_formation_url(self, url):
        try:
            resp = requests.get(url)
        except requests.RequestException:
            self.logger.exception("Unable to load formation URL: %s", url)
            raise

        if not resp.status_code == 200:
            self.logger.error('Improper status code: %s', resp.status_code)
            raise requests.RequestException(
                'MLS returned a %s status code' % resp.status_code)

        return self._parse_formation_html(resp.content)

    def _parse_formation_html(self, html):
        soup = BeautifulSoup(html)
        formations = soup.find('div', {'class': 'formations'})
        home, away = formations.findAll('div', recursive=False)
        return {
            'home': Formation(self._process_formation(home, True)),
            'away': Formation(self._process_formation(away))
        }

    def get_formations(self):
        ''' Parses out and retreives Formation objects '''
        url = self.stat_url.replace('/stats', '/formation')
        results = self._parse_formation_url(url)
        self.game.home_team.formation = results['home']
        self.game.away_team.formation = results['away']
