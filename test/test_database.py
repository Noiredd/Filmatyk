import os
import sys
from typing import List, Set, Tuple
import unittest

sys.path.append(os.path.join('..', 'filmatyk'))
import containers
import database
import filmweb

from api_prototype import loadDatabase, getApi

class DatabaseDifference():
  """Represents a difference between two DBs.

  Can be constructed using the "compute" @staticmethod, which can be used to
  replace the __ne__ (!=) operator on the Database class. This way, comparing
  (db1 != db2) returns an instance of this class, which:
  * holds detailed information on difference, specifically two sets of IDs (one
    for objects present in db1 and not in db2, other for vice-versa) and a list
    of all differing Items,
  * is bool-convertible, allowing its usage in if clauses,
  * has a __repr__ so can be pretty printed.

  Example usage:
    db1:database.Database
    db2:database.Database
    diff = db1 != db2
    print(diff)
  """
  @staticmethod
  def ne_to_eq(a, b):
    """Since overriding __ne__ by "compute" makes more sense than __eq__,

    we invert != to obtain ==, not the other way around.
    """
    return not (a != b)

  @staticmethod
  def compute(db1, db2):
    """Finds the difference between the two objects."""
    # Work with IDs only
    ids1 = set(item.getRawProperty('id') for item in db1)
    ids2 = set(item.getRawProperty('id') for item in db2)
    # Compute differences
    common_ids = ids1.intersection(ids2)
    only_in_1 = ids1.difference(common_ids)
    only_in_2 = ids2.difference(common_ids)
    # Extract Item instances for pretty printing
    items_1 = [item for item in db1 if item.getRawProperty('id') in only_in_1]
    items_2 = [item for item in db2 if item.getRawProperty('id') in only_in_2]
    return DatabaseDifference(only_in_1, only_in_2, items_1+items_2)

  def __init__(self, ids1:Set[int], ids2:Set[int], items:List[containers.Item]):
    self.ids1 = ids1
    self.ids2 = ids2
    self.items = {item.getRawProperty('id'): item for item in items}
    self.equal = len(self.ids1) == 0 and len(self.ids2) == 0

  def __str__(self):
    if self.equal:
      return 'These databases are equal!'
    else:
      lines = []
      if self.ids1:
        lines.append('These {} IDs were present only in DB1:'.format(len(self.ids1)))
        lines.extend('\t{} ({})'.format(i, self.items[i]['title']) for i in self.ids1)
      if self.ids2:
        lines.append('These {} IDs were present only in DB2:'.format(len(self.ids2)))
        lines.extend('\t{} ({})'.format(i, self.items[i]['title']) for i in self.ids2)
      return '\n'.join(lines)

  def __repr__(self):
    print(self)

  def __bool__(self):
    return not self.equal  


class FakeAPI(filmweb.FilmwebAPI):
  """Loads cached data instead of connecting online.

  When initializing, will look for HTML files in the given directory and treat
  them as "pages" to load data from, later when emulating "getItemsPage".
  """
  def __init__(self, src_path:str='', itemtype:str='Movie'):
    super(FakeAPI, self).__init__(None)
    self.src_path = src_path
    self.page_paths = self.initPages()
    self.item_count, self.items_per_page = self.initAnalyze(itemtype)

  def initPages(self):
    """Finds HTML files with movie ratings cached by the API tests."""
    if not os.path.exists(self.src_path):
      return []
    pages = [
      item.path for item in os.scandir(self.src_path)
      if item.name.endswith('.html') and item.name.startswith('movies_')
    ]
    return pages

  def initAnalyze(self, itemtype:str):
    """Checks how many items are in the stored files, and how many per page."""
    counts = []
    for path in self.page_paths:
      page = self.fetchPage(path)
      items = self.parsePage(page, itemtype)
      counts.append(len(items))
    # Return in the same format as getNumOf.
    # The first page will either have exactly as many items as any other page,
    # or will contain all items - in either case its length being the count of
    # items per page.
    return sum(counts), counts[0]

  def checkSession(self):
    """First part of the hack - don't bother with the session at all."""
    return True

  def fetchPage(self, path:str):
    """Load HTML from file instead of URL."""
    with open(path, 'r', encoding='utf-8') as html:
      page = filmweb.BS(html.read(), features='lxml')
    return page

  def getItemsPage(self, itemtype:str, page:int=1):
    """Hack to use cached HTMLs instead of online session."""
    path = self.page_paths[page - 1]
    #path = os.path.join(self.src_path, 'movies_{}.html'.format(page))
    page = self.fetchPage(path)
    items = self.parsePage(page, itemtype)
    return items

  def getNumOf(self, itemtype:str):
    """Simply return the values we have computed earlier (initAnalyze)."""
    return self.item_count, self.items_per_page


class UpdateScenario():
  """Database modification scenario to obtain a simulated previous state.

  Contains:
  * a list of Item indices to remove from the Database - a new Database created
    via this removal will look like these items were yet to be added,
  * a list of tuples of Item indices and IDs to add to the Database - simulates
    removal of items in the same manner.
  """
  def __init__(self, removals:List[int]=[], additions:List[Tuple[int,int]]=[]):
    self.removals = removals
    self.additions = additions


class TestDatabaseCreation(unittest.TestCase):
  """Basic test for Database loading data from scratch using the API."""
  @classmethod
  def setUpClass(self):
    self.api = FakeAPI('data')

  def test_creation(self):
    """Create a new Database and fill it with items using (Fake)API.

    Basically checks whether a new instance has as many items in it as the API
    says there are available, and whether these items are actually instances of
    the Item class.
    """
    db = database.Database(
      itemtype='Movie',
      api=self.api,
      callback=lambda x: x,
    )
    db.hardUpdate()
    known_count, _ = self.api.getNumOf('Movie')
    self.assertEqual(len(db.items), known_count)
    self.assertIsInstance(db.items[0], containers.Item)


class TestDatabaseSerialization(unittest.TestCase):
  """Test Database serialization and deserialization.

  The only test in this case validates the whole serialization-deserialization
  cycle, so if anything goes wrong, it will be hard to say which functionality
  is actually broken.
  """
  @classmethod
  def setUpClass(self):
    self.api = FakeAPI('data')

  def test_serialization(self):
    """Serialize and deserialize a Database, check if they look the same."""
    original = database.Database(
      itemtype='Movie',
      api=self.api,
      callback=lambda x: x,
    )
    # Load some initial data
    original.hardUpdate()
    # Serialize/deserialize cycle
    string = original.storeToString()
    restored = database.Database.restoreFromString(
      itemtype='Movie',
      string=string,
      api=self.api,
      callback=lambda x: x,
    )
    self.assertEqual(original, restored)


class TestDatabaseUpdates(unittest.TestCase):
  """Test Database updates capability in different initial conditions.

  Each test consists of the following 3 steps:
  * load an original Database,
  * perform some change to its content, simulating some earlier point in time
    (e.g. where some Items were not yet present),
  * call a soft update.
  The desired result is a Database back in the original state. Any differences
  are considered failures.

  The update itself is performed via a proxy, which loads data cached from
  earlier tests instead of requiring a live and authenticated session.
  """
  @classmethod
  def setUpClass(self):
    self.api = FakeAPI('data')
    # Create the original database
    self.orig_db = database.Database(
      itemtype='Movie', api=self.api, callback=lambda x: x
    )
    # Fill it with available cached data
    for i in range(len(self.api.page_paths)):
      self.orig_db.items += self.api.getItemsPage('Movie', page=i+1)

  @classmethod
  def makeModifiedDatabase(self, scenario:UpdateScenario):
    """Creates a new DB by modifying the copy according to the scenario."""
    # Create a bare new instance
    new_db = database.Database(
      itemtype=self.orig_db.itemtype,
      api=self.orig_db.api,
      callback=self.orig_db.callback,
    )
    # Remove items according to the scenario
    new_db.items = [
      item for i, item in enumerate(self.orig_db.items)
      if i not in scenario.removals
    ]
    # Add new items according to the scenario
    # The items are all clones of the last available item, with changed ID
    template = new_db.items[-1].asDict()
    template.pop('id')  # that will be replaced
    item_cls = containers.classByString[new_db.itemtype]
    # Create items and insert on their respective places
    for index, item_id in scenario.additions:
      new_item = item_cls(id=item_id, **template)
      new_db.items.insert(index, new_item)
    return new_db

  def __test_body(self, scenario):
    """Since they all look the same..."""
    alter_db = self.makeModifiedDatabase(scenario)
    # Make sure the databases are actually different!
    self.assertNotEqual(alter_db, self.orig_db)
    # Call update and check difference
    alter_db.softUpdate()
    self.assertEqual(alter_db, self.orig_db)

  # Addition tests

  def test_singleAddition(self):
    """Add a single missing item."""
    scenario = UpdateScenario(removals=[0])
    self.__test_body(scenario)

  def test_simpleAddition(self):
    """Add a few items missing from the first page."""
    scenario = UpdateScenario(removals=[0, 1, 2])
    self.__test_body(scenario)

  def test_randomAddition(self):
    """Add an item missing from somewhere on the first page."""
    scenario = UpdateScenario(removals=[4])
    self.__test_body(scenario)

  def test_nonContinuousAddition(self):
    """Add a few items non-continuously missing from the first page."""
    scenario = UpdateScenario(removals=[0, 1, 2, 3, 6])
    self.__test_body(scenario)

  def test_multipageAddition(self):
    """Add a few items non-continuously missing from multiple pages."""
    scenario = UpdateScenario(removals=[0, 1, 2, 16, 30, 32])
    self.__test_body(scenario)

  # Removal tests

  def test_singleRemoval(self):
    """Remove a single item from the first page."""
    scenario = UpdateScenario(additions=[(0, 666)])
    self.__test_body(scenario)

  def test_simpleRemoval(self):
    """Remove a few items from the first page."""
    scenario = UpdateScenario(additions=[(0, 666), (1, 4270)])
    self.__test_body(scenario)

  def test_randomRemoval(self):
    """Remove an item from somewhere on the first page."""
    scenario = UpdateScenario(additions=[(4, 420)])
    self.__test_body(scenario)

  def test_nonContinuousRemoval(self):
    """Remove a few items non-continuously from the first page."""
    scenario = UpdateScenario(
      additions=[(0, 666), (1, 4270), (2, 2137), (5, 61504)]
    )
    self.__test_body(scenario)

  def test_multipageRemoval(self):
    """Remove a few items non-continuously from multiple pages."""
    scenario = UpdateScenario(
      additions=[(3, 666), (4, 4270), (15, 2137), (35, 61504)]
    )
    self.__test_body(scenario)

  # Other tests

  def test_complexAdditionRemoval(self):
    """Add and remove a few items at once, but only from the first page."""
    scenario = UpdateScenario(
      removals=[0, 1, 2, 9, 13],
      additions=[(3, 1991), (4, 37132)]
    )

  @unittest.skip('Relevant feature not implemented yet.')
  def test_difficultAdditionRemoval(self):
    """Add and remove a few items at once from multiple pages.

    This test is extremely difficult because it is impossible to recognize such
    scenario in real usage (online), by looking at getNumOf alone. That number
    only shows the total balance of added/removed items. If that balance evens
    out on any page further than 1st (like in the case of removing some items
    and adding the same number of items), it is impossible to spot to any fast
    and simple algorithm (i.e. one that does not deeply inspect all pages).
    """
    scenario = UpdateScenario(
      removals=[0, 1, 2, 9, 33],
      additions=[(3, 1991), (34, 37132)]
    )

  def test_hardUpdate(self):
    """Make "random" removals and additions, then hard update."""
    scenario = UpdateScenario(
      removals=[1, 5, 6, 7, 40],
      additions=[(0, 666), (13, 667)]
    )
    alter_db = self.makeModifiedDatabase(scenario)
    self.assertNotEqual(alter_db, self.orig_db)
    alter_db.hardUpdate()
    self.assertEqual(alter_db, self.orig_db)


if __name__ == "__main__":
  database.Database.__ne__ = DatabaseDifference.compute
  database.Database.__eq__ = DatabaseDifference.ne_to_eq
  unittest.main()
