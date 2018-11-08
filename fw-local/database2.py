import json
import os
from math import ceil

import containers

class Database(object):
  def __init__(self, username:str, itemtype:str, api:object, demo=False):
    self.username = username
    self.itemtype = itemtype
    self.items = []
    self.api = api
    if demo:
      self.items = self.api.getDemoPage()
  def getItems(self):
    return self.items
  # Serialization-deserialization
  @staticmethod
  def restoreFromString(username, itemtype:object, string:str, api=None):
    newDatabase = Database(username, itemtype, api)
    listOfDicts = json.loads(string)
    itemclass = containers.classByString[itemtype]
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

def restoreFromFile():
  with open('database.fdb', 'r') as dbf:
    data = dbf.read()
  return Database.restoreFromString(None, containers.Item, data)
def checkDataExists():
  return os.path.isfile('database.fdb')