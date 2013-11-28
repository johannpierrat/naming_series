import urllib2
import re
import sys
import itertools
from HTMLParser import HTMLParser
from BeautifulSoup import BeautifulSoup

def get_starting_season(soup):
    """ Return the first season number """
    season_find = re.compile("(?:serie?|Season)s? \d+", flags=re.IGNORECASE)
    pilot_find = re.compile("Pilot", flags=re.IGNORECASE)

    for found in soup.findAll(
            'span',
            attrs={'class':'mw-headline'}):
        # we consider pilot as season 0
        if pilot_find.findall(str(found)):
            return 0
        for season_found in season_find.findall(str(found)):
            return int(re.findall("\d+", season_found)[0])

def parse_title(title):
    """ Parse the title from html format to file format """
    parser = HTMLParser()

    title = parser.unescape(title)
    title = re.sub('"', "", title)

    return title

def combination_word(word):
    """ Creat iterator for every test for a single word """
    word = word.lower()
    for p in itertools.product(*[(0,1)] * len(word)):
        yield ''.join(c.upper() if t else c for t,c in itertools.izip(p, word))


def get_episode_list(serie):
    """
    Get every episode title from the entered series
    It uses wikipedia list of episode and does not work for some cases
    """

    resp = None

    for s in combination_word(serie):
        url = "http://en.wikipedia.org/wiki/List_of_%s_episodes" % s
        try:
            resp = urllib2.urlopen(url.lower())
            break
        except urllib2.HTTPError:
            pass

    if resp is None:
        sys.stderr.write("Unable to find information for serie %s\n" % serie)
        return None

    res = {}
    soup_html = BeautifulSoup(resp)
    season_num = get_starting_season(soup_html)
    if season_num is None:
        season_num = 1

    for table in soup_html.findAll(
            'table',
            attrs={'class':re.compile(r"\bwikitable\b.*")}):
        res[season_num] = {}
        episode_num = 1
        soup_table = BeautifulSoup(str(table))
        for row in soup_table.findAll(
                'tr',
                attrs={'class':'vevent'}):
            soup_row = BeautifulSoup(str(row))
            title = soup_row.find('td', attrs={'class':'summary'}).text
            res[season_num][episode_num] = parse_title(title)
            episode_num = episode_num + 1
        if episode_num > 1:
            season_num = season_num + 1

    return res


if __name__ == "__main__":
    res = get_episode_list("it_crowds")
    if res is not None:
        for season in res:
            for episode in res[season]:
                print(
                        "season %d episode %d: %s"
                        % (season, episode, res[season][episode])
                )
