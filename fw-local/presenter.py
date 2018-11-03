import tkinter as tk
from tkinter import ttk

import containers

class Config(object):
  # Stores the current treeview configuration, handling serialization and
  # deserialization, as well as config changes. Presenter owns one and queries
  # it when displaying items.
  # TODO: GUI aspect for user-interactive config.
  def __init__(self, itemtype:str):
    self.columns = ['title', 'year', 'rating', 'cast']
    self.columnWidths = {
      'title': 200,
      'year': 35,
      'rating': 150,
      'cast': 200
    }
    itemclass = containers.classByString[itemtype]
    self.columnHeaders = {name: bp.getHeading() for name, bp in itemclass.blueprints.items()}
  @staticmethod
  def restoreFromString(itemtype:str, string:str):
    return Config(itemtype)
  def storeToString(self):
    pass

class Presenter(object):
  """ TODO MAJOR
      3. GUI stores the savefile by serializing Presenter and Database separately
      5. Presenter is semi-configurable (i.e. stores and restores column config,
         but without GUI window for controlling it)
      6. Presenter only has a handle to the Database which is instantiated by the
         GUI, and a switch whether to display ratings or want-tos', as well as a
         flag whether to allow database updates (so that the unified underlying
         database wasn't updated twice)
      7. GUI calls update on Presenter, which calls DB
      7. Session management - API is constructed immediately, but only asks for
         login (GUI callback) when executing commands that need a session
      9. Presenter handles sorting and preview callbacks
  """
  # TODO: config fine-tuning basing on displayed item type?
  def __init__(self, root, api, database, config:str, displayRating=True):
    self.root = root
    self.main = tk.Frame(root)
    self.database = database
    self.config = Config.restoreFromString(database.itemtype, config)
    self.constructTreeView()

  def constructTreeView(self):
    self.tree = tree = ttk.Treeview(
      self.main,
      height=32,
      selectmode='none',
      columns=['id'] + self.config.columns
    )
    tree['displaycolumns'] = [c for c in tree['columns'] if c not in ['#0', 'id']]
    tree.column(column='#0', width=0)
    for column in self.config.columns:
      # TODO: column width overflow handling?
      tree.column(column=column, width=self.config.columnWidths[column], stretch=False)
      tree.heading(column=column, text=self.config.columnHeaders[column], anchor=tk.W)
    # TODO: sorting and preview spawn callbacks
    tree.grid(row=0, column=0)
    yScroll = ttk.Scrollbar(self.main, command=tree.yview)
    yScroll.grid(row=0, column=1, sticky=tk.NS)
    # TODO: column width and x-scrolling
    tree.configure(yscrollcommand=yScroll.set)#, xscrollcommand=xScroll.set)

  # TK interface for GUI placement
  def pack(self, **kw):
    self.main.pack(**kw)
  def grid(self, **kw):
    self.main.grid(**kw)

  # Display pipeline
  def filtersUpdate(self, event=None):
    # do things
    self.sortingUpdate()
  def sortingUpdate(self, event=None):
    # do things
    self.displayUpdate()
  def displayUpdate(self):
    # clear existing results
    for item in self.tree.get_children():
      self.tree.delete(item)
    # get the requested properties of items to present
    for item in self.database.getItems():
      values = [item['id']] + [item[prop] for prop in self.config.columns]
      self.tree.insert(parent='', index=0, text='', values=values)
    # TODO: update summaries, plots etc.
