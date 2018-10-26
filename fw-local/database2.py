import containers
import filmweb as fw

import json
import os
from math import ceil

class Database(object):
  def __init__(self, username:str, itemtype:str='Item', api:object=None):
    self.username = username
    self.itemtype = itemtype
    self.items = []
    self.api = api if api is not None else fw.FilmwebAPI(None,None)
  def getItems(self):
    return self.items
  # Serialization-deserialization
  @staticmethod
  def restoreFromString(username, itemclass:object, string:str, api=None):
    newDatabase = Database(username, api)
    listOfDicts = json.loads(string)
    newDatabase.items = [itemclass(**dct) for dct in listOfDicts]
    return newDatabase
  def storeToString(self):
    return json.dumps([item.asDict() for item in self.items])
  def save(self):
    with open('database.fdb', 'w') as dbf:
      dbf.write(self.storeToString())
  # Data acquisition
  def softUpdate(self):
    # TODO: user management - not as simple as it may seem
    # ask the API how many items should there be and how many are there per page
    rated, per_page = self.api.getNumOf(self.itemtype)
    # compute how many pages should be requested
    pages = ceil((rated-len(self.items))/per_page)
    # request these pages from the API
    itemPages = []
    for page in range(pages):
      itemPages.append(self.api.getItemsPage(itemtype=self.itemtype, page=page))
      #print("Got page {}/{}!".format(page+1, pages))  # TODO: progress bar?
    new_items = [item for page in itemPages for item in page]
    # add items to the database, replacing duplicates by new ones
    old_items = self.items
    self.items = new_items
    new_ids = [item['id'] for item in new_items]
    for item in old_items:
      if item['id'] not in new_ids:
        self.items.append(item)
  def hardUpdate(self):
    # delete all items and get them from scratch
    self.items = []
    self.softUpdate()
  # LEGACY INTERFACE
  def setConfig(self, config):
    self.config = config
  def filterMovies(self, filters:dict={}):
    pass
  def sortMovies(self, sorting):
    pass
  def returnMovies(self):
    self.filtered = self.items #some of the GUI code asks for this attr
    self.movies = self.items   #some of the GUI code asks for this attr
    display = []
    histogram = [0 for i in range(11)]
    for movie in self.items:
      mov = []
      mov.append(movie['id'])
      for conf in self.config:
        #Each conf is a 2-tuple containing key name and presentation rule
        key, rule = conf
        mov.append(movie[key])
      display.append(mov)
      #This can be bugged for now, but in the end it will not be done by the
      #database anyway, but a dedicated statistics module
      #rating = int(movie['rating'])
      #histogram[rating] += 1
    return display, histogram
  def getListOfAll(self, what):
    return []
  def getYearsSeen(self):
    return []
  def getMovieByID(self, id):
    for movie in self.items:
      if movie['id'] == str(id):
        return movie
    return None

def restoreFromFile():
  with open('database.fdb', 'r') as dbf:
    data = dbf.read()
  return Database.restoreFromString(None, containers.Item, data)
def checkDataExists():
  return os.path.isfile('database.fdb')
