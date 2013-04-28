import unittest
import os

from mock import Mock
from BeautifulSoup import BeautifulSoup

import mls_scraper


class TestMLSScraper(unittest.TestCase):

    def setUp(self):
        super(TestMLSScraper, self).setUp()
        self.orig_requests = mls_scraper.requests
        self.stat_html = open(
            os.path.join(os.path.dirname(__file__), 'test_stats.html')
        ).read()
        mls_scraper.requests = Mock()
        self.game = mls_scraper.GameStatSet()

    def tearDown(self):
        mls_scraper.requests = self.orig_requests
        super(TestMLSScraper, self).tearDown()

    def _create_requests_mock_return(self, url='http://www.example.com/stats',
                                     status_code=200):
        requests_mock = Mock()
        requests_mock.get.return_value = Mock(
            content=self.stat_html,
            status_code=status_code,
            url=url,
        )
        mls_scraper.requests = requests_mock

    def _load_stats(self):
        self.game.stat_url = 'http://www.example.com/stats'
        self._create_requests_mock_return()
        self.game._load_stat_html()

    def test_load_stat_html(self):
        ''' Asserts that we successfully parse HTML, and translate recap urls
        into legit stat urls
        '''
        self.game.stat_url = 'http://www.example.com/recap'
        self._create_requests_mock_return(url='http://www.example.com/recap')
        self.game._load_stat_html()
        assert isinstance(self.game.stat_html, BeautifulSoup)
        self.assertEqual(self.game.stat_url, 'http://www.example.com/stats')

    def test_process_header(self):
        ''' Asserts that we get the right team names and game start time '''
        self._load_stats()
        self.game._process_header()
        self.assertEqual(self.game.home_team.name, 'Chicago Fire')
        self.assertEqual(self.game.away_team.name, 'Chivas USA')
        assert self.game.game_date

    def test_process_team_stats(self):
        self._load_stats()
        self.game._process_team_stats()
        assert self.game.home_team.stats
        assert self.game.away_team.stats

    def test_process_starters(self):
        self._load_stats()
        self.game._process_starters()
        assert self.game.home_team.players
        assert self.game.away_team.players
        self.assertEqual(len(self.game.home_team.players), 10)
        self.assertEqual(len(self.game.away_team.players), 10)

    def test_process_keepers(self):
        self._load_stats()
        self.game._process_keepers()
        assert self.game.home_team.keepers
        assert self.game.away_team.keepers
        self.assertEqual(len(self.game.home_team.keepers), 1)
        self.assertEqual(len(self.game.away_team.keepers), 1)

    def test_process_subs(self):
        self._load_stats()
        self.game._process_subs()
        assert self.game.home_team.players
        assert self.game.away_team.players
        self.assertEqual(len(self.game.home_team.players), 3)
        self.assertEqual(len(self.game.away_team.players), 3)

    def test_process_goals(self):
        self._load_stats()
        self.game._process_goals()
        assert self.game.goals
        self.assertEqual(len(self.game.goals), 5)

    def test_process_disciplinary_actions(self):
        self._load_stats()
        self.game._process_disciplinary_actions()
        assert self.game.disciplinary_events
        self.assertEqual(len(self.game.disciplinary_events), 3)

if __name__ == '__main__':
    unittest.main()
