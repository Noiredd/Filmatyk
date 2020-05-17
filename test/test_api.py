import functools
import getpass
import os
import sys
import unittest

from bs4 import BeautifulSoup as BS

sys.path.append(os.path.join('..', 'filmatyk'))
import containers
import filmweb

class TestAPIBasics(unittest.TestCase):
  """Test basic API funcionality: login & fetching raw HTML data from Filmweb.

  This test is skipped by default, as it requires obtaining a session (and that
  requires logging in, which would become rather tedious when experimenting).
  It however produces assets later used by other tests, therefore it is crucial
  that it be run before any other tests at least once.
  """
  noTests = True

  @classmethod
  def setUpClass(self):
    self.api = None
    self.assets_path = 'assets'

  @classmethod
  def storeAPI(self, api):
    self.api = api

  def setUp(self):
    """Ensure the tests are skipped if the flag is set."""
    if self.noTests:
      self.skipTest(reason='Basics tests skipped by default!')

  @staticmethod
  def login_callback(username, password, *args, **kwargs):
    """Fake callback for FilmwebAPI, to pass instead of a GUI login handler.

    "username" and "password" must be supplied prior to passing to FilmwebAPI
    by functools.partial (or similar).
    """
    isOK, session = filmweb.FilmwebAPI.login(username, password)
    if not isOK:
      session = None
    return (session, username)

  def test_01_login(self):
    """Attempt to log in to Filmweb. Requires credentials."""
    username = input('Username: ').strip()
    password = getpass.getpass().strip()
    login_callback = functools.partial(
      self.login_callback,
      password=password,
    )
    api = filmweb.FilmwebAPI(login_callback, username)
    self.assertIsNotNone(api)
    api.checkSession()
    self.assertIsNotNone(api.session)
    self.storeAPI(api)

  def test_02_fetch_one_movie(self):
    """Attempt to download a single page of movie ratings from Filmweb."""
    self.assertIsNotNone(self.api)
    self.assertIsNotNone(self.api.session)
    url = self.api.constants.getUserMoviePage(page=1)
    page = self.api.fetchPage(url)
    text = page.prettify()
    self.assertIsInstance(text, str)
    self.assertGreater(len(text), 100 * 2 ** 10)

  def test_10_fetch_save_movies(self):
    """Attempt to download 3 pages of movie ratings from Filmweb.

    This also stores them as "assets" for other tests.
    """
    N_PAGES = 3
    for i in range(N_PAGES):
      getURL = self.api.urlGenerationMethods['Movie']
      url = getURL(page=i+1)
      page = self.api.fetchPage(url)
      path = os.path.join('assets', 'movies_{}.html'.format(i+1))
      with open(path, 'w', encoding='utf-8') as html:
        text = page.prettify()
        self.assertGreater(len(text), 100 * 2 ** 10)
        html.write(text)
    for i in range(N_PAGES):
      self.assertIn('movies_{}.html'.format(i+1), os.listdir('assets'))

  def test_20_fetch_save_series(self):
    """Attempt to download and save a page of series ratings."""
    getURL = self.api.urlGenerationMethods['Series']
    page_num = 1
    url = getURL(page=page_num)
    page = self.api.fetchPage(url)
    path = os.path.join('assets', 'series_{}.html'.format(page_num))
    with open(path, 'w', encoding='utf-8') as html:
      text = page.prettify()
      self.assertGreater(len(text), 100 * 2 ** 10)
      html.write(text)
    self.assertIn('series_{}.html'.format(page_num), os.listdir('assets'))

  def test_30_fetch_save_games(self):
    """Attempt to download and save a page of game ratings."""
    getURL = self.api.urlGenerationMethods['Game']
    page_num = 1
    url = getURL(page=page_num)
    page = self.api.fetchPage(url)
    path = os.path.join('assets', 'games_{}.html'.format(page_num))
    with open(path, 'w', encoding='utf-8') as html:
      text = page.prettify()
      self.assertGreater(len(text), 100 * 2 ** 10)
      html.write(text)
    self.assertIn('games_{}.html'.format(page_num), os.listdir('assets'))

  def __test_count_body(self, itemtype:str):
    """Performs a single test of item count retrieval."""
    item_count, items_per_page = self.api.getNumOf(itemtype)
    self.assertGreater(item_count, 0)
    self.assertGreaterEqual(item_count, items_per_page)

  def test_40_get_num_of_movies(self):
    """Attempt to retrieve the item count of type 'Movie'."""
    self.__test_count_body('Movie')

  def test_41_get_num_of_series(self):
    """Attempt to retrieve the item count of type 'Series'."""
    self.__test_count_body('Series')

  def test_42_get_num_of_games(self):
    """Attempt to retrieve the item count of type 'Game'."""
    self.__test_count_body('Game')


class TestAPIParsing(unittest.TestCase):
  """Test API parsing functionalities.

  Basic tests are done on Movies, later the suite extends to other types too.

  Basics start with extraction of main data region - a div that holds details
  of all items and ratings. Then tests parsing of individual items, finally of
  a whole page.
  """

  @classmethod
  def setUpClass(self):
    self.api = filmweb.FilmwebAPI(None)
    self.moviePagePath = os.path.join('assets', 'movies_1.html')
    self.seriesPagePath = os.path.join('assets', 'series_1.html')
    self.gamePagePath = os.path.join('assets', 'games_1.html')

  @staticmethod
  def getPage(path:str):
    """Load a cached page into a BeautifulSoup format."""
    with open(path, 'r', encoding='utf-8') as html:
      return BS(html.read(), features='lxml')

  def test_01_data_source_extract(self):
    """Find the main div containing details of rated objects."""
    page = self.getPage(self.moviePagePath)
    div = self.api.extractDataSource(page)
    self.assertIsNotNone(div)
    self.assertGreater(len(div.getText()), 10**4)

  def test_02_item_divs_extract(self):
    """Retrieve all the item detail divs."""
    page = self.getPage(self.moviePagePath)
    div = self.api.extractDataSource(page)
    items = self.api.extractItems(div)
    self.assertGreater(len(items), 0)

  def test_03_item_ratings_extract(self):
    """Retrieve all the item rating strings."""
    page = self.getPage(self.moviePagePath)
    div = self.api.extractDataSource(page)
    items = self.api.extractItems(div)
    ratings = self.api.extractRatings(div)
    self.assertEqual(len(items), len(ratings))

  def __test_single_body(self, page:BS, itemtype:str):
    """Performs the entire test of single item parsing."""
    div = self.api.extractDataSource(page)
    items = self.api.extractItems(div)
    item = self.api.parseOne(items[0], itemtype)
    # We don't know much about the parsed items, but they will have titles...
    self.assertGreater(len(item['title']), 2)
    ratings = self.api.extractRatings(div)
    rating, rid = self.api.parseRating(ratings[0])
    # ...and ratings, and IDs
    self.assertIn('rating', rating.keys())
    self.assertEqual(rid, item.getRawProperty('id'))

  def test_10_single_movie_parsing(self):
    """Parse a single movie and rating."""
    page = self.getPage(self.moviePagePath)
    self.__test_single_body(page, 'Movie')

  def test_11_single_series_parsing(self):
    """Parse a single series and rating."""
    page = self.getPage(self.seriesPagePath)
    self.__test_single_body(page, 'Series')

  def test_12_single_game_parsing(self):
    """Parse a single game and rating."""
    page = self.getPage(self.gamePagePath)
    self.__test_single_body(page, 'Game')

  def test_20_parse_movie_page(self):
    """Parse an entire page of movies."""
    page = self.getPage(self.moviePagePath)
    items = self.api.parsePage(page, 'Movie')
    # Again, it's hard to tell anything about the items we retrieve, except for
    # the fact that they will exist, and no exception will be thrown during
    # parsing.
    self.assertGreater(len(items), 0)

  def test_21_parse_series_page(self):
    """Parse an entire page of movies."""
    page = self.getPage(self.seriesPagePath)
    items = self.api.parsePage(page, 'Series')
    self.assertGreater(len(items), 0)

  def test_22_parse_game_page(self):
    """Parse an entire page of movies."""
    page = self.getPage(self.gamePagePath)
    items = self.api.parsePage(page, 'Game')
    self.assertGreater(len(items), 0)


if __name__ == "__main__":
  try:
    TestAPIBasics.noTests = (sys.argv[1] != 'all')
    del sys.argv[1]
  except IndexError:
    pass
  unittest.main()
