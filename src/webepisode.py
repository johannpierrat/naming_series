import urllib2
import re
import sys
import itertools
from HTMLParser import HTMLParser
from BeautifulSoup import BeautifulSoup
import multiprocessing
import Queue


class TestProcess(multiprocessing.Process):
    def __init__(self, urls_queue, result_queue, verbose=False):
        multiprocessing.Process.__init__(self)

        self.urls = urls_queue
        self.result = result_queue
        self.verbose = verbose

    def run(self):
        while True:
            try:
                url = self.urls.get_nowait()
            except Queue.Empty:
                break

            if self.verbose:
                print 'Testing url "{}"'.format(url)
            ret = urllib2.Request(url)

            try:
                urllib2.urlopen(ret)
                if self.verbose:
                    print 'URL "{}" found'.format(url)
                self.result.put(url)
            except (urllib2.HTTPError, urllib2.URLError):
                pass


def get_starting_season(soup):
    """ Return the first season number """
    season_find = re.compile("(?:serie?|Season)s? \d+", flags=re.IGNORECASE)
    pilot_find = re.compile("Pilot", flags=re.IGNORECASE)

    for found in soup.findAll(
            'span',
            attrs={'class': "mw-headline"}):
        # we consider pilot as season 0
        if pilot_find.findall(str(found)):
            return 0
        for season_found in season_find.findall(str(found)):
            return int(re.findall("\d+", season_found)[0])


def parse_title(title):
    """ Parse the title from html format to file format """
    parser = HTMLParser()

    title = parser.unescape(title)
    # We only take the first title in case there is multiple
    title = title.split('""')[0]
    title = re.sub('"', '', title)

    return title


def combination_word(word):
    """ Creat iterator for every test for a single word """

    # Try every capitalization of everyword
    words = [w if w.isupper() else w.lower() for w in word.split(' ')]
    for p in itertools.product(*[(0, 1)] * len(words)):
        yield '_'.join(
                c.capitalize() if t else c for t, c in itertools.izip(p, words)
        )


def get_episode_list(serie, verbose=False, start_season=None):
    """
    Get every episode title from the entered series
    Note: It uses wikipedia list of episode and does not work for some cases
    """

    resp = None

    url_queue = multiprocessing.Queue()
    result_queue = multiprocessing.Queue()

    num_proc = 0
    for s in combination_word(serie):
        url = "http://en.wikipedia.org/wiki/List_of_{}_episodes".format(s)
        num_proc += 1
        url_queue.put(url)

    num_proc = 9 if num_proc > 9 else num_proc
    for i in xrange(num_proc):
        test = TestProcess(url_queue, result_queue)
        test.start()

    while result_queue:
        url = result_queue.get()
        resp = urllib2.urlopen(url)
        break

    if resp is None:
        sys.stderr.write("Unable to find information for serie %s\n" % serie)
        return None

    res = {}
    soup_html = BeautifulSoup(resp)
    if start_season is None:
        season_num = get_starting_season(soup_html)
    else:
        season_num = start_season
    if season_num is None:
        season_num = 1

    for table in soup_html.findAll(
            'table',
            attrs={'class': re.compile(r"\bwikitable\b.*")}):
        res[season_num] = {}
        episode_num = 1
        soup_table = BeautifulSoup(str(table))
        for row in soup_table.findAll(
                'tr',
                attrs={'class': 'vevent'}):
            soup_row = BeautifulSoup(str(row))
            title = soup_row.find('td', attrs={'class': 'summary'}).text
            res[season_num][episode_num] = (
                    parse_title(title).encode(
                            "ascii",
                            "replace")
                    )
            episode_num = episode_num + 1
        if episode_num > 1:
            season_num = season_num + 1

    return res


if __name__ == "__main__":
    res = get_episode_list("Battlestar Galactica (2004 TV series)", True)
    if res is not None:
        for season in res:
            for episode in res[season]:
                print(
                        "season {} episode {}: {}".format(
                                season, episode, res[season][episode]
                        )
                )
