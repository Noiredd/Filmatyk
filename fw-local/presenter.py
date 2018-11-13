import json
import tkinter as tk
from tkinter import ttk

import containers
from defaults import DEFAULT_CONFIGS, DEFAULT_SORTING
from detailviews import DetailWindow
from filters import FilterMachine
from statview import StatView

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
  def __init__(self, tree, columns:list, itemtype:str):
    self.tree = tree
    self.columns = columns
    self.current_id = ''
    self.original_heading = ''
    self.sorting = None
    self.ascending = False
    self.firstRun(itemtype)
  def firstRun(self, itemtype:str):
    default_key, default_asc = DEFAULT_SORTING[itemtype]
    # get the index of a column that holds the default key (if there is such!)
    if default_key not in self.columns:
      return
    column_num = self.columns.index(default_key) + 1 # plus a #0 ID column
    column_id = '#{}'.format(column_num)
    self.update(column_id)
    self.ascending = default_asc
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
  """
  def __init__(self, root, api, database, config:str, displayRating=True):
    self.root = root
    self.main = tk.Frame(root)
    self.database = database
    self.items = []
    self.config = Config.restoreFromString(database.itemtype, config)
    self.__construct()
    self.sortMachine = SortingMachine(self.tree, self.config.getColumns(), self.database.itemtype)
    self.filtMachine = FilterMachine(self.filtersUpdate)
    self.detailWindow = DetailWindow.getDetailWindow()

  def __construct(self):
    # TREEVIEW
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
    tree.grid(row=0, column=0, rowspan=2)
    yScroll = ttk.Scrollbar(self.main, command=tree.yview)
    yScroll.grid(row=0, column=1, rowspan=2, sticky=tk.NS)
    tree.configure(yscrollcommand=yScroll.set)
    # bind event handlers (TODO: column resize, pop-up menu)
    tree.bind('<Button-1>', self.sortingClick)
    tree.bind('<Double-Button-1>', self.detailClick)
    # STATISTICS VIEW
    self.stats = StatView(self.main, self.database.itemtype)
    self.stats.grid(row=0, column=2, sticky=tk.NW)
    # FILTER FRAME
    self.fframe = tk.Frame(self.main)
    self.fframe.grid(row=1, column=2, sticky=tk.NW)
    # store the row and col range of inserted filters to know where to place the
    # reset all button
    self.fframe_grid = [0, 0]
    # delay to the first update, after all of the filters have been added
    self.isResetAllButtonPlaced = False
  def __placeResetAllButton(self):
    rab_row = self.fframe_grid[0]
    rab_col = self.fframe_grid[1]
    raButton = tk.Button(self.fframe, text='Resetuj filtry!', command=self.filtMachine.resetAllFilters)
    raButton.grid(row=rab_row, column=rab_col, rowspan=rab_row+1, columnspan=rab_col+1, sticky=tk.SE)

  def storeToString(self):
    return self.config.storeToString()

  # TK interface for GUI placement
  def pack(self, **kw):
    self.main.pack(**kw)
  def grid(self, **kw):
    self.main.grid(**kw)

  def addFilter(self, filter_class, **grid_args):
    filter_object = filter_class(self.fframe, self.filtMachine.updateCallback)
    self.filtMachine.registerFilter(filter_object)
    filter_object.grid(**grid_args)
    # remember where was the furthest filter placed
    if grid_args['row'] > self.fframe_grid[0]:
      self.fframe_grid[0] = grid_args['row']
    if grid_args['column'] > self.fframe_grid[1]:
      self.fframe_grid[1] = grid_args['column']

  # Display pipeline
  # Internally, the pipeline consists of 4 steps: acquiring data from the DB,
  # filtering it using the given filters, sorting by the given criterion, and
  # displaying it on the treeview. Each of those operations is performed by
  # a dedicated function. Those functions are arranged in a call chain - each
  # one does its work and then calls the next. So there is no need to perform
  # the complete update everything when just one little thing (e.g. sorting)
  # has changed - the update can be triggered only from this specific point.
  def totalUpdate(self):
    # acquire from database to an internal state
    self.o_items = self.database.getItems()
    self.items = self.o_items
    self.filtMachine.populateChoices(self.o_items)
    # The first update is the first moment where all of the Filters have been
    # placed for sure. This is the time when a resetAll button can be placed.
    if not self.isResetAllButtonPlaced:
      self.__placeResetAllButton()
      self.isResetAllButtonPlaced = True
    self.filtersUpdate()
  def filtersUpdate(self):
    filtering = self.filtMachine.getFiltering()
    self.items = list(filter(filtering, self.o_items))
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
    # update statistics
    self.stats.update(self.items)

  # Interface
  def detailClick(self, event=None):
    # if a treeview item was double-clicked - spawn the detail view window
    if event is None:
      return
    click_region = self.tree.identify_region(event.x, event.y)
    if click_region == 'cell':
      item_row = self.tree.identify_row(event.y)
      item_dct = self.tree.item(item_row)
      item_ID = item_dct['values'][0]
      item_obj = self.database.getItemByID(item_ID)
      if item_obj is not None:
        self.detailWindow.launchPreview(item_obj)
  def sortingClick(self, event=None):
    if event is None:
      return
    # if a treeview heading was clicked - update the sorting
    click_region = self.tree.identify_region(event.x, event.y)
    if click_region != 'heading':
      return
    column_id = self.tree.identify_column(event.x)
    self.sortMachine.update(column_id)
    self.sortingUpdate()
