import containers
from filmweb import FilmwebAPI

import json
import os

class Database(object):
  def __init__(self, username, api=None):
    self.username = username
    self.items = []
    self.api = api if api is not None else FilmwebAPI(None,None)
    self.items = self.api.getDemoPage()
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
    # ask the API how many items should there be
    # compute how many items should be requested
    # ask the API how many items are per page
    # compute how many pages should be requested
    # request these pages from the API
    # add items to the database, replacing dupes
    pass
  def hardUpdate(self):
    pass
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
