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
    page = self.api._FilmwebAPI__fetchPage(url)
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
      page = self.api._FilmwebAPI__fetchPage(url)
      path = os.path.join('assets', 'movies_{}.html'.format(i+1))
      with open(path, 'w', encoding='utf-8') as html:
        text = page.prettify()
        self.assertGreater(len(text), 100 * 2 ** 10)
        html.write(text)
    for i in range(N_PAGES):
      self.assertIn('movies_{}.html'.format(i+1), os.listdir('assets'))


if __name__ == "__main__":
  try:
    TestAPIBasics.noTests = (sys.argv[1] != 'all')
    del sys.argv[1]
  except IndexError:
    pass
  unittest.main()
