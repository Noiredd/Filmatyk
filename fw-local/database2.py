import json
import os
from math import ceil

import containers

class Database(object):
  def __init__(self, itemtype:str, api:object, demo=False):
    self.itemtype = itemtype
    self.items = []
    self.api = api
    if demo:
      self.items = self.api.getDemoPage()
  def getItems(self):
    return self.items
  # Serialization-deserialization
  @staticmethod
  def restoreFromString(itemtype:object, string:str, api=None):
    newDatabase = Database(itemtype, api)
    if not string:
      # simply return a raw, empty DB
      return newDatabase
    listOfDicts = json.loads(string)
    itemclass = containers.classByString[itemtype]
    newDatabase.items = [itemclass(**dct) for dct in listOfDicts]
    return newDatabase
  def storeToString(self):
    return json.dumps([item.asDict() for item in self.items])
  # Data acquisition
  def softUpdate(self):
    # ask the API how many items should there be and how many are there per page
    first_request = self.api.getNumOf(self.itemtype)
    if first_request is None:
      #this will happen if the user fails to log in
      return None
    rated, per_page = first_request
    # compute how many pages should be requested
    pages = ceil((rated-len(self.items))/per_page)
    # request these pages from the API
    itemPages = []
    for page in range(pages):
      itemPages.append(self.api.getItemsPage(itemtype=self.itemtype, page=page))
      break # DEBUG DEBUG DEBUG DEBUG
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
    # in theory, this removes all existing items and recollects the whole data
    # but in practice this reacquisition may fall - in which case we shouldn't
    # just lose the existing database and shrug, so this backs it up first
    old_items = self.items
    self.items = []
    if not self.softUpdate():
      self.items = old_items

