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

class SortingMachine(object):
  # Changes the column heading to indicate the chosen sorting
  # Returns a dict of parameters for the sort function
  ASC_CHAR = '▲ '
  DSC_CHAR = '▼ '
  @staticmethod
  def makeLambda(key):
    return lambda x: x.properties[key]
  def __init__(self, tree, columns):
    self.tree = tree
    self.columns = columns
    self.current_id = ''
    self.original_heading = ''
    self.sorting = None
    self.ascending = False
  def update(self, column_id:str):
    # retrieve the column name which is also the name of element to sort by
    column_name = self.tree.column(column=column_id, option='id')
    # retrieve the column's original heading
    column_heading = self.tree.heading(column=column_id, option='text')
    # first run
    if not self.current_id:
      self.current_id = column_id
      self.original_heading = column_heading
      self.tree.heading(column=column_id, text=self.DSC_CHAR + self.original_heading)
      self.sorting = dict(key=self.makeLambda(column_name), reverse=self.ascending)
      return self.sorting
    # on every other run, check whether the same column was clicked again
    elif column_id == self.current_id:
      # only switch the order in this case
      if self.ascending:
        self.ascending = False
        char = self.DSC_CHAR
      else:
        self.ascending = True
        char = self.ASC_CHAR
      self.tree.heading(column=column_id, text=char + self.original_heading)
      self.sorting['reverse'] = self.ascending
      return self.sorting
    # otherwise, a different column was clicked
    else:
      # in this case, restore the original column's heading
      self.tree.heading(column=self.current_id, text=self.original_heading)
      self.current_id = column_id
      self.original_heading = column_heading
      self.ascending = False
      self.tree.heading(column=column_id, text=self.DSC_CHAR + self.original_heading)
      self.sorting = dict(key=self.makeLambda(column_name), reverse=self.ascending)
      return self.sorting
  def getSorting(self):
    return self.sorting

class Presenter(object):
  """ TODO MAJOR
      1. Presenter has a switch whether to display ratings or want-tos
      2. Presenter handles filtering and preview callbacks
  """
  def __init__(self, root, api, database, config:str, displayRating=True):
    self.root = root
    self.main = tk.Frame(root)
    self.database = database
    self.items = []
    self.config = Config.restoreFromString(database.itemtype, config)
    self.constructTreeView()
    self.sortMachine = SortingMachine(self.tree, self.config.getColumns())

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
    tree.grid(row=0, column=0)
    yScroll = ttk.Scrollbar(self.main, command=tree.yview)
    yScroll.grid(row=0, column=1, sticky=tk.NS)
    tree.configure(yscrollcommand=yScroll.set)
    # bind event handlers (TODO: detail preview)
    tree.bind('<Button-1>', self.sortingClick)

  def storeToString(self):
    return self.config.storeToString()

  # TK interface for GUI placement
  def pack(self, **kw):
    self.main.pack(**kw)
  def grid(self, **kw):
    self.main.grid(**kw)

  # Display pipeline
  # Internally, the pipeline consists of 4 steps: acquiring data from the DB,
  # filtering it using the given filters, sorting by the given criterion, and
  # displaying it on the treeview. Each of those operations is performed by
  # a dedicated function. Those functions are arranged in a call chain - each
  # one does its work and then calls the next. So there is no need to perform
  # the complete update everything when just one little thing (e.g. sorting)
  # has changed - the update can be triggered only from this specific point.
  def srcdataUpdate(self):
    # acquire from database to an internal state
    self.items = self.database.getItems()
    self.filtersUpdate()
  def filtersUpdate(self):
    # do things
    self.sortingUpdate()
  def sortingUpdate(self):
    sorting = self.sortMachine.getSorting()
    if sorting:
      self.items.sort(**sorting)
    self.displayUpdate()
  def displayUpdate(self):
    # clear existing results
    for item in self.tree.get_children():
      self.tree.delete(item)
    # get the requested properties of items to present
    for item in self.items:
      values = [item['id']] + [item[prop] for prop in self.config.getColumns()]
      self.tree.insert(parent='', index=0, text='', values=values)
    # TODO: update summaries, plots etc.

  # Interface
  def detailClick(self, event=None):
    # for spawning the detail window
    pass
  def totalUpdate(self):
    # for triggering the whole update chain
    self.srcdataUpdate()
  def sortingClick(self, event=None):
    # if a treeview heading was clicked - update the sorting
    click_region = self.tree.identify_region(event.x, event.y)
    if click_region != 'heading':
      return
    column_id = self.tree.identify_column(event.x)
    self.sortMachine.update(column_id)
    self.sortingUpdate()
