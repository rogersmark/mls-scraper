
import re

import requests
from BeautifulSoup import BeautifulSoup

def get_contents(l, formatter=lambda s: s):
    """Fetch the contents from a soup object."""

    if not hasattr(l, 'contents'):
        s = l
    else:
        s = ""

        for e in l.contents:
            s += get_contents(e)
    return formatter(s.strip())

def process_formation(soup):
    strip_leading_digits = lambda s: re.match("\d*(.*)", s).groups()[0].strip()
    extract_player = lambda tag: strip_leading_digits(get_contents(tag))
    extract_line = lambda l: [extract_player(e) for e in l if extract_player(e)]

    try:
        lines = soup.findAll('div')
    except:
        import pdb; pdb.set_trace()
    f = [extract_line(e) for e in lines[:-1]]
    f.reverse()
    return f

def parse_formation_url(url):
    resp = requests.get(url)
    return parse_formation_html(resp.content)


def parse_formation_html(html):
    soup = BeautifulSoup(html)
    formations = soup.find('div', {'class':'formations'})
    home, away = formations.findAll('div', recursive=False)
    return {
        'home': process_formation(home),
        'away': process_formation(away)
        }



if __name__ == "__main__":
    print parse_formation_url('http://www.mlssoccer.com/matchcenter/2013-04-27-MTL-v-CHI/formation')
    
    
    
