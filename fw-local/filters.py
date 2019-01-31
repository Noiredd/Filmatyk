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
    # flags for performance improvement: construct a callable only from those
    # filters that are currently active; only reset those too; additionally,
    # ignore repeated resets (speeds up startup SIGNIFICANTLY)
    self.filterFlags = []
    self.filterMap = {} # maps filter ID's to their positions on the lists
    self.callback = callback # to notify the Presenter about any changes
    self.ignoreCallback = False # see resetAllFilters for the meaning of it
  def registerFilter(self, filter_object:object):
    filter_object.setCallback(self.updateCallback)
    self.filterObjs.append(filter_object)
    self.filterFuns.append(filter_object.getFunction())
    self.filterFlags.append(False)
    self.filterMap[filter_object.getID()] = len(self.filterObjs) - 1
  def resetAllFilters(self):
    # disable calling back to the Presenter until all of the work is done
    self.ignoreCallback = True
    for filter, flag in zip(self.filterObjs, self.filterFlags):
      if flag:
        filter.reset()
    self.filterFlags = [False for flag in self.filterFlags] # clear all
    # and now call back
    self.ignoreCallback = False
    self.callback()
  def updateCallback(self, filter_id:int, new_function, reset=False):
    filter_pos = self.filterMap[filter_id]
    self.filterFuns[filter_pos] = new_function
    # don't call back if the filter is dormant and has requested a reset
    if reset and not self.filterFlags[filter_pos]:
      return
    # otherwise, proceed; set the flag on update, clear on reset
    self.filterFlags[filter_pos] = not reset
    if not self.ignoreCallback:
      self.callback()
  def populateChoices(self, items:list):
    for filter in self.filterObjs:
      filter.populateChoices(items)
    self.resetAllFilters()
  def getFiltering(self):
    # returns a callable that executes all of the filters
    funs = [fun for fun, flag in zip(self.filterFuns, self.filterFlags) if flag]
    if not funs:
      funs = [lambda x: True]
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

  def __init__(self, root):
    # automatically assign the next free ID
    self.ID = self.__getNewID()
    # construct the GUI aspect
    self.main = tk.Frame(root)
    self.buildUI()
    # callback takes 2 pos args: an ID (int) and a function (callable)
    # and 1 keyword arg: "reset"
    self.machineCallback = lambda x: x # machine sets that during registering
    # end result of a filter: a callable
    self.function = self.DEFAULT
  def setCallback(self, callback):
    self.machineCallback = callback
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
    self.machineCallback(self.ID, self.function, reset=True)
  def getID(self):
    return self.ID
  def getFunction(self):
    return self.function

  # TK interface for GUI placement
  def pack(self, **kw):
    self.main.pack(**kw)
  def grid(self, **kw):
    self.main.grid(**kw)

class TitleFilter(Filter):
  def __init__(self, root):
    self.title_in = tk.StringVar()
    self.function = self.filterTitle
    super(TitleFilter, self).__init__(root)
  def reset(self):
    self.title_in.set('')
    self._reset()
  def buildUI(self):
    self.nameEntry = tk.Entry(master=self.main, width=100, textvariable=self.title_in)
    self.nameEntry.grid(row=0, column=0)
    self.nameEntry.bind('<Key>', self._enterKey)
    ttk.Button(master=self.main, text='X', width=3, command=self.reset).grid(row=0, column=1)
  def _enterKey(self, event=None):
    # Clear the entry when user hits escape
    if event:
      if event.keysym == 'Escape':
        self.reset()
    # Wait before updating (see ListboxFilter.waitAndUpdate)
    self.main.after(50, self._update)
  def _update(self, event=None):
    search_string = self.title_in.get().lower()
    def filterTitle(item):
      title = item.getRawProperty('title')
      return search_string in title.lower()
    self.function = filterTitle
    self.notifyMachine()
  def filterTitle(self, item):
    title = item.getRawProperty('title')
    return self.title_val in title.lower()

class YearFilter(Filter):
  default_years = [1, 9999]
  def __init__(self, root):
    self.year_from = tk.StringVar()
    self.year_to   = tk.StringVar()
    self.all_years = self.default_years
    super(YearFilter, self).__init__(root)
  def reset(self):
    self.year_from.set(str(self.all_years[0]))
    self.year_to.set(str(self.all_years[-1]))
    self._reset()
  def buildUI(self):
    m = self.main
    tk.Label(m, text='Rok produkcji:').grid(row=0, column=0, columnspan=5, sticky=tk.NW)
    tk.Label(m, text='Od:').grid(row=1, column=0, sticky=tk.NW)
    tk.Label(m, text='Do:').grid(row=1, column=2, sticky=tk.NW)
    self.yFrom = yFrom = tk.Spinbox(m, width=5, textvariable=self.year_from, command=self._updateFrom)
    yFrom.bind('<KeyRelease>', self._updateFrom)
    yFrom.grid(row=1, column=1, sticky=tk.NW)
    self.yTo = yTo = tk.Spinbox(m, width=5, textvariable=self.year_to, command=self._updateTo)
    yTo.bind('<KeyRelease>', self._updateTo)
    yTo.grid(row=1, column=3, sticky=tk.NW)
    ttk.Button(m, text='Reset', width=5, command=self.reset).grid(row=1, column=4, sticky=tk.NW)
  def populateChoices(self, items:list):
    all_years = set()
    for item in items:
      year = item.getRawProperty('year')
      if not year:
        continue
      all_years.add(year)
    self.all_years = sorted(list(all_years))
    if len(self.all_years) == 0:
      self.all_years = self.default_years
    self.yFrom.configure(values=self.all_years)
    self.yTo.configure(values=self.all_years)
    self.reset()
  def _updateTo(self, event=None):
    self._update(to=True, event=event)
  def _updateFrom(self, event=None):
    self._update(to=False, event=event)
  def _update(self, to, event=None):
    try:
      yearFrom = int(self.year_from.get())
    except ValueError:
      yearFrom = self.all_years[0]
    try:
      yearTo = int(self.year_to.get())
    except ValueError:
      yearTo = self.all_years[-1]
    # reject nonsensical input (e.g. if user types "199", about to hit "5")
    if yearFrom > 2999:
      yearFrom = self.all_years[0]
    if yearTo < 1000:
      yearTo = self.all_years[-1]
    # automatically align the opposite limit if the combination is nonsensical
    if yearFrom > yearTo:
      if to: # yearTo was modified -- pull yearFrom down with it
        yearFrom = yearTo
        self.year_from.set(str(yearFrom))
      else: # yearFrom was modified -- pull yearTo up with it
        yearTo = yearFrom
        self.year_to.set(str(yearTo))
    def yearFilter(item):
      year = item.getRawProperty('year')
      if year >= yearFrom and year <= yearTo:
        return True
      else:
        return False
    self.function = yearFilter
    self.notifyMachine()

class ListboxFilter(Filter):
  PROPERTY = '' #derived classes must override this
  def __init__(self, root):
    self.all_options = []
    super(ListboxFilter, self).__init__(root)
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
      if isinstance(self.PROPERTY, list):
        for prop in self.PROPERTY:
          for value in item.getRawProperty(prop):
            all_options.add(value)
      else:
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
  def __init__(self, root):
    self.mode = tk.IntVar()
    self.selected = []
    self.filterMap = {
      0: self.filterAtLeast,
      1: self.filterAll,
      2: self.filterExactly
    }
    super(GenreFilter, self).__init__(root)
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
    ttk.Button(m, text='Reset', width=5, command=self.reset).grid(row=2, column=0, sticky=tk.SE)
  def _update(self, event=None):
    self.selected = self.getSelection()
    if len(self.selected) == 0:
      self.function = Filter.DEFAULT
    else:
      self.function = self.filterMap[self.mode.get()]
    self.notifyMachine()
  def filterAtLeast(self, item):
    for genre in self.selected:
      if genre in item.getRawProperty(self.PROPERTY):
        return True
    return False
  def filterAll(self, item):
    for genre in self.selected:
      if genre not in item.getRawProperty(self.PROPERTY):
        return False
    return True
  def filterExactly(self, item):
    if len(self.selected) == len(item.getRawProperty(self.PROPERTY)):
      return self.filterAll(item)
    return False

class CountryFilter(ListboxFilter):
  PROPERTY = 'countries'
  def __init__(self, root):
    self.selected = []
    super(CountryFilter, self).__init__(root)
  def reset(self):
    self.selected = []
    self._reset()
  def buildUI(self):
    m = self.main
    tk.Label(m, text='Kraj produkcji:').grid(row=0, column=0, sticky=tk.NW)
    self.makeListbox(m, tk.SINGLE, row=1, column=0)
    ttk.Button(m, text='Reset', width=5, command=self.reset).grid(row=2, column=0, sticky=tk.SE)
  def _update(self, event=None):
    self.selected = self.getSelection()
    if len(self.selected) == 0:
      self.function = Filter.DEFAULT
    else:
      self.function = self.filterBelongs
    self.notifyMachine()
  def filterBelongs(self, item):
    for country in item.getRawProperty(self.PROPERTY):
      if country in self.selected:
        return True
    return False

class DirectorFilter(ListboxFilter):
  PROPERTY = 'directors'
  def __init__(self, root):
    self.selected = []
    super(DirectorFilter, self).__init__(root)
  def reset(self):
    self.selected = []
    self._reset()
  def buildUI(self):
    m = self.main
    tk.Label(m, text='Reżyser:').grid(row=0, column=0, sticky=tk.NW)
    self.makeListbox(m, tk.SINGLE, row=1, column=0)
    ttk.Button(m, text='Reset', width=5, command=self.reset).grid(row=2, column=0, sticky=tk.SE)
  def _update(self, event=None):
    self.selected = self.getSelection()
    if len(self.selected) == 0:
      self.function = Filter.DEFAULT
    else:
      self.function = self.filterBelongs
    self.notifyMachine()
  def filterBelongs(self, item):
    for director in item.getRawProperty(self.PROPERTY):
      if director in self.selected:
        return True
    return False

class PlatformFilter(ListboxFilter):
  PROPERTY = 'platforms'
  def __init__(self, root):
    self.selected = []
    super(PlatformFilter, self).__init__(root)
  def reset(self):
    self.selected = []
    self._reset()
  def buildUI(self):
    m = self.main
    tk.Label(m, text='Platforma:').grid(row=0, column=0, sticky=tk.NW)
    self.makeListbox(m, tk.SINGLE, row=1, column=0)
    ttk.Button(m, text='Reset', width=5, command=self.reset).grid(row=2, column=0, sticky=tk.SE)
  def _update(self, event=None):
    self.selected = self.getSelection()
    if len(self.selected) == 0:
      self.function = Filter.DEFAULT
    else:
      self.function = self.filterBelongs
    self.notifyMachine()
  def filterBelongs(self, item):
    for maker in item.getRawProperty(self.PROPERTY):
      if maker in self.selected:
        return True

class GamemakerFilter(ListboxFilter):
  PROPERTY = ['developers', 'producers']
  def __init__(self, root):
    self.selected = []
    super(GamemakerFilter, self).__init__(root)
  def reset(self):
    self.selected = []
    self._reset()
  def buildUI(self):
    m = self.main
    tk.Label(m, text='Twórca:').grid(row=0, column=0, sticky=tk.NW)
    self.makeListbox(m, tk.SINGLE, row=1, column=0)
    ttk.Button(m, text='Reset', width=5, command=self.reset).grid(row=2, column=0, sticky=tk.SE)
  def _update(self, event=None):
    self.selected = self.getSelection()
    if len(self.selected) == 0:
      self.function = Filter.DEFAULT
    else:
      self.function = self.filterBelongs
    self.notifyMachine()
  def filterBelongs(self, item):
    makers = []
    for prop in self.PROPERTY:
      for maker in item.getRawProperty(prop):
        makers.append(maker)
    for maker in makers:
      if maker in self.selected:
        return True
    return False

class RatingFilter(Filter):
  def __init__(self, root):
    self.rate_from = tk.StringVar()
    self.rate_to = tk.StringVar()
    super(RatingFilter, self).__init__(root)
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
    rFrom = tk.Spinbox(m, width=5, textvariable=self.rate_from, command=self._updateFrom, values=values)
    rFrom.bind('<KeyRelease>', self._updateFrom)
    rFrom.grid(row=1, column=1, sticky=tk.NW)
    rTo = tk.Spinbox(m, width=5, textvariable=self.rate_to, command=self._updateTo, values=values)
    rTo.bind('<KeyRelease>', self._updateTo)
    rTo.grid(row=1, column=3, sticky=tk.NW)
    ttk.Button(m, text='Reset', width=5, command=self.reset).grid(row=1, column=4, sticky=tk.NE)
  def _updateTo(self, event=None):
    self._update(to=True, event=event)
  def _updateFrom(self, event=None):
    self._update(to=False, event=event)
  def _update(self, to, event=None):
    try:
      rateFrom = int(self.rate_from.get())
    except ValueError:
      rateFrom = 0
    try:
      rateTo = int(self.rate_to.get())
    except ValueError:
      rateTo = 10
    # similar mechanism as in YearFilter
    if rateFrom > rateTo:
      if to:
        rateFrom = rateTo
        self.rate_from.set(str(rateFrom))
      else:
        rateTo = rateFrom
        self.rate_to.set(str(rateTo))
    def ratingFilter(item):
      rating = item.getRawProperty('rating')
      if rating >= rateFrom and rating <= rateTo:
        return True
      else:
        return False
    self.function = ratingFilter
    self.notifyMachine()

class DateFilter(Filter):
  default_years = [1, 9999]
  def __init__(self, root):
    self.from_year = tk.StringVar()
    self.from_month = tk.StringVar()
    self.from_day = tk.StringVar()
    self.to_year = tk.StringVar()
    self.to_month = tk.StringVar()
    self.to_day = tk.StringVar()
    self.all_years = self.default_years
    super(DateFilter, self).__init__(root)
  def reset(self):
    dayzero = datetime.date(
      year=self.all_years[0],
      month=1,
      day=1
    )
    self._setDates(dateFrom=dayzero, dateTo=datetime.date.today())
    self._reset()
  def buildUI(self):
    m = self.main
    tk.Label(m, text='Data ocenienia:').grid(row=0, column=0, columnspan=4, sticky=tk.NW)
    tk.Label(m, text='Od:').grid(row=1, column=0, sticky=tk.NW)
    tk.Label(m, text='Do:').grid(row=2, column=0, sticky=tk.NW)
    self.fySpin = fySpin = tk.Spinbox(m, width=5, textvariable=self.from_year, command=self._updateFrom)
    fySpin.bind('<KeyRelease>', self._updateFrom)
    fySpin.grid(row=1, column=1, sticky=tk.NW)
    self.tySpin = tySpin = tk.Spinbox(m, width=5, textvariable=self.to_year, command=self._updateTo)
    tySpin.bind('<KeyRelease>', self._updateTo)
    tySpin.grid(row=2, column=1, sticky=tk.NW)
    months = [i+1 for i in range(12)]
    fmSpin = tk.Spinbox(m, width=3, textvariable=self.from_month, command=self._updateFrom, values=months)
    fmSpin.bind('<KeyRelease>', self._updateFrom)
    fmSpin.grid(row=1, column=2, sticky=tk.NW)
    tmSpin = tk.Spinbox(m, width=3, textvariable=self.to_month, command=self._updateTo, values=months)
    tmSpin.bind('<KeyRelease>', self._updateTo)
    tmSpin.grid(row=2, column=2, sticky=tk.NW)
    days = [i+1 for i in range(31)]
    fdSpin = tk.Spinbox(m, width=3, textvariable=self.from_day, command=self._updateFrom, values=days)
    fdSpin.bind('<KeyRelease>', self._updateFrom)
    fdSpin.grid(row=1, column=3, sticky=tk.NW)
    tdSpin = tk.Spinbox(m, width=3, textvariable=self.to_day, command=self._updateTo, values=days)
    tdSpin.bind('<KeyRelease>', self._updateTo)
    tdSpin.grid(row=2, column=3, sticky=tk.NW)
    ttk.Button(m, text='Reset', width=5, command=self.reset).grid(row=1, column=4, rowspan=2, sticky=tk.E)
    # shortcut buttons
    sc = tk.Frame(m)
    tk.Frame(sc, height=10).grid(row=0, column=0) # separator
    tk.Label(sc, text='Ostatni:').grid(row=1, column=0, sticky=tk.W)
    ttk.Button(sc, text='rok', width=4, command=self._thisYear).grid(row=1, column=1)
    ttk.Button(sc, text='msc', width=4, command=self._thisMonth).grid(row=1, column=2)
    ttk.Button(sc, text='tdzn', width=4, command=self._thisWeek).grid(row=1, column=3)
    tk.Label(sc, text='Poprzedni:').grid(row=2, column=0, sticky=tk.W)
    ttk.Button(sc, text='rok', width=4, command=self._lastYear).grid(row=2, column=1)
    ttk.Button(sc, text='msc', width=4, command=self._lastMonth).grid(row=2, column=2)
    ttk.Button(sc, text='tdzn', width=4, command=self._lastWeek).grid(row=2, column=3)
    sc.grid(row=3, column=0, columnspan=5, sticky=tk.NW)
  def populateChoices(self, items:list):
    all_years = set()
    for item in items:
      item_date = item.getRawProperty('dateOf')
      if not item_date:
        continue
      all_years.add(item_date.year)
    self.all_years = sorted(list(all_years))
    if len(self.all_years) == 0:
      self.all_years = self.default_years
    self.fySpin.configure(values=self.all_years)
    self.tySpin.configure(values=self.all_years)
    self.reset()
  @staticmethod
  def getIntValue(var, default:int=1):
    val = var.get()
    try:
      val = int(val)
    except ValueError:
      val = default
    return val
  def _thisYear(self):
    dateTo = datetime.date.today()
    delta = datetime.timedelta(days=365)
    dateFrom = dateTo - delta
    self._setDates(dateFrom=dateFrom, dateTo=dateTo)
    self._makeUpdate(dateFrom, dateTo)
  def _thisMonth(self):
    dateTo = datetime.date.today()
    delta = datetime.timedelta(days=31)
    dateFrom = dateTo - delta
    self._setDates(dateFrom=dateFrom, dateTo=dateTo)
    self._makeUpdate(dateFrom, dateTo)
  def _thisWeek(self):
    dateTo = datetime.date.today()
    delta = datetime.timedelta(days=7)
    dateFrom = dateTo - delta
    self._setDates(dateFrom=dateFrom, dateTo=dateTo)
    self._makeUpdate(dateFrom, dateTo)
  def _lastYear(self):
    delta = datetime.timedelta(days=365)
    dateTo = datetime.date.today() - delta
    dateFrom = dateTo - delta
    self._setDates(dateFrom=dateFrom, dateTo=dateTo)
    self._makeUpdate(dateFrom, dateTo)
  def _lastMonth(self):
    delta = datetime.timedelta(days=31)
    dateTo = datetime.date.today() - delta
    dateFrom = dateTo - delta
    self._setDates(dateFrom=dateFrom, dateTo=dateTo)
    self._makeUpdate(dateFrom, dateTo)
  def _lastWeek(self):
    delta = datetime.timedelta(days=7)
    dateTo = datetime.date.today() - delta
    dateFrom = dateTo - delta
    self._setDates(dateFrom=dateFrom, dateTo=dateTo)
    self._makeUpdate(dateFrom, dateTo)
  def _updateTo(self, event=None):
    self._update(to=True, event=event)
  def _updateFrom(self, event=None):
    self._update(to=False, event=event)
  def _setDates(self, dateFrom=None, dateTo=None):
    if dateFrom:
      self.from_year.set(str(dateFrom.year))
      self.from_month.set(str(dateFrom.month))
      self.from_day.set(str(dateFrom.day))
    if dateTo:
      self.to_year.set(str(dateTo.year))
      self.to_month.set(str(dateTo.month))
      self.to_day.set(str(dateTo.day))
  def _getDates(self):
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
    return dateFrom, dateTo
  def _update(self, to, event=None):
    dateFrom, dateTo = self._getDates()
    self._makeUpdate(dateFrom, dateTo)
  def _makeUpdate(self, dateFrom, dateTo):
    def dateFilter(item):
      date = item.getRawProperty('dateOf')
      if date >= dateFrom and date <= dateTo:
        return True
      else:
        return False
    self.function = dateFilter
    self.notifyMachine()
