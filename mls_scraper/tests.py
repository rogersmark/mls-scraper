#!/usr/local/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os

from mock import Mock
from BeautifulSoup import BeautifulSoup

import parser
import formation


class TestMLSScraper(unittest.TestCase):

    def setUp(self):
        super(TestMLSScraper, self).setUp()
        self.orig_requests = parser.requests
        self.stat_html = open(
            os.path.join(os.path.dirname(__file__), 'test_stats.html')
        ).read()
        parser.requests = Mock()
        self.parser = parser.MLSStatsParser(
            'http://www.example.com/stats/', False)

    def tearDown(self):
        parser.requests = self.orig_requests
        self.parser = None
        super(TestMLSScraper, self).tearDown()

    def _create_requests_mock_return(self, url='http://www.example.com/stats',
                                     status_code=200):
        requests_mock = Mock()
        requests_mock.get.return_value = Mock(
            content=self.stat_html,
            status_code=status_code,
            url=url,
        )
        parser.requests = requests_mock

    def _load_stats(self, players=False):
        self.parser.stat_url = 'http://www.example.com/stats'
        self._create_requests_mock_return()
        self.parser._load_stat_html()
        self.parser.get_general_info()
        if players:
            self.parser.get_players()

    def test_load_stat_html(self):
        ''' Asserts that we successfully parse HTML, and translate recap urls
        into legit stat urls
        '''
        self.parser.stat_url = 'http://www.example.com/recap'
        self._create_requests_mock_return(url='http://www.example.com/recap')
        self.parser._load_stat_html()
        assert isinstance(self.parser.stat_html, BeautifulSoup)
        self.assertEqual(self.parser.stat_url, 'http://www.example.com/stats')

    def test_get_general_info(self):
        ''' Asserts that we get the right team names and game start time '''
        self._load_stats()
        self.parser.get_general_info()
        self.assertEqual(self.parser.game.home_team.name, 'Chicago Fire')
        self.assertEqual(self.parser.game.away_team.name, 'Chivas USA')
        assert self.parser.game.game_date

    def test_get_team_stats(self):
        self._load_stats()
        self.parser.get_team_stats()
        assert self.parser.game.home_team.stats
        assert self.parser.game.away_team.stats

    def test_get_starters(self):
        self._load_stats()
        self.parser._get_starters()
        assert self.parser.game.home_team.players
        assert self.parser.game.away_team.players
        self.assertEqual(len(self.parser.game.home_team.players), 10)
        self.assertEqual(len(self.parser.game.away_team.players), 10)

    def test_get_keepers(self):
        self._load_stats()
        self.parser._get_keepers()
        assert self.parser.game.home_team.keepers
        assert self.parser.game.away_team.keepers
        self.assertEqual(len(self.parser.game.home_team.keepers), 1)
        self.assertEqual(len(self.parser.game.away_team.keepers), 1)

    def test_get_substitutions(self):
        self._load_stats()
        self.parser._get_substitutions()
        assert self.parser.game.home_team.players
        assert self.parser.game.away_team.players

        self.assertEqual(len(self.parser.game.home_team.players), 3)
        self.assertEqual(len(self.parser.game.away_team.players), 3)

    def test_process_subs_puts_correct_players_on_home_team(self):
        self._load_stats()
        self.parser._get_substitutions()
        assert self.parser.game.home_team.players
        assert self.parser.game.away_team.players

        amarikwa_sub = [player for player in self.parser.game.home_team.players
                        if player.name == 'Quincy Amarikwa']
        self.assertTrue(len(amarikwa_sub) > 0)

    def test_process_subs_puts_correct_players_on_away_team(self):
        self._load_stats()
        self.parser._get_substitutions()
        assert self.parser.game.home_team.players
        assert self.parser.game.away_team.players

        correa_sub = [player for player in self.parser.game.away_team.players
                      if player.name == 'Jose Correa']
        self.assertTrue(len(correa_sub) > 0)

    def test_get_goals(self):
        self._load_stats(players=True)
        self.parser.get_goals()
        assert self.parser.game.goals
        self.assertEqual(len(self.parser.game.goals), 5)
        goal = self.parser.game.goals[1]
        self.assertEqual(goal.player.name, 'Patrick Nyarko')
        self.assertEqual(goal.time, 64)
        self.assertEqual(
            [x.name for x in goal.assisted_by],
            [u'Sherjill MacDonald', u'Maicon Santos']
        )
        self.assertEqual(goal.team.name, 'Chicago Fire')

    def test_get_bookings(self):
        self._load_stats(players=True)
        self.parser.get_bookings()
        assert self.parser.game.disciplinary_events
        self.assertEqual(len(self.parser.game.disciplinary_events), 3)
        booking = self.parser.game.disciplinary_events[0]
        self.assertEqual(booking.reason, 'Off the ball foul')
        self.assertEqual(booking.time, 22)
        self.assertEqual(booking.team.name, 'Chicago Fire')
        self.assertEqual(booking.player.name, 'Dan Paladini')


# Test formations.
# This is the relevant block of html.
#  <h2>Starting Formations</h2>
#  <div class="formations">
#    <div class="home formation-4231">
#      <div class="formation-row row-1 length-4"><span class="player no-9"><strong>11</strong>Darren Mattocks</span><span class="stretch"></span></div><div class="formation-row row-3 length-4"><span class="player no-11"><strong>7</strong>Camilo Da Silva Sanvezzo</span><span class="player no-10"><strong>28</strong>Gershon Koffie</span><span class="player no-7"><strong>14</strong>Daigo Kobayashi</span><span class="stretch"></span></div><div class="formation-row row-2 length-4"><span class="player no-4"><strong>27</strong>Jun Marques Davidson</span><span class="player no-8"><strong>13</strong>Nigel Reo-Coker</span><span class="stretch"></span></div><div class="formation-row row-4 length-4"><span class="player no-3"><strong>4</strong>Alain Rochat</span><span class="player no-6"><strong>3</strong>Brad Rusin</span><span class="player no-5"><strong>40</strong>Andy O'Brien</span><span class="player no-2"><strong>12</strong>Lee Young-Pyo</span><span class="stretch"></span></div><div class="keeper"><span class="player no-1"><strong>1</strong>Joe Cannon</span></div>      <div class="current_formation">4-2-3-1 formation</div>    </div>
#    <div class="away formation-4231">
#      <div class="formation-row row-1 length-4"><span class="player no-9"><strong>7</strong>Blas Pérez</span><span class="stretch"></span></div><div class="formation-row row-3 length-4"><span class="player no-11"><strong>6</strong>Jackson</span><span class="player no-10"><strong>10</strong>David Ferreira</span><span class="player no-7"><strong>33</strong>Kenny Cooper</span><span class="stretch"></span></div><div class="formation-row row-2 length-4"><span class="player no-4"><strong>31</strong>Michel</span><span class="player no-8"><strong>4</strong>Andrew Jacobson</span><span class="stretch"></span></div><div class="formation-row row-4 length-4"><span class="player no-3"><strong>5</strong>Jair Benitez</span><span class="player no-6"><strong>24</strong>Matt Hedges</span><span class="player no-5"><strong>14</strong>George John</span><span class="player no-2"><strong>17</strong>Zach Loyd</span><span class="stretch"></span></div><div class="keeper"><span class="player no-1"><strong>1</strong>Raúl Fernández</span></div>      <div class="current_formation">4-2-3-1 formation</div>    </div>
#  </div>
#</div>

class TestFormationScraper(unittest.TestCase):

    def setUp(self):
        super(TestFormationScraper, self).setUp()
        html = open(os.path.join(os.path.dirname(__file__), 'test_formation.html')).read()
        self.formations = formation.parse_formation_html(html)

    def tearDown(self):
        super(TestFormationScraper, self).tearDown()

    def test_home(self):
        h = self.formations['home']
        assert len(h) == 5
        assert h[0][0] == 'Joe Cannon'
        assert h[-1][0] == 'Darren Mattocks'
        assert h[1] == ['Alain Rochat', 'Brad Rusin', 'Andy O\'Brien', 'Lee Young-Pyo']

    def test_away(self):
        a = self.formations['away']
        print a
        assert a[1] == [u'Jair Benitez', u'Matt Hedges', u'George John', u'Zach Loyd']
        assert a[2] == [u'Michel', u'Andrew Jacobson']
        assert a[3] == [u'Jackson', u'David Ferreira', u'Kenny Cooper']

if __name__ == '__main__':
    unittest.main()
