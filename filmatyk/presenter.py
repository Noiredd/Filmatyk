from collections import OrderedDict
import json
import tkinter as tk
from tkinter import ttk

import containers
from defaults import DEFAULT_CONFIGS, DEFAULT_SORTING
from detailviews import DetailWindow
from filters import FilterMachine, TitleFilter
from statview import StatView

class Config(object):
  # Stores the current treeview configuration, handling serialization and
  # deserialization, as well as config changes. Presenter owns one and queries
  # it when displaying items.

  def __init__(self, itemtype:str, columns:OrderedDict, parent:object):
    self.parent = parent
    self.rawConfig = columns
    self.itemtype = itemtype
    itemclass = containers.classByString[itemtype]
    self.allColumns = [name for name, bp in itemclass.blueprints.items() if name != 'id']
    self.columnHeaders = {name: bp.getHeading() for name, bp in itemclass.blueprints.items()}
    self.columnWidths = {name: bp.getColWidth() for name, bp in itemclass.blueprints.items()}
    self.makeColumns()
    self.__construct()
    self.window.protocol('WM_DELETE_WINDOW', self._confirmClick) # always accept changes
    self.window.attributes("-topmost", True)
  # GUI aspect
  def setDirtyBit(fun):
    # this is meant to be a decorator, not a method!
    # will cause any decorated function to set a dirty flag in the parent Presenter
    # see: filmweb.py > FilmwebAPI.enforceSession for explanation
    def wrapper(*args, **kwargs):
      self = args[0]
      self.parent.isDirty = True
      self.isDirty = True
      return fun(*args, **kwargs)
    return wrapper
  def __construct(self):
    self.window = cw = tk.Toplevel()
    self.window.resizable(False, False)
    self.window.title('Konfiguracja kolumn')
    columns = ['id', 'name', 'width']
    self.activeCols = ttk.Treeview(cw, height=10, selectmode='browse', columns=columns)
    self.activeCols['displaycolumns'] = columns[1:]
    self.activeCols.column(column='#0', width=0, stretch=False)
    self.activeCols.column(column='name', width=150, stretch=False)
    self.activeCols.column(column='width', width=55, stretch=False)
    self.activeCols.heading(column='name', text='Nazwa', anchor=tk.W)
    self.activeCols.heading(column='width', text='Rozmiar', anchor=tk.W)
    self.activeCols.grid(row=0, column=0, rowspan=3)
    self.activeCols.bind('<Button-1>', self._unselectAvailable)
    self.availableCols = ttk.Treeview(cw, height=10, selectmode='browse', columns=columns)
    self.availableCols['displaycolumns'] = columns[1:]
    self.availableCols.column(column='#0', width=0, stretch=False)
    self.availableCols.column(column='name', width=150, stretch=False)
    self.availableCols.column(column='width', width=55, stretch=False)
    self.availableCols.heading(column='name', text='Nazwa', anchor=tk.W)
    self.availableCols.heading(column='width', text='Rozmiar', anchor=tk.W)
    self.availableCols.grid(row=0, column=2, rowspan=3)
    self.availableCols.bind('<Button-1>', self._unselectActive)
    enablers = tk.Frame(cw)
    enablers.grid(row=0, column=1, pady=20, sticky=tk.N)
    ttk.Button(enablers, text='←', width=2, command=self._moveToActive).grid(row=0, column=0)
    ttk.Button(enablers, text='→', width=2, command=self._moveToAvailable).grid(row=0, column=1)
    order = tk.Frame(cw)
    order.grid(row=1, column=1)
    ttk.Button(order, text='↑', width=2, command=self._moveUp).grid(row=0, column=0)
    ttk.Button(order, text='↓', width=2, command=self._moveDown).grid(row=1, column=0)
    ctrl = tk.Frame(cw)
    ctrl.grid(row=2, column=1, sticky=tk.S)
    ttk.Button(ctrl, text='Domyślne', command=self._resetDefaults).grid(row=0, column=0)
    ttk.Button(ctrl, text='OK', command=self._confirmClick).grid(row=1, column=0)
    self.window.withdraw()
  def _unselectActive(self, event=None):
    row = self.activeCols.focus()
    self.activeCols.selection_remove(row)
  def _unselectAvailable(self, event=None):
    row = self.availableCols.focus()
    self.availableCols.selection_remove(row)
  @setDirtyBit
  def _moveToActive(self, event=None):
    # if one of the available columns was selected - move it to the active ones
    row = self.availableCols.focus()
    if row == '':
      return
    item = self.availableCols.item(row)
    values = item['values']
    self.activeCols.insert(parent='', index=tk.END, text='', values=values)
    self.availableCols.delete(row)
    # also, alter the actual internal dicts
    name = values[0]
    self.rawConfig[name] = None # reminder: rawConfig value is column width, None == default
    self.makeColumns()
  @setDirtyBit
  def _moveToAvailable(self, event=None):
    # if one of the active columns was selected - remove it and restore it among availables
    row = self.activeCols.focus()
    if row == '':
      return
    item = self.activeCols.item(row)
    self.activeCols.delete(row)
    name = item['values'][0]
    values = [name, self.columnHeaders[name], self.columnWidths[name]]
    self.availableCols.insert(parent='', index=tk.END, text='', values=values)
    # backend
    self.rawConfig.pop(name)
    self.makeColumns()
  @setDirtyBit
  def _moveUp(self, event=None):
    # change order - only for the active columns
    row = self.activeCols.focus()
    if row == '':
      return
    index = self.activeCols.index(row)
    self.activeCols.move(row, parent='', index=index-1)
    # backend
    item = self.activeCols.item(row)
    name = item['values'][0]
    self.moveKeyUp(self.rawConfig, name)
    self.makeColumns()
  @setDirtyBit
  def _moveDown(self, event=None):
    # change order - only for the active columns
    row = self.activeCols.focus()
    if row == '':
      return
    index = self.activeCols.index(row)
    self.activeCols.move(row, parent='', index=index+1)
    # backend
    item = self.activeCols.item(row)
    name = item['values'][0]
    self.moveKeyDown(self.rawConfig, name)
    self.makeColumns()
  @setDirtyBit
  def _resetDefaults(self, event=None):
    # restore default settings
    self.rawConfig = DEFAULT_CONFIGS[self.itemtype].copy()
    self.makeColumns()
    # regenerate the window
    self.fillTrees()
  def _confirmClick(self, event=None):
    # hide window and release focus
    self.window.withdraw()
    self.window.grab_release()
    # if changes were made - update the parent and change its window properties
    # so that it can resize along with the treeview
    if self.isDirty:
      self.parent.root.root.resizable(True, True)
      self.parent.configureColumns()
      self.parent.root.root.update()
      self.parent.root.root.resizable(False, False)
      self.parent.root.root.wm_attributes('-topmost', 0)
    # refresh items
    self.parent.displayUpdate()
  def centerWindow(self):
    self.window.update()
    ws = self.window.winfo_screenwidth()
    hs = self.window.winfo_screenheight()
    w = self.window.winfo_width()
    h = self.window.winfo_height()
    x = ws/2 - w/2
    y = hs/2 - h/2
    self.window.geometry('+{:.0f}+{:.0f}'.format(x, y))
  def popUp(self):
    self.isDirty = False # until some change has been made
    self.fillTrees()
    # steal focus
    self.window.grab_set()
    self.window.deiconify()
    self.centerWindow()
  def fillTrees(self):
    # clear the views and fill with the most up-to-date data
    for item in self.activeCols.get_children():
      self.activeCols.delete(item)
    for key, width in self.columns.items():
      values = [key, self.columnHeaders[key], width]
      self.activeCols.insert(parent='', index=tk.END, text='', values=values)
    for item in self.availableCols.get_children():
      self.availableCols.delete(item)
    for item in self.allColumns:
      if item in self.columns.keys():
        continue
      values = [item, self.columnHeaders[item], self.columnWidths[item]]
      self.availableCols.insert(parent='', index=tk.END, text='', values=values)
  # backend
  def makeColumns(self):
    # turn rawConfig into presentable columns
    self.columns = OrderedDict()
    for name in self.rawConfig.keys():
      default_width = self.columnWidths[name]
      config_width = self.rawConfig[name]
      set_width = config_width if config_width is not None else default_width
      self.columns[name] = set_width
  @staticmethod
  def moveKeyUp(dct:OrderedDict, key):
    # moves the 'key' up one position by moving the key before it and all others to the end
    keys = list(dct.keys())
    index = keys.index(key)
    if index == 0:
      return
    dct.move_to_end(key)
    del keys[index] # don't move the original one again
    for key in keys[index-1:]:
      dct.move_to_end(key)
  @staticmethod
  def moveKeyDown(dct:OrderedDict, key):
    # moves the 'key' down one position by moving that and then subsequent keys to the end
    keys = list(dct.keys())
    index = keys.index(key)
    last = len(keys) - 1
    if index < last:
      # if this wasn't already the last key - move it to the end
      dct.move_to_end(key)
      if index <= last-2:
        # if there are more than one keys behind it - leave that one and move the rest
        for key in keys[index+2:]:
          dct.move_to_end(key)
  # getters
  def getAllColumns(self):
    return self.allColumns
  def getColumns(self):
    return list(self.columns.keys())
  def getWidth(self, column):
    return self.columns[column]
  def getHeading(self, column):
    return self.columnHeaders[column]
  # setters
  @setDirtyBit
  def manualResize(self, column):
    # the user has manually resized some column - store this change
    oldWidth = self.getWidth(column)
    newWidth = self.parent.tree.column(column=column, option='width') # a bit hacky
    if oldWidth == newWidth:
      # restore a "None" value in config and default width in current setting
      self.rawConfig[column] = None
      self.columns[column] = self.columnWidths[column] # faster than makeColumns just for that
    else:
      self.rawConfig[column] = newWidth
      self.columns[column] = newWidth
  @setDirtyBit
  def manualDefault(self, column):
    # the user has requested this column to return to the default setting
    self.rawConfig[column] = None
    defWidth = self.columnWidths[column]
    self.columns[column] = defWidth
    self.parent.tree.column(column=column, width=defWidth)
  @staticmethod
  def restoreFromString(itemtype:str, string:str, parent:object):
    # The config string is a JSON dump of a dict that contains columns to be
    # presented as keys, and their widths as values (or None for defaults).
    if string == '':
      config = DEFAULT_CONFIGS[itemtype]
    else:
      config = json.loads(string, object_pairs_hook=OrderedDict) # preserve order
    return Config(itemtype, config, parent)
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
    if default_key not in self.columns:
      return
    self.update(default_key)
    self.ascending = default_asc
  def update(self, column_id:str):
    # retrieve the column's original heading
    column_heading = self.tree.heading(column=column_id, option='text')
    # first run
    if not self.current_id:
      self.current_id = column_id
      self.original_heading = column_heading
      self.setMarker()
      self.sorting = dict(key=self.makeLambda(column_id), reverse=self.ascending)
      return self.sorting
    # on every other run, check whether the same column was clicked again
    elif column_id == self.current_id:
      # only switch the order in this case
      self.ascending = not self.ascending
      self.setMarker()
      self.sorting['reverse'] = self.ascending
      return self.sorting
    # otherwise, a different column was clicked
    else:
      # in this case, restore the original column's heading
      self.tree.heading(column=self.current_id, text=self.original_heading)
      self.current_id = column_id
      self.original_heading = column_heading
      self.ascending = False
      self.setMarker()
      self.sorting = dict(key=self.makeLambda(column_id), reverse=self.ascending)
      return self.sorting
  def setMarker(self):
    # prefixes the currently selected column's heading with a marker indicating sort direction
    char = self.ASC_CHAR if self.ascending else self.DSC_CHAR
    self.tree.heading(column=self.current_id, text=char + self.original_heading)
  def getSorting(self):
    return self.sorting

class Presenter(object):
  """ TODO MAJOR
      1. Presenter has a switch whether to display ratings or want-tos
  """
  def __init__(self, root, api, database, config:str, displayRating=True):
    self.root = root
    self.main = ttk.Frame(root.notebook)
    self.database = database
    self.items = []
    self.config = Config.restoreFromString(database.itemtype, config, self)
    self.__construct()
    self.sortMachine = SortingMachine(self.tree, self.config.getColumns(), self.database.itemtype)
    self.filtMachine = FilterMachine(self.filtersUpdate)
    self.detailWindow = DetailWindow.getDetailWindow()
    self.__placeTitleFilter()
    self.isDirty = False
  def __construct(self):
    """ LEFT SIDE """
    self.left = tk.Frame(self.main)
    # TREEVIEW
    self.tree = tree = ttk.Treeview(
      self.left,
      height=28,
      selectmode=tk.BROWSE,
      columns=['id'] + self.config.getAllColumns()
    )
    self.configureColumns()
    tree.column(column='#0', width=0, minwidth=0, stretch=False)
    tree.grid(row=1, column=0, sticky=tk.NW)
    yScroll = ttk.Scrollbar(self.left, command=tree.yview)
    yScroll.grid(row=1, column=1, sticky=tk.NS)
    tree.configure(yscrollcommand=yScroll.set)
    # POP-UP MENU
    self.menu = tk.Menu(self.left, tearoff=0)
    self.menu.add_command(label='Konfiguracja', command=self.config.popUp)
    # BIND CALLBACKS
    tree.bind('<Button-1>', self._singleClick)
    tree.bind('<Double-Button-1>', self._doubleClick)
    tree.bind('<ButtonRelease-1>', self._leftRelease)
    tree.bind('<Button-3>', self._rightClick)
    tree.bind('<FocusOut>', self.clearSelection)
    """ RIGHT SIDE """
    self.right = tk.Frame(self.main)
    # STATISTICS VIEW
    self.stats = StatView(self.right, self.database.itemtype)
    self.stats.grid(row=0, column=0, sticky=tk.N)
    # FILTER FRAME
    self.fframe = ttk.Frame(self.right)
    self.fframe.grid(row=1, column=0, sticky=tk.NW)
    # store the row and col range of inserted filters to know where to place the
    # reset all button
    self.fframe_grid = [0, 0]
    # PLACE THE FRAMES
    self.left.grid(row=0, column=0, sticky=tk.N)
    self.right.grid(row=0, column=1, sticky=tk.N)
    # delay placing the reset button to the first update,
    # after all of the filters have been added
    self.isResetAllButtonPlaced = False
  def __placeTitleFilter(self):
    # TitleFilter is special as it does not reside within the filter frame, but
    # instead is placed right above the treeview. It would be tempting to place
    # it in the window during __construct, but this is impossible. Placing this
    # filter requires a FilterMachine object, which cannot be constructed until
    # TreeView is in place. So: FM requires TV but TV is spawned in __construct
    # which in turn cannot be called after FM is in place. For these reasons, a
    # TitleFilter has to be spawned separately, after those two are ready. Sort
    # of like any other Filter.
    titleFilter = TitleFilter(self.left)
    self.filtMachine.registerFilter(titleFilter)
    titleFilter.grid(row=0, column=0, columnspan=2, pady=2, sticky=tk.EW)
  def configureColumns(self):
    for column in self.config.getColumns():
      self.tree.column(column=column, width=self.config.getWidth(column), stretch=False)
      self.tree.heading(column=column, text=self.config.getHeading(column), anchor=tk.W)
    # setting this AFTER widths and headings prevents an annoying little bug in which
    # whenever a new column was added that was narrower than the current last one, the
    # TV would get stretched as if it was as long as that last column (leaving empty space)
    self.tree['displaycolumns'] = self.config.getColumns()
    try:
      # if the columns have just been reconfigured, ask the sortMachine to reset the marker
      self.sortMachine.setMarker()
    except AttributeError:
      # this is a first run and the machine doesn't even exist - which is fine
      pass
  def __placeResetAllButton(self):
    rab_row = self.fframe_grid[0]
    rab_col = self.fframe_grid[1]
    raButton = ttk.Button(self.fframe, text='Resetuj filtry!', command=self.filtMachine.resetAllFilters)
    raButton.grid(row=rab_row, column=rab_col, rowspan=rab_row+1, columnspan=rab_col+1, sticky=tk.SE)
    self.filtMachine.resetAllFilters(force=True)

  def storeToString(self):
    return self.config.storeToString()

  def addFilter(self, filter_class, **grid_args):
    filter_object = filter_class(self.fframe)
    self.filtMachine.registerFilter(filter_object)
    filter_object.grid(**grid_args)
    # remember where was the furthest filter placed
    if grid_args['row'] > self.fframe_grid[0]:
      self.fframe_grid[0] = grid_args['row']
    if grid_args['column'] > self.fframe_grid[1]:
      self.fframe_grid[1] = grid_args['column']

  # take a spot in the entire Notebook tab of a given name
  def placeInTab(self, tab):
    self.main.grid(row=0, column=0, pady=5, padx=5)
    self.root.notebook.add(self.main, text=tab)

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
    # list all properties that the TV needs to describe an item when inserting
    all_columns = self.config.getAllColumns()
    # only some of those will actually be displayed - list them separately
    display_these = self.config.getColumns()
    # retrieve only the necessary properties of every displayed item
    for item in self.items:
      # list of values to put into the tree, always starts with the id
      values = [item['id']]
      # go through all the properties required logically by the TV (at insert)
      for col in all_columns:
        # but only actually query the item for those that will be displayed
        if col not in display_these:
          values.append('')
        else:
          values.append(item[col])
      self.tree.insert(parent='', index=0, text='', values=values)
    # update statistics
    self.stats.update(self.items)

  # Interface
  def _singleClick(self, event=None):
    if event is None:
      return
    # if a treeview heading was clicked - change the sorting
    click_region = self.tree.identify_region(event.x, event.y)
    if click_region == 'heading':
      self.changeSorting(event)
  def _doubleClick(self, event=None):
    if event is None:
      return
    # if clicked on a cell - spawn a detail view window
    # if on a column separator - restore column default width
    click_region = self.tree.identify_region(event.x, event.y)
    if click_region == 'cell':
      self.detailSpawn(event)
    elif click_region == 'separator':
      self.resetColumn(event)
  def _rightClick(self, event=None):
    if event is None:
      return
    # if right clicked on the heading - spawn the pop-up menu
    click_region = self.tree.identify_region(event.x, event.y)
    if click_region == 'heading':
      self.menu.post(event.x_root, event.y_root)
  def _leftRelease(self, event=None):
    if event is None:
      return
    # if the LMB was released over the column separator - notify config of a change
    click_region = self.tree.identify_region(event.x, event.y)
    if click_region == 'separator':
      self.resizeColumn(event)
  def detailSpawn(self, event):
    item_row = self.tree.identify_row(event.y)
    item_dct = self.tree.item(item_row)
    item_ID = item_dct['values'][0]
    item_obj = self.database.getItemByID(item_ID)
    if item_obj is not None:
      self.detailWindow.launchPreview(item_obj)
  def resetColumn(self, event):
    column_id = self.tree.identify_column(event.x)
    column_name = self.tree.column(column=column_id, option='id')
    self.config.manualDefault(column_name)
  def changeSorting(self, event):
    column_id = self.tree.identify_column(event.x)
    column_name = self.tree.column(column=column_id, option='id')
    self.sortMachine.update(column_name)
    self.sortingUpdate()
  def resizeColumn(self, event):
    column_id = self.tree.identify_column(event.x)
    column_name = self.tree.column(column=column_id, option='id')
    self.config.manualResize(column_name)
  def clearSelection(self, event=None):
    selection = self.tree.focus()
    self.tree.selection_remove(selection)
