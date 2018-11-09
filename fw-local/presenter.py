import json
import tkinter as tk
from tkinter import ttk

import containers
from defaults import DEFAULT_CONFIGS

class Config(object):
  # Stores the current treeview configuration, handling serialization and
  # deserialization, as well as config changes. Presenter owns one and queries
  # it when displaying items.
  # TODO: GUI aspect for user-interactive config.
  def __init__(self, itemtype:str, columns:dict={}):
    self.rawConfig = columns
    itemclass = containers.classByString[itemtype]
    self.allColumns = [name for name in itemclass.blueprints.items()]
    self.columnHeaders = {name: bp.getHeading() for name, bp in itemclass.blueprints.items()}
    self.columnWidths = {name: bp.getColWidth() for name, bp in itemclass.blueprints.items()}
    self.columns = {}
    for name in self.rawConfig.keys():
      default_width = self.columnWidths[name]
      config_width = self.rawConfig[name]
      set_width = config_width if config_width is not None else default_width
      self.columns[name] = set_width
  def getColumns(self):
    return list(self.columns.keys())
  def getWidth(self, column):
    return self.columns[column]
  def getHeading(self, column):
    return self.columnHeaders[column]
  @staticmethod
  def restoreFromString(itemtype:str, string:str):
    # The config string is a JSON dump of a dict that contains columns to be
    # presented as keys, and their widths as values (or None for defaults).
    if string == '':
      config = DEFAULT_CONFIGS[itemtype]
    else:
      config = json.loads(string)
    return Config(itemtype, config)
  def storeToString(self):
    return json.dumps(self.rawConfig)

class Presenter(object):
  """ TODO MAJOR
      6. Presenter only has a handle to the Database which is instantiated by the
         GUI, and a switch whether to display ratings or want-tos
      7. GUI calls update on Presenter, which calls DB
      7. Session management - API is constructed immediately, but only asks for
         login (GUI callback) when executing commands that need a session
      9. Presenter handles sorting and preview callbacks
  """
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
      columns=['id'] + self.config.getColumns()
    )
    tree['displaycolumns'] = [c for c in tree['columns'] if c not in ['#0', 'id']]
    tree.column(column='#0', width=0)
    for column in self.config.getColumns():
      # TODO (low priority): treeview total width limiting and X-scrolling
      # potential problem: Notebook view (different TVs having different widths)
      # may be unnecessary though - why try to cram all the info in a single TV,
      # if there is already a Detail view (e.g. for those long comments)?
      tree.column(column=column, width=self.config.getWidth(column), stretch=False)
      tree.heading(column=column, text=self.config.getHeading(column), anchor=tk.W)
    # TODO: sorting and preview spawn callbacks
    tree.grid(row=0, column=0)
    yScroll = ttk.Scrollbar(self.main, command=tree.yview)
    yScroll.grid(row=0, column=1, sticky=tk.NS)
    tree.configure(yscrollcommand=yScroll.set)

  def storeToString(self):
    return self.config.storeToString()

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
      values = [item['id']] + [item[prop] for prop in self.config.getColumns()]
      self.tree.insert(parent='', index=0, text='', values=values)
    # TODO: update summaries, plots etc.
