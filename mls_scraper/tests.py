#!/usr/local/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os

from mock import Mock
from BeautifulSoup import BeautifulSoup

import parser


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
                                     status_code=200, html=None):
        requests_mock = Mock()
        requests_mock.get.return_value = Mock(
            content=html if html else self.stat_html,
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

    def test_generate_stats(self):
        ''' Tests the big method of generating all of the stats for a parser.
        We're mostly concerned that it just hits all the right methods, since
        the various methods themselves are all tested below.
        '''
        methods_to_call = [
            '_load_stat_html',
            'get_general_info',
            'get_team_stats',
            'get_players',
            'get_events',
            'get_formations',
        ]
        pre_mocks = []
        for method in methods_to_call:
            pre_mocks.append(getattr(self.parser, method))
            setattr(self.parser, method, Mock())

        self.parser._generate_stats()
        for count, method in enumerate(methods_to_call):
            assert getattr(self.parser, method).called
            setattr(self.parser, method, pre_mocks[count])

    def test_get_events(self):
        ''' Tests the method that calls our various event grabbers. Just
        testing that it calls the right methods, since we already have tests
        for the individual methods elsewhere.
        '''
        methods_to_call = [
            '_get_substitution_events',
            '_get_goals',
            '_get_bookings',
        ]
        pre_mocks = []
        for method in methods_to_call:
            pre_mocks.append(getattr(self.parser, method))
            setattr(self.parser, method, Mock())

        self.parser.get_events()
        for count, method in enumerate(methods_to_call):
            assert getattr(self.parser, method).called
            setattr(self.parser, method, pre_mocks[count])

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
        self.parser._get_goals()
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

    def test_own_goal(self):
        ''' Tests that own goals are handled properly '''
        self._load_stats(players=True)
        self.parser._get_goals()
        assert self.parser.game.goals
        self.assertEqual(len(self.parser.game.goals), 5)
        goal = self.parser.game.goals[-1]
        self.assertEqual(goal.player.name, 'Jalil Anibaba')
        assert goal.own_goal

    def test_process_subs_list_generates_subs_list(self):
        self._load_stats(players=True)
        self.parser._get_substitution_events()

        self.assertTrue(hasattr(self.parser.game.home_team, "subs"))
        self.assertTrue(hasattr(self.parser.game.away_team, "subs"))

    def test_process_subs_list_has_correct_number(self):
        self._load_stats(players=True)
        self.parser._get_substitution_events()

        self.assertEqual(6, len(self.parser.game.subs))

    def test_process_subs_list_has_correct_players(self):
        self._load_stats(players=True)
        self.parser._get_substitution_events()

        correa_sub = [sub for sub in self.parser.game.subs
                      if sub.player_on.name == 'Jose Correa']
        self.assertTrue(len(correa_sub) > 0)

    def test_process_subs_list_have_correct_minutes(self):
        self._load_stats(players=True)
        self.parser._get_substitution_events()

        correa_sub = [sub for sub in self.parser.game.subs
                      if sub.player_on.name == 'Jose Correa'][0]
        self.assertEqual(74, correa_sub.time)

    def test_get_bookings(self):
        self._load_stats(players=True)
        self.parser._get_bookings()
        assert self.parser.game.disciplinary_events
        self.assertEqual(len(self.parser.game.disciplinary_events), 4)
        booking = self.parser.game.disciplinary_events[0]
        self.assertEqual(booking.reason, 'Off the ball foul')
        self.assertEqual(booking.time, 22)
        self.assertEqual(booking.team.name, 'Chicago Fire')
        self.assertEqual(booking.player.name, 'Dan Paladini')

        bench_booking = self.parser.game.disciplinary_events[3]
        self.assertEqual(bench_booking.reason, 'Being on the bench')
        self.assertEqual(bench_booking.time, 90)
        self.assertEqual(bench_booking.player.name, 'Bench Player')
        assert bench_booking.player in self.parser.game.away_team.players

    def test_get_formations(self):
        ''' Test parsing out the formation information for each team '''
        html = open(os.path.join(
            os.path.dirname(__file__), 'test_formation.html')).read()
        self._load_stats(players=True)
        self._create_requests_mock_return(html=html)
        self.parser.get_formations()
        self.assertEqual(
            self.parser.game.home_team.formation.formation,
            '4-2-3-1'
        )
        self.assertEqual(
            self.parser.game.away_team.formation.formation,
            '3-5-2'
        )


if __name__ == '__main__':
    unittest.main()
