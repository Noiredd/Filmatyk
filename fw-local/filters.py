import tkinter as tk

class FilterMachine(object):
  # Holds multiple filters and returns a callable that can be simply passed to a
  # "filter" function on the set of Items that the Presenter holds. The machine
  # remembers all filters, so when either of them triggers an update, the whole
  # callable is updated, and Presenter's filtersUpdate() is executed.

  def __init__(self, callback):
    self.filterObjs = []
    self.filterFuns = []
    self.filterMap = {} # maps filter ID's to their positions on the lists
    self.callback = callback # to notify the Presenter about any changes
  def registerFilter(self, filter_object:object):
    self.filterObjs.append(filter_object)
    self.filterFuns.append(filter_object.getFunction())
    self.filterMap[filter_object.getID()] = len(self.filterObjs) - 1
  def updateCallback(self, filter_id:int, new_function):
    filter_pos = self.filterMap[filter_id]
    self.filterFuns[filter_pos] = new_function
    self.callback()
  def getFiltering(self):
    # returns a callable that executes all of the filters
    funs = self.filterFuns if len(self.filterFuns) > 0 else [lambda x: True]
    return lambda item: all([fun(item) for fun in funs])

class Filter(object):
  # Filters return callables that, executed on Items, return a boolean value
  # informing that a given Item passes or does not pass some criteria. These
  # criteria are internal to the filter objects, and can be modified by user.
  # A filter object has to be registered with the Presenter and instantiated in
  # its GUI (the object controls its own widgets). It takes a look into the DB
  # to collect all possible values to populate its widgets (e.g. all directors).
  # When the user manipulates the filter's widgets, the object calls Presenter
  # via the supplied callback, returning the updated callable the the Presenter
  # can now use to filter its data.
  # A derived filter has to:
  #   have a buildUI function to draw the interface (using self.main as root!)
  #   define self.function
  #   ensure that whenever the parameters change, notifyMachine is called

  # filters have IDs so that machines can recognize them on callbacks
  NEXT_ID = 0
  @classmethod
  def __getNewID(cls):
    id = cls.NEXT_ID
    cls.NEXT_ID += 1
    return id
  # by default any filter is inactive and everything shall pass it
  @staticmethod
  def DEFAULT(x):
    return True

  def __init__(self, root, machineCallback):
    # automatically assign the next free ID
    self.ID = self.__getNewID()
    # construct the GUI aspect
    self.main = tk.Frame(root)
    self.buildUI()
    # callback takes 2 args: an ID (int) and a function (callable)
    self.machineCallback = machineCallback
    # end result of a filter: a callable
    self.function = self.DEFAULT
  def buildUI(self):
    # user-defined code for UI construction
    pass
  # execute this every time the user modifies filter settings
  def notifyMachine(self):
    self.machineCallback(self.ID, self.function)
  # execute this when the filter was reset
  def reset(self):
    self.function = self.DEFAULT
    self.notifyMachine()
  def getID(self):
    return self.ID
  def getFunction(self):
    return self.function

  # TK interface for GUI placement
  def pack(self, **kw):
    self.main.pack(**kw)
  def grid(self, **kw):
    self.main.grid(**kw)

class YearFilter(Filter):
  def __init__(self, root, callback):
    self.year_from = tk.StringVar()
    self.year_to   = tk.StringVar()
    super(YearFilter, self).__init__(root, callback)
  def _reset(self):
    self.year_from.set('')
    self.year_to.set('')
    self.reset()
  def buildUI(self):
    m = self.main
    tk.Label(m, text='Rok produkcji:').grid(row=0, column=0, columnspan=5, sticky=tk.NW)
    tk.Label(m, text='Od:').grid(row=1, column=0, sticky=tk.NW)
    tk.Label(m, text='Do:').grid(row=1, column=2, sticky=tk.NW)
    yFrom = tk.Entry(m, width=5, textvariable=self.year_from)
    yFrom.bind('<KeyRelease>', self._update)
    yFrom.grid(row=1, column=1, sticky=tk.NW)
    yTo = tk.Entry(m, width=5, textvariable=self.year_to)
    yTo.bind('<KeyRelease>', self._update)
    yTo.grid(row=1, column=3, sticky=tk.NW)
    tk.Button(m, text='Reset', command=self._reset).grid(row=1, column=4, sticky=tk.NW)
  def _update(self, event):
    try:
      yearFrom = int(self.year_from.get())
    except ValueError:
      yearFrom = 0
    try:
      yearTo = int(self.year_to.get())
    except ValueError:
      yearTo = 9999
    # CONSIDER: if years were stored in the DB as ints...
    def yearFilter(item):
      year = int(item.properties['year'])
      if year >= yearFrom and year <= yearTo:
        return True
      else:
        return False
    self.function = yearFilter
    self.notifyMachine()
