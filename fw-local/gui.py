import datetime
import os

import tkinter as tk
from tkinter import ttk

from blueprint import Blueprint
import database as db
from plotting import drawHistogram
import scraper


def readConfigFile():
  config_path = '../config.txt'
  if not os.path.isfile(config_path):
    #write default config:
    with open(config_path, 'w') as cf:
      cf.write('title\n')
      cf.write('#otitle\n')
      cf.write('year\n')
      cf.write('genres\n')
      cf.write('#duration\n')
      cf.write('#countries\n')
      cf.write('directors\n')
      cf.write('#cast\n')
      cf.write('#fwRating\n')
      cf.write('timeSeen\n')
      cf.write('rating\n')
      cf.write('#favourite\n')
      cf.write('comment\n')
  with open(config_path, 'r') as cf:
    config = []
    for item in cf.readlines():
      item = item.strip('\n')
      if item.startswith('#'):
        continue
      if item not in Blueprint.keys():
        print('Unknown key: "' + item + '", check ' + config_path)
        exit()
      elif Blueprint[item]['presentation'] is None:
        print('This item cannot be printed!')
        exit()
      else:
        config.append((item, Blueprint[item]['presentation']))
    return config


class Login(object):
  #Handles the login operation, from construction of the window to scraper calls
  default_message = 'Zaloguj się do filmweb.pl'

  def __init__(self, root):
    self.constructLoginWindow()
    self.session = None
    self.root = root
    self.window.resizable(0,0)
    self.isDone = tk.BooleanVar()
    self.isDone.set(False)
    self.stateGood = True

  #PUBLIC
  def requestLogin(self, message=''):
    #bring up the window and block until user completes
    self.messageLabel['text'] = message if message!='' else self.default_message
    self.window.deiconify()
    self.usernameEntry.focus_set()
    self.root.wait_variable(self.isDone)
    _ses = self.session
    self.session = None
    self.isDone.set(False)
    return _ses

  #CONSTRUCTION
  def constructLoginWindow(self):
    self.window = cw = tk.Toplevel()
    cw.title('Zaloguj się')
    self.messageLabel = tk.Label(master=cw, text=self.default_message)
    self.messageLabel.grid(row=0, column=0, columnspan=2)
    tk.Label(master=cw, text='Nazwa użytkownika:').grid(row=1, column=0, sticky=tk.E)
    tk.Label(master=cw, text='Hasło:').grid(row=2, column=0, sticky=tk.E)
    self.usernameEntry = tk.Entry(master=cw, width=20)
    self.usernameEntry.grid(row=1, column=1, sticky=tk.W)
    self.usernameEntry.bind('<Key>', self._setStateGood)
    self.passwordEntry = tk.Entry(master=cw, width=20, show='*')
    self.passwordEntry.grid(row=2, column=1, sticky=tk.W)
    self.passwordEntry.bind('<Key>', self._setStateGood)
    self.infoLabel = tk.Label(master=cw, text='')
    self.infoLabel.grid(row=3, column=0, columnspan=2)
    tk.Button(master=cw, text='Zaloguj', command=self._loginClick).grid(row=4, column=1, sticky=tk.W)
    tk.Button(master=cw, text='Anuluj', command=self._cancelClick).grid(row=4, column=0, sticky=tk.E)
    self.window.withdraw()

  #CALLBACKS
  def _setStateBad(self, event=None):
    self.infoLabel['text'] = 'Niepowodzenie logowania!'
    self.stateGood = False
  def _setStateGood(self, event=None):
    if not self.stateGood:
      self.infoLabel['text'] = ''
      self.stateGood = True
    #also, maybe the user has hit enter key, meaning to log in
    if event.keycode == 13:
      self._loginClick()
  def _loginClick(self):
    #collect login data
    username = self.usernameEntry.get()
    password = self.passwordEntry.get()
    self.passwordEntry.delete(0, tk.END)  #always clear the password field
    #attempt to log in
    session = scraper.login(username, password)
    if session is None:
      #inform the user
      self._setStateBad()
    else:
      #clear&hide the window, store session and pass control back to the caller
      self.usernameEntry.delete(0, tk.END)
      self.session = session
      self.isDone.set(True)
      self.window.withdraw()
  def _cancelClick(self):
    self.passwordEntry.delete(0, tk.END)
    self.usernameEntry.delete(0, tk.END)
    self.session = None
    self.isDone.set(True)
    self.window.withdraw()


class Main(object):
  summary_format = 'Wyświetlono {0!s} z {1!s} filmów'
  max_width = 1000

  def __init__(self):
    self.root = root = tk.Tk()
    #prepare the components
    self.config = readConfigFile()
    self.loginHandler = Login(self.root)
    self.session = None
    self.filters = {
      'year_from':  tk.StringVar(),
      'year_to':    tk.StringVar(),
      'rating_from':tk.StringVar(),
      'rating_to':  tk.StringVar(),
      'genre':      {'mode': tk.IntVar(), 'list': []},
      'country':    '',
      'seen_from':  {'year': tk.IntVar(), 'month': tk.IntVar(), 'day': tk.IntVar()},
      'seen_to':    {'year': tk.IntVar(), 'month': tk.IntVar(), 'day': tk.IntVar()},
      'director':   ''
    }
    self.sorting = None
    #see if there already is a database, or create a new one
    if db.checkDataExists():
      self.database = db.restoreFromFile()
    else:
      self._reloadData(newDatabase = True)
    self.database.setConfig(self.config)
    #construct the window
    root.title('FW local')
    root.resizable(0,0)
    self.constructMainWindow()
    #all set - refresh and pass control to user
    self._changeSorting('timeSeen')
    self._changeSorting('timeSeen') #twice - latest first
    self._filtersUpdate()
    #center window AFTER creating everything (including plot)
    self.centerWindow()
    tk.mainloop()

  #CONSTRUCTION
  def constructMainWindow(self):
    def _constructTreeView(self):
      wrap = tk.Frame(self.root)
      self.tree = tree = ttk.Treeview(wrap,
                                      height=32,
                                      selectmode='none',
                                      columns=[c[0] for c in self.config])
      tree.column(column='#0', width=0, stretch=False)
      total_width = 0
      for item in self.config:
        total_width += item[1]['width']
        if total_width > self.max_width:
          remaining = item[1]['width'] - (total_width - self.max_width)
          tree.column(column=item[0], width=remaining, minwidth=item[1]['width'], stretch=True)
        else:
          tree.column(column=item[0], width=item[1]['width'], stretch=False)
        tree.heading(column=item[0], text=item[1]['name'], anchor=tk.W)
      tree.bind('<1>', self._sortingUpdate)
      tree.grid(row=0, column=0)
      #scrollbars
      yScroll = ttk.Scrollbar(wrap, command=tree.yview)
      yScroll.grid(row=0, column=1, sticky=tk.NS)
      xScroll = ttk.Scrollbar(wrap, command=tree.xview, orient=tk.HORIZONTAL)
      if total_width > self.max_width:
        xScroll.grid(row=1, column=0, sticky=tk.EW)
      tree.configure(yscrollcommand=yScroll.set, xscrollcommand=xScroll.set)
      wrap.grid(row=0, column=0, rowspan=4, padx=5, pady=5, sticky=tk.N)
    def _constructFilterFrame(self):
      #placeholder for the histogram and summary
      self.summ = tk.Label(self.root, text='')
      self.summ.grid(row=0, column=1, sticky=tk.N+tk.W)
      self.plot = tk.Label(self.root, text='--------------------------------------')
      self.plot.grid(row=1, column=1, sticky=tk.N)
      #outer frame holding all filters
      frame = tk.LabelFrame(self.root, text='Filtry')
      #frame for year filters
      _yearFrame = tk.Frame(frame)
      tk.Label(_yearFrame, text='Rok produkcji:').grid(row=0, column=0, columnspan=4, sticky=tk.N+tk.W)
      tk.Label(_yearFrame, text='Od:').grid(row=1, column=0, sticky=tk.W)
      tk.Label(_yearFrame, text='Do:').grid(row=1, column=2, sticky=tk.W)
      _yearFrom = tk.Entry(_yearFrame, width=5, textvariable=self.filters['year_from'])
      _yearFrom.bind('<KeyRelease>', self._filtersUpdate)
      _yearFrom.grid(row=1, column=1, sticky=tk.W)
      _yearTo = tk.Entry(_yearFrame, width=5, textvariable=self.filters['year_to'])
      _yearTo.bind('<KeyRelease>', self._filtersUpdate)
      _yearTo.grid(row=1, column=3, sticky=tk.W)
      def _resetYearFrame(update=True):
        self.filters['year_from'].set('')
        self.filters['year_to'].set('')
        if update:
          self._filtersUpdate()
      tk.Button(_yearFrame, text='Reset', command=_resetYearFrame).grid(row=2, column=0, columnspan=4, sticky=tk.E)
      _yearFrame.grid(row=1, column=0, padx=5, pady=5, sticky=tk.N+tk.W)
      #frame for rating filters
      _ratingFrame = tk.Frame(frame)
      tk.Label(_ratingFrame, text='Moja ocena:').grid(row=0, column=0, columnspan=4, sticky=tk.N+tk.W)
      tk.Label(_ratingFrame, text='Od:').grid(row=1, column=0, sticky=tk.W)
      tk.Label(_ratingFrame, text='Do:').grid(row=1, column=2, sticky=tk.W)
      _ratingFrom = tk.Entry(_ratingFrame, width=5, textvariable=self.filters['rating_from'])
      _ratingFrom.bind('<KeyRelease>', self._filtersUpdate)
      _ratingFrom.grid(row=1, column=1, sticky=tk.W)
      _ratingTo = tk.Entry(_ratingFrame, width=5, textvariable=self.filters['rating_to'])
      _ratingTo.bind('<KeyRelease>', self._filtersUpdate)
      _ratingTo.grid(row=1, column=3, sticky=tk.W)
      def _resetRatingFrame(update=True):
        self.filters['rating_from'].set('')
        self.filters['rating_to'].set('')
        if update:
          self._filtersUpdate()
      tk.Button(_ratingFrame, text='Reset', command=_resetRatingFrame).grid(row=2, column=0, columnspan=4, sticky=tk.E)
      _ratingFrame.grid(row=2, column=0, padx=5, pady=5, sticky=tk.N+tk.W)
      #frame for timeSeen filters
      _timeSeenFrame = tk.Frame(frame)
      tk.Label(_timeSeenFrame, text='Data obejrzenia:').grid(row=0, column=0, columnspan=4, sticky=tk.N+tk.W)
      tk.Label(_timeSeenFrame, text='Od:').grid(row=1, column=0, sticky=tk.N+tk.W)
      tk.Label(_timeSeenFrame, text='Do:').grid(row=2, column=0, sticky=tk.N+tk.W)
      self.timeSeenFromYear = tk.Spinbox(_timeSeenFrame, width=7, textvariable=self.filters['seen_from']['year'], command=self._filtersUpdate)
      self.timeSeenFromYear.bind('<KeyRelease>', self._filtersUpdate)
      self.timeSeenFromYear.grid(row=1, column=1, sticky=tk.N+tk.W)
      _timeSeenFromMonth = tk.Spinbox(_timeSeenFrame, width=4, textvariable=self.filters['seen_from']['month'], command=self._filtersUpdate, values=[i+1 for i in range(12)])
      _timeSeenFromMonth.bind('<KeyRelease>', self._filtersUpdate)
      _timeSeenFromMonth.grid(row=1, column=2, sticky=tk.N+tk.W)
      _timeSeenFromDay = tk.Spinbox(_timeSeenFrame, width=4, textvariable=self.filters['seen_from']['day'], command=self._filtersUpdate, values=[i+1 for i in range(31)])
      _timeSeenFromDay.bind('<KeyRelease>', self._filtersUpdate)
      _timeSeenFromDay.grid(row=1, column=3, sticky=tk.N+tk.W)
      self.timeSeenToYear = tk.Spinbox(_timeSeenFrame, width=7, textvariable=self.filters['seen_to']['year'], command=self._filtersUpdate)
      self.timeSeenToYear.bind('<KeyRelease>', self._filtersUpdate)
      self.timeSeenToYear.grid(row=2, column=1, sticky=tk.N+tk.W)
      _timeSeenToMonth = tk.Spinbox(_timeSeenFrame, width=4, textvariable=self.filters['seen_to']['month'], command=self._filtersUpdate, values=[i+1 for i in range(12)])
      _timeSeenToMonth.bind('<KeyRelease>', self._filtersUpdate)
      _timeSeenToMonth.grid(row=2, column=2, sticky=tk.N+tk.W)
      _timeSeenToDay = tk.Spinbox(_timeSeenFrame, width=4, textvariable=self.filters['seen_to']['day'], command=self._filtersUpdate, values=[i+1 for i in range(31)])
      _timeSeenToDay.bind('<KeyRelease>', self._filtersUpdate)
      _timeSeenToDay.grid(row=2, column=3, sticky=tk.N+tk.W)
      def _resetTimeSeenFrame(update=True):
        self.filters['seen_from']['year'].set(self.yearsSeen[0])
        self.filters['seen_from']['month'].set(1)
        self.filters['seen_from']['day'].set(1)
        today = datetime.datetime.now()
        self.filters['seen_to']['year'].set(today.year)
        self.filters['seen_to']['month'].set(today.month)
        self.filters['seen_to']['day'].set(today.day)
        if update:
          self._filtersUpdate()
      tk.Button(_timeSeenFrame, text='Reset', command=_resetTimeSeenFrame).grid(row=3, column=0, columnspan=4, sticky=tk.N+tk.E)
      _timeSeenFrame.grid(row=3, column=0, padx=5, pady=5, sticky=tk.N+tk.W)
      self.setYearChoices()
      #frame for genre filters
      _genreFrame = tk.Frame(frame)
      tk.Label(_genreFrame, text='Gatunek:').grid(row=0, column=0, columnspan=2, sticky=tk.N+tk.W)
      _genreWrap = tk.Frame(_genreFrame)
      self.genreBox = _genreBox = tk.Listbox(_genreWrap, height=10, selectmode=tk.EXTENDED, exportselection=0)  #multiple listboxes with exportselection mutually block each other
      _genreBox.bind('<1>', lambda e: self.root.after(50, self._filtersUpdate)) #ugly but necessary - need to wait till GUI updates selection
      _genreScroll = ttk.Scrollbar(_genreWrap, command=_genreBox.yview)
      _genreScroll.pack(side=tk.RIGHT, fill=tk.Y)
      _genreBox.configure(yscrollcommand=_genreScroll.set)
      _genreBox.pack(side=tk.LEFT)
      _genreWrap.grid(row=1, column=0, rowspan=1, columnspan=2, sticky=tk.N+tk.E)
      _radioWrap = tk.Frame(_genreFrame)
      tk.Radiobutton(_radioWrap, text='przynajmniej', variable=self.filters['genre']['mode'], value=0, command=self._filtersUpdate).pack(anchor=tk.W)
      tk.Radiobutton(_radioWrap, text='wszystkie', variable=self.filters['genre']['mode'], value=1, command=self._filtersUpdate).pack(anchor=tk.W)
      tk.Radiobutton(_radioWrap, text='dokładnie', variable=self.filters['genre']['mode'], value=2, command=self._filtersUpdate).pack(anchor=tk.W)
      _radioWrap.grid(row=2, column=0, sticky=tk.S+tk.W)
      def _resetGenreFrame(update=True):
        self.filters['genre']['mode'].set(0)
        self.filters['genre']['list'] = []
        self.genreBox.selection_clear(0, tk.END)
        if update:
          self._filtersUpdate()
      tk.Button(_genreFrame, text='Reset', command=_resetGenreFrame).grid(row=2, column=1, sticky=tk.N+tk.E)
      _genreFrame.grid(row=1, column=1, rowspan=4, padx=5, pady=5, sticky=tk.N+tk.W)
      self.setGenreChoices()
      #frame for country filters
      _countryFrame = tk.Frame(frame)
      tk.Label(_countryFrame, text='Kraj produkcji:').grid(row=0, column=0, sticky=tk.N+tk.W)
      _countryWrap = tk.Frame(_countryFrame)
      self.countryBox =_countryBox = tk.Listbox(_countryWrap, height=10, selectmode=tk.SINGLE, exportselection=0)
      _countryBox.bind('<1>', lambda e: self.root.after(50, self._filtersUpdate))
      _countryScroll = ttk.Scrollbar(_countryWrap, command=_countryBox.yview)
      _countryScroll.pack(side=tk.RIGHT, fill=tk.Y)
      _countryBox.configure(yscrollcommand=_countryScroll.set)
      _countryBox.pack(side=tk.LEFT)
      _countryWrap.grid(row=1, column=0, sticky=tk.N+tk.E)
      def _resetCountryFrame(update=True):
        self.filters['country'] = ''
        self.countryBox.selection_clear(0, tk.END)
        if update:
          self._filtersUpdate()
      tk.Button(_countryFrame, text='Reset', command=_resetCountryFrame).grid(row=2, column=0, sticky=tk.N+tk.E)
      _countryFrame.grid(row=1, column=2, rowspan=4, padx=5, pady=5, sticky=tk.N+tk.W)
      self.setCountryChoices()
      #frame for director filters
      _directorFrame = tk.Frame(frame)
      tk.Label(_directorFrame, text='Reżyser:').grid(row=0, column=0, sticky=tk.N+tk.W)
      _directorWrap = tk.Frame(_directorFrame)
      self.directorBox = _directorBox = tk.Listbox(_directorWrap, height=10, selectmode=tk.SINGLE, exportselection=0)
      _directorBox.bind('<1>', lambda e: self.root.after(50, self._filtersUpdate))
      _directorScroll = ttk.Scrollbar(_directorWrap, command=_directorBox.yview)
      _directorScroll.pack(side=tk.RIGHT, fill=tk.Y)
      _directorBox.configure(yscrollcommand=_directorScroll.set)
      _directorBox.pack(side=tk.LEFT)
      _directorWrap.grid(row=1, column=0, sticky=tk.N+tk.W)
      def _resetDirectorFrame(update=True):
        self.filters['director'] = ''
        self.directorBox.selection_clear(0, tk.END)
        if update:
          self._filtersUpdate()
      tk.Button(_directorFrame, text='Reset', command=_resetDirectorFrame).grid(row=2, column=0, sticky=tk.N+tk.E)
      _directorFrame.grid(row=1, column=3, rowspan=4, padx=5, pady=5, sticky=tk.N+tk.W)
      self.setDirectorChoices()
      #reset all filters
      def _resetAllFrames():
        _resetYearFrame(False)
        _resetRatingFrame(False)
        _resetTimeSeenFrame(False)
        _resetGenreFrame(False)
        _resetCountryFrame(False)
        _resetDirectorFrame(False)
        self._filtersUpdate()
      tk.Button(frame, text='Resetuj wszystkie', command=_resetAllFrames).grid(row=3, column=3, padx=5, pady=5, sticky=tk.S+tk.E)
      #instantiate the outer frame
      frame.grid(row=2, column=1, padx=5, pady=5, sticky=tk.N+tk.W)
    def _constructControlPanel(self):
      frame = tk.Frame(self.root)
      tk.Button(frame, text='Aktualizuj', command=self._updateData).grid(row=0, column=0, sticky=tk.S+tk.W)
      tk.Button(frame, text='PRZEŁADUJ!', command=self._reloadData).grid(row=0, column=1, sticky=tk.S+tk.W)
      frame.grid(row=3, column=1, padx=5, pady=5, sticky=tk.S+tk.W)
      tk.Button(self.root, text='Wyjście', command=self._quit).grid(row=3, column=1, padx=5, pady=5, sticky=tk.S+tk.E)
    _constructTreeView(self)
    _constructFilterFrame(self)
    _constructControlPanel(self)
  def centerWindow(self):
    self.root.update()
    ws = self.root.winfo_screenwidth()
    hs = self.root.winfo_screenheight()
    w = self.root.winfo_width()
    h = self.root.winfo_height()
    x = ws/2 - w/2
    y = hs/2 - h/2
    self.root.geometry('%dx%d+%d+%d' % (w, h, x, y))
  def setGenreChoices(self):
    self.genres = self.database.getListOfAll('genres')
    self.genreBox.delete(0, tk.END)
    if len(self.genres)>0:
      for genre in self.genres:
        self.genreBox.insert(tk.END, genre)
  def setCountryChoices(self):
    self.countries = self.database.getListOfAll('countries')
    self.countryBox.delete(0, tk.END)
    if len(self.countries)>0:
      for country in self.countries:
        self.countryBox.insert(tk.END, country)
  def setDirectorChoices(self):
    self.directors = self.database.getListOfAll('directors')
    self.directorBox.delete(0, tk.END)
    if len(self.directors)>0:
      for director in self.directors:
        self.directorBox.insert(tk.END, director)
  def setYearChoices(self):
    self.yearsSeen = self.database.getYearsSeen()
    self.timeSeenFromYear.configure(values=self.yearsSeen)
    self.timeSeenToYear.configure(values=self.yearsSeen)
    today = datetime.datetime.now()
    self.filters['seen_to']['year'].set(today.year)
    self.filters['seen_to']['month'].set(today.month)
    self.filters['seen_to']['day'].set(today.day)

  #INTERNALS
  def _changeSorting(self, column):
    ASC_CHAR = '▲ '
    DSC_CHAR = '▼ '
    #when ran for the first time, current sorting will be None
    if self.sorting == None:
      #we simply set the sorting and alter the column heading
      self.sorting = {'key': column, 'descending': False}
      new_heading = ASC_CHAR + Blueprint[column]['presentation']['name']
      self.tree.heading(column=column, text=new_heading)
    else:
      #otherwise, there are two cases: when the same column was clicked, and when another
      if column == self.sorting['key']:
        #if the same column - toggle the sorting direction and change the heading
        if self.sorting['descending']:
          self.sorting['descending'] = False
          new_heading = ASC_CHAR + Blueprint[column]['presentation']['name']
        else:
          self.sorting['descending'] = True
          new_heading = DSC_CHAR + Blueprint[column]['presentation']['name']
        self.tree.heading(column=column, text=new_heading)
      else:
        #if a different column - clear the heading of the old column and proceed
        #as if it was the first time anything was clicked
        restored_column_name = self.sorting['key']
        restored_heading = Blueprint[restored_column_name]['presentation']['name']
        self.tree.heading(column=restored_column_name, text=restored_heading)
        self.sorting = None
        self._changeSorting(column)

  #CALLBACKS
  def _filtersUpdate(self, event=None):
    #year filters update automatically, but genres have to be collected manually
    self.filters['genre']['list'] = [self.genres[i] for i in self.genreBox.curselection()]
    #similar with countries and directors, but for now we only allow selecting one
    selected_country = self.countryBox.curselection()
    if len(selected_country)>0:
      self.filters['country'] = self.countries[selected_country[0]]
    else:
      self.filters['country'] = ''
    selected_director = self.directorBox.curselection()
    if len(selected_director)>0:
      self.filters['director'] = self.directors[selected_director[0]]
    else:
      self.filters['director'] = ''
    self.database.filterMovies(self.filters)
    self._sortingUpdate()
  def _sortingUpdate(self, event=None):
    #if the method was called by the Treeview - change in sorting was requested
    if event is not None:
      region = self.tree.identify('region', event.x, event.y)
      if region=='heading':
        column_num = self.tree.identify_column(event.x)
        column_name = self.tree.column(column=column_num, option='id')
        self._changeSorting(column_name)
    #otherwise, this was called by _filtersUpdate as a part of refresh operation
    #in such case we just need to sort the newly filtered data in the same way
    self.database.sortMovies(self.sorting)
    self._displayUpdate()
  def _displayUpdate(self):
    #clear the tree
    for item in self.tree.get_children():
      self.tree.delete(item)
    #fill with new values
    movies, histogram = self.database.returnMovies()
    for movie in movies:
      self.tree.insert(parent='', index=0, text='', values=movie)
    #update the histogram
    self.histogram = drawHistogram(histogram)
    self.plot.config(image=self.histogram)
    #update the summary
    shown = len(self.database.filtered)
    total = len(self.database.movies)
    self.summ['text'] = self.summary_format.format(shown, total)
  def _updateData(self):
    if self.session is None:
      self.session = self.loginHandler.requestLogin()
    if self.session is not None:
      self.database.softUpdate(self.session)
    #refresh data used in the GUI
    self.setYearChoices()
    self.setGenreChoices()
    self.setCountryChoices()
    self.setDirectorChoices()
    self._filtersUpdate() #triggers a full refresh
  def _reloadData(self, newDatabase=False):
    self.session = self.loginHandler.requestLogin(message='Zaloguj się by zaimportować oceny' if newDatabase else '')
    if self.session is None:
      return
    if newDatabase:
      self.database = db.Database(self.session.username)
    self.database.hardUpdate(self.session)
    #refresh data used in the GUI
    self.setYearChoices()
    self.setGenreChoices()
    self.setCountryChoices()
    self.setDirectorChoices()
    self._filtersUpdate() #triggers a full refresh
  def _quit(self):
    #saves data and exits
    self.root.quit()

Main()
