import datetime
import tkinter as tk
from tkinter import ttk

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
  def resetAllFilters(self):
    for filter in self.filterObjs:
      filter.reset()
  def updateCallback(self, filter_id:int, new_function):
    filter_pos = self.filterMap[filter_id]
    self.filterFuns[filter_pos] = new_function
    self.callback()
  def populateChoices(self, items:list):
    for filter in self.filterObjs:
      filter.populateChoices(items)
      filter.reset()
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
    id = Filter.NEXT_ID
    Filter.NEXT_ID += 1
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
    # derived-class-defined code for UI construction
    pass
  def populateChoices(self, items):
    # derived-class-defined code for updating internal filter data from items
    pass
  # execute this every time the user modifies filter settings
  def notifyMachine(self):
    self.machineCallback(self.ID, self.function)
  # execute this when the filter was reset
  def reset(self):
    self._reset()
  def _reset(self):
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
    self.all_years = [0, 9999]
    super(YearFilter, self).__init__(root, callback)
  def reset(self):
    self.year_from.set(str(self.all_years[0]))
    self.year_to.set(str(self.all_years[-1]))
    self._reset()
  def buildUI(self):
    m = self.main
    tk.Label(m, text='Rok produkcji:').grid(row=0, column=0, columnspan=5, sticky=tk.NW)
    tk.Label(m, text='Od:').grid(row=1, column=0, sticky=tk.NW)
    tk.Label(m, text='Do:').grid(row=1, column=2, sticky=tk.NW)
    self.yFrom = yFrom = tk.Spinbox(m, width=5, textvariable=self.year_from, command=self._update)
    yFrom.bind('<KeyRelease>', self._update)
    yFrom.grid(row=1, column=1, sticky=tk.NW)
    self.yTo = yTo = tk.Spinbox(m, width=5, textvariable=self.year_to, command=self._update)
    yTo.bind('<KeyRelease>', self._update)
    yTo.grid(row=1, column=3, sticky=tk.NW)
    tk.Button(m, text='Reset', command=self.reset).grid(row=1, column=4, sticky=tk.NW)
  def populateChoices(self, items:list):
    all_years = set()
    for item in items:
      year = item.getRawProperty('year')
      if not year:
        continue
      all_years.add(year)
    self.all_years = sorted(list(all_years))
    if len(self.all_years) == 0:
      self.all_years = [0, 9999]
    self.yFrom.configure(values=self.all_years)
    self.yTo.configure(values=self.all_years)
    self.reset()
  def _update(self, event=None):
    try:
      yearFrom = int(self.year_from.get())
    except ValueError:
      yearFrom = int(self.all_years[0])
    try:
      yearTo = int(self.year_to.get())
    except ValueError:
      yearTo = int(self.all_years[-1])
    # reject nonsensical input (e.g. if user types "199", about to hit "5")
    if yearFrom > 2999:
      yearFrom = int(self.all_years[0])
    if yearTo < 1000:
      yearTo = int(self.all_years[-1])
    # CONSIDER: if years were stored in the DB as ints...
    def yearFilter(item):
      year = int(item.getRawProperty('year'))
      if year >= yearFrom and year <= yearTo:
        return True
      else:
        return False
    self.function = yearFilter
    self.notifyMachine()

class ListboxFilter(Filter):
  PROPERTY = '' #derived classes must override this
  def __init__(self, root, callback):
    self.all_options = []
    super(ListboxFilter, self).__init__(root, callback)
  def makeListbox(self, where, selectmode, **grid_args):
    frame = tk.Frame(where)
    # exportselection is necessary, otherwise multiple Listboxes break each other
    self.box = tk.Listbox(frame, height=10, selectmode=selectmode, exportselection=0)
    self.box.bind('<1>', self.waitAndUpdate)
    self.box.pack(side=tk.LEFT)
    scroll = ttk.Scrollbar(frame, command=self.box.yview)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    self.box.configure(yscrollcommand=scroll.set)
    frame.grid(**grid_args)
  def populateChoices(self, items:list):
    all_options = set()
    for item in items:
      for value in item.getRawProperty(self.PROPERTY):
        all_options.add(value)
    self.all_options = sorted(list(all_options))
    self.box.delete(0, tk.END)
    for option in self.all_options:
      self.box.insert(tk.END, option)
  def waitAndUpdate(self, e=None):
    # without after(), the callback executes *before* GUI has updated selection
    self.main.after(50, self._update)
  def getSelection(self):
    return [self.all_options[i] for i in self.box.curselection()]
  def _reset(self):
    self.box.selection_clear(0, tk.END)
    Filter._reset(self)

class GenreFilter(ListboxFilter):
  PROPERTY = 'genres'
  def __init__(self, root, callback):
    self.mode = tk.IntVar()
    self.selected = []
    self.filterMap = {
      0: self.filterAtLeast,
      1: self.filterAll,
      2: self.filterExactly
    }
    super(GenreFilter, self).__init__(root, callback)
  def reset(self):
    self.mode.set(0)
    self.selected = []
    self._reset()
  def buildUI(self):
    m = self.main
    tk.Label(m, text='Gatunek:').grid(row=0, column=0, sticky=tk.NW)
    self.makeListbox(m, tk.EXTENDED, row=1, column=0)
    radios = tk.Frame(m)
    radios.grid(row=2, column=0, sticky=tk.NW)
    tk.Radiobutton(radios, text='przynajmniej', variable=self.mode, value=0,
      command=self._update).pack(anchor=tk.W)
    tk.Radiobutton(radios, text='wszystkie', variable=self.mode, value=1,
      command=self._update).pack(anchor=tk.W)
    tk.Radiobutton(radios, text='dokładnie', variable=self.mode, value=2,
      command=self._update).pack(anchor=tk.W)
    tk.Button(m, text='Reset', command=self.reset).grid(row=2, column=0, sticky=tk.SE)
  def _update(self, event=None):
    self.selected = self.getSelection()
    if len(self.selected) == 0:
      self.function = Filter.DEFAULT
    else:
      self.function = self.filterMap[self.mode.get()]
    self.notifyMachine()
  def filterAtLeast(self, item):
    for genre in self.selected:
      if genre in item.getRawProperty('genres'):
        return True
    return False
  def filterAll(self, item):
    for genre in self.selected:
      if genre not in item.getRawProperty('genres'):
        return False
    return True
  def filterExactly(self, item):
    if len(self.selected) == len(item.getRawProperty('genres')):
      return self.filterAll(item)
    return False

class CountryFilter(ListboxFilter):
  PROPERTY = 'countries'
  def __init__(self, root, callback):
    self.selected = []
    super(CountryFilter, self).__init__(root, callback)
  def reset(self):
    self.selected = []
    self._reset()
  def buildUI(self):
    m = self.main
    tk.Label(m, text='Kraj produkcji:').grid(row=0, column=0, sticky=tk.NW)
    self.makeListbox(m, tk.SINGLE, row=1, column=0)
    tk.Button(m, text='Reset', command=self.reset).grid(row=2, column=0, sticky=tk.SE)
  def _update(self, event=None):
    self.selected = self.getSelection()
    if len(self.selected) == 0:
      self.function = Filter.DEFAULT
    else:
      self.function = self.filterBelongs
    self.notifyMachine()
  def filterBelongs(self, item):
    for country in item.getRawProperty('countries'):
      if country in self.selected:
        return True
    return False

class DirectorFilter(ListboxFilter):
  PROPERTY = 'directors'
  def __init__(self, root, callback):
    self.selected = []
    super(DirectorFilter, self).__init__(root, callback)
  def reset(self):
    self.selected = []
    self._reset()
  def buildUI(self):
    m = self.main
    tk.Label(m, text='Reżyser:').grid(row=0, column=0, sticky=tk.NW)
    self.makeListbox(m, tk.SINGLE, row=1, column=0)
    tk.Button(m, text='Reset', command=self.reset).grid(row=2, column=0, sticky=tk.SE)
  def _update(self, event=None):
    self.selected = self.getSelection()
    if len(self.selected) == 0:
      self.function = Filter.DEFAULT
    else:
      self.function = self.filterBelongs
    self.notifyMachine()
  def filterBelongs(self, item):
    for director in item.getRawProperty('directors'):
      if director in self.selected:
        return True
    return False

class RatingFilter(Filter):
  def __init__(self, root, callback):
    self.rate_from = tk.StringVar()
    self.rate_to = tk.StringVar()
    super(RatingFilter, self).__init__(root, callback)
  def reset(self):
    self.rate_from.set('-')
    self.rate_to.set('10')
    self._reset()
  def buildUI(self):
    m = self.main
    tk.Label(m, text='Moja ocena:').grid(row=0, column=0, columnspan=5, sticky=tk.NW)
    tk.Label(m, text='Od:').grid(row=1, column=0, sticky=tk.NW)
    tk.Label(m, text='Do:').grid(row=1, column=2, sticky=tk.NW)
    values = ['-'] + [str(i) for i in range(1,11)]
    rFrom = tk.Spinbox(m, width=4, textvariable=self.rate_from, command=self._update, values=values)
    rFrom.bind('<KeyRelease>', self._update)
    rFrom.grid(row=1, column=1, sticky=tk.NW)
    rTo = tk.Spinbox(m, width=4, textvariable=self.rate_to, command=self._update, values=values)
    rTo.bind('<KeyRelease>', self._update)
    rTo.grid(row=1, column=3, sticky=tk.NW)
    tk.Button(m, text='Reset', command=self.reset).grid(row=1, column=4, sticky=tk.NE)
  def _update(self, event=None):
    try:
      rateFrom = int(self.rate_from.get())
    except ValueError:
      rateFrom = 0
    try:
      rateTo = int(self.rate_to.get())
    except ValueError:
      rateTo = 10
    def ratingFilter(item):
      rating = int(item.getRawProperty('rating'))
      if rating >= rateFrom and rating <= rateTo:
        return True
      else:
        return False
    self.function = ratingFilter
    self.notifyMachine()

class DateFilter(Filter):
  def __init__(self, root, callback):
    self.from_year = tk.StringVar()
    self.from_month = tk.StringVar()
    self.from_day = tk.StringVar()
    self.to_year = tk.StringVar()
    self.to_month = tk.StringVar()
    self.to_day = tk.StringVar()
    self.all_years = [0, 9999]
    super(DateFilter, self).__init__(root, callback)
  def reset(self):
    self.from_year.set(self.all_years[0])
    self.from_month.set(1)
    self.from_day.set(1)
    today = datetime.datetime.now()
    self.to_year.set(today.year)
    self.to_month.set(today.month)
    self.to_day.set(today.day)
    self._reset()
  def buildUI(self):
    m = self.main
    tk.Label(m, text='Data ocenienia:').grid(row=0, column=0, columnspan=4, sticky=tk.NW)
    tk.Label(m, text='Od:').grid(row=1, column=0, sticky=tk.NW)
    tk.Label(m, text='Do:').grid(row=2, column=0, sticky=tk.NW)
    self.fySpin = fySpin = tk.Spinbox(m, width=7, textvariable=self.from_year, command=self._update)
    fySpin.bind('<KeyRelease>', self._update)
    fySpin.grid(row=1, column=1, sticky=tk.NW)
    self.tySpin = tySpin = tk.Spinbox(m, width=7, textvariable=self.to_year, command=self._update)
    tySpin.bind('<KeyRelease>', self._update)
    tySpin.grid(row=2, column=1, sticky=tk.NW)
    months = [i+1 for i in range(12)]
    mfSpin = tk.Spinbox(m, width=4, textvariable=self.from_month, command=self._update, values=months)
    mfSpin.bind('<KeyRelease>', self._update)
    mfSpin.grid(row=1, column=2, sticky=tk.NW)
    mtSpin = tk.Spinbox(m, width=4, textvariable=self.to_month, command=self._update, values=months)
    mtSpin.bind('<KeyRelease>', self._update)
    mtSpin.grid(row=2, column=2, sticky=tk.NW)
    days = [i+1 for i in range(31)]
    dfSpin = tk.Spinbox(m, width=4, textvariable=self.from_day, command=self._update, values=days)
    dfSpin.bind('<KeyRelease>', self._update)
    dfSpin.grid(row=1, column=3, sticky=tk.NW)
    dtSpin = tk.Spinbox(m, width=4, textvariable=self.to_day, command=self._update, values=days)
    dtSpin.bind('<KeyRelease>', self._update)
    dtSpin.grid(row=2, column=3, sticky=tk.NW)
    tk.Button(m, text='Reset', command=self.reset).grid(row=3, column=0, columnspan=4, sticky=tk.NE)
  def populateChoices(self, items:list):
    all_years = set()
    for item in items:
      item_date = item.getRawProperty('dateOf')
      if not item_date:
        continue
      all_years.add(item_date.year)
    self.all_years = sorted(list(all_years))
    if len(self.all_years) == 0:
      self.all_years = [0, 9999]
    self.fySpin.configure(values=self.all_years)
    self.tySpin.configure(values=self.all_years)
    self.reset()
  def getIntValue(self, var, default:int=1):
    val = var.get()
    try:
      val = int(val)
    except ValueError:
      val = default
    return val
  def _update(self, event=None):
    dateFrom = datetime.date(
      year=self.getIntValue(self.from_year),
      month=self.getIntValue(self.from_month),
      day=self.getIntValue(self.from_day)
    )
    dateTo = datetime.date(
      year=self.getIntValue(self.to_year, default=9999),
      month=self.getIntValue(self.to_month),
      day=self.getIntValue(self.to_day)
    )
    def dateFilter(item):
      date = item.getRawProperty('dateOf')
      if date >= dateFrom and date <= dateTo:
        return True
      else:
        return False
    self.function = dateFilter
    self.notifyMachine()
