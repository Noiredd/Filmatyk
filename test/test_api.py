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

  def test_02_fetch_one(self):
    """Attempt to download a single page of movie ratings from Filmweb."""
    self.assertIsNotNone(self.api)
    self.assertIsNotNone(self.api.session)
    url = self.api.Constants.getUserMoviePage(
      self.api.username,
      page=1,
    )
    page = self.api.fetchPage(url)
    text = page.prettify()
    self.assertIsInstance(text, str)
    self.assertGreater(len(text), 100 * 2 ** 10)

  def test_03_fetch_save(self):
    """Attempt to download 3 pages of movie ratings from Filmweb.

    This also stores them as "assets" for other tests.
    """
    N_PAGES = 3
    for i in range(N_PAGES):
      url = self.api.Constants.getUserMoviePage(self.api.username, page=i+1)
      page = self.api.fetchPage(url)
      path = os.path.join('assets', 'movies_{}.html'.format(i+1))
      with open(path, 'w', encoding='utf-8') as html:
        text = page.prettify()
        self.assertGreater(len(text), 100 * 2 ** 10)
        html.write(text)
    for i in range(N_PAGES):
      self.assertIn('movies_{}.html'.format(i+1), os.listdir('assets'))


class TestAPIParsing(unittest.TestCase):
  """Test API parsing functionalities.

  Starts with extraction of main data region - a div that holds details of all
  items and ratings. Then tests parsing of individual items, finally of a whole
  page.
  """

  @classmethod
  def setUpClass(self):
    self.api = filmweb.FilmwebAPI(None)
    self.page = None
    with open(os.path.join('assets', 'movies_1.html'), 'r', encoding='utf-8') as html:
      self.page = BS(html.read(), 'lxml')

  def test_01_data_source_extract(self):
    """Find the main div containing details of rated objects."""
    div = self.api.extractDataSource(self.page)
    self.assertIsNotNone(div)
    self.assertGreater(len(div.getText()), 10**4)

  def test_02_item_divs_extract(self):
    """Retrieve all the item detail divs."""
    div = self.api.extractDataSource(self.page)
    items = self.api.extractItems(div)
    self.assertGreater(len(items), 0)

  def test_03_item_ratings_extract(self):
    """Retrieve all the item rating strings."""
    div = self.api.extractDataSource(self.page)
    items = self.api.extractItems(div)
    ratings = self.api.extractRatings(div)
    self.assertEqual(len(items), len(ratings))

  def test_04_single_parsing(self):
    """Parse a single item and rating."""
    div = self.api.extractDataSource(self.page)
    items = self.api.extractItems(div)
    item = self.api.parseOne(items[0], 'Movie')
    self.assertGreater(len(item['title']), 2)
    ratings = self.api.extractRatings(div)
    rating, rid = self.api.parseRating(ratings[0])
    self.assertIn('rating', rating.keys())
    self.assertEqual(rid, item.getRawProperty('id'))

  def test_10_parse_page(self):
    """Parse an entire page of movies."""
    items = self.api.parsePage(self.page, 'Movie')
    self.assertGreater(len(items), 0)


if __name__ == "__main__":
  try:
    TestAPIBasics.noTests = (sys.argv[1] != 'all')
    del sys.argv[1]
  except IndexError:
    pass
  unittest.main()
