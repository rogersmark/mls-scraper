import sys
from optparse import OptionParser

import requests
from BeautifulSoup import BeautifulSoup


def digest_stats(soup):
    stats_table = soup.find(id='stats-game')
    header = stats_table.findNext('tr')
    team_one_stats = {'name': header.findChildren()[0].text}
    team_two_stats = {'name': header.findChildren()[-1].text}
    stats_row = header.findNext('tr')
    while stats_row:
        stat_title = stats_row.findChildren()[1].text
        team_one_stats[stat_title] = stats_row.findChildren()[0].text
        team_two_stats[stat_title] = stats_row.findChildren()[-1].text
        stats_row = stats_row.findNext('tr')
    print team_one_stats
    print team_two_stats

def main(urls):
    for url in urls:
        resp = requests.get(url)
        if not resp.status_code == 200:
            print 'Failed to load %s' % url
            continue
        soup = BeautifulSoup(resp.content)
        digest_stats(soup)


if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    sys.exit(main(args))
