import datetime
import os

import tkinter as tk
from tkinter import ttk

import filters
from database import Database
from filmweb import FilmwebAPI
from presenter import Presenter

VERSION = '1.0-alpha.12'

class Login(object):
  # By default a dormant window that offers a request function to be called by
  # the API. That function blocks until user enters data and clicks to log in.
  # It then calls API again to do the actual backend login stuff.
  default_message = 'Zaloguj się do filmweb.pl'
  logerr_message = 'Niepowodzenie logowania!'
  conerr_message = 'Sprawdź połączenie z internetem!'

  def __init__(self, root):
    self.__construct()
    self.session = None
    self.username = ''
    self.root = root
    self.window.resizable(False, False)
    self.window.attributes("-topmost", True)
    self.window.title('Zaloguj się')
    self.isDone = tk.BooleanVar()
    self.isDone.set(False)
    self.stateGood = True

  #PUBLIC
  def requestLogin(self, username:str=''):
    #bring up the window and block until user completes
    self.window.deiconify()
    self.window.grab_set()
    self.centerWindow()
    #if the username was given by caller, prevent user from changing it
    self.username = username
    if username:
      #because there is no set() method :|
      self.usernameEntry.delete(0, 1000)
      self.usernameEntry.insert(0, username)
      self.usernameEntry.config(state=tk.DISABLED)
      self.passwordEntry.focus_set()
    else:
      self.usernameEntry.config(state=tk.NORMAL)
      self.usernameEntry.focus_set()
    self.root.wait_variable(self.isDone)
    _ses = self.session
    self.session = None
    self.isDone.set(False)
    self.window.grab_release()
    #return both the acquired session as well as the (perhaps acquired) username
    return _ses, self.username

  #CONSTRUCTION
  def __construct(self):
    self.window = cw = tk.Toplevel()
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
  def centerWindow(self):
    self.window.update()
    ws = self.window.winfo_screenwidth()
    hs = self.window.winfo_screenheight()
    w = self.window.winfo_width()
    h = self.window.winfo_height()
    x = ws/2 - w/2
    y = hs/2 - h/2
    self.window.geometry('+{:.0f}+{:.0f}'.format(x, y))

  #CALLBACKS
  def _setStateBad(self, event=None, connection=False):
    message = self.conerr_message if connection else self.logerr_message
    self.infoLabel['text'] = message
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
    success, session = FilmwebAPI.login(username, password)
    if not success:
      # in this case, "session" is actually a connection error flag
      self._setStateBad(connection=session)
    else:
      #clear&hide, store session/username and pass control back to the caller
      self.usernameEntry.delete(0, tk.END)
      self.session = session
      self.username = username
      self.isDone.set(True)
      self.window.withdraw()
  def _cancelClick(self):
    self.passwordEntry.delete(0, tk.END)
    self.usernameEntry.delete(0, tk.END)
    self.session = None
    self.isDone.set(True)
    self.window.withdraw()

class Main(object):
  filename = 'userdata.fws' # TODO: maybe use user's local folder?

  def __init__(self):
    self.root = root = tk.Tk()
    root.title('FW local')
    # construct the window: first the notebook for tabbed view
    self.notebook = ttk.Notebook(root)
    self.notebook.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NW)
    # then the control panel
    frame = tk.Frame(root)
    frame.grid(row=1, column=0, padx=5, pady=5, sticky=tk.SW)
    ttk.Button(frame, text='Aktualizuj', command=self._updateData).grid(row=0, column=0, sticky=tk.SW)
    ttk.Button(frame, text='PRZEŁADUJ!', command=self._reloadData).grid(row=0, column=1, sticky=tk.SW)
    self.progressVar = tk.IntVar()
    self.progressbar = ttk.Progressbar(root, orient='horizontal', length=400, mode='determinate', variable=self.progressVar)
    self.progressbar.grid(row=1, column=0, padx=5, pady=5)
    self._setProgress(-1) # start with the progress bar hidden
    ttk.Button(root, text='Wyjście', command=self._quit).grid(row=1, column=0, padx=5, pady=5, sticky=tk.SE)
    # construct the login window manager and prepare to load data
    self.loginHandler = Login(self.root)
    self.databases = []
    self.presenters = []
    # load the savefile
    userdata = self.loadUserData()
    u_name = userdata['username'] if userdata else ''
    conf_m = userdata['movies_cfg'] if userdata else ''
    data_m = userdata['movies_db'] if userdata else ''
    conf_s = userdata['series_cfg'] if userdata else ''
    data_s = userdata['series_db'] if userdata else ''
    conf_g = userdata['games_cfg'] if userdata else ''
    data_g = userdata['games_db'] if userdata else ''
    # instantiate Presenters and Databases
    self.api = FilmwebAPI(self.loginHandler.requestLogin, u_name)
    movieDatabase = Database.restoreFromString('Movie', data_m, self.api, self._setProgress)
    self.databases.append(movieDatabase)
    moviePresenter = Presenter(self, self.api, movieDatabase, conf_m)
    moviePresenter.addFilter(filters.YearFilter, row=0, column=0, sticky=tk.NW)
    moviePresenter.addFilter(filters.RatingFilter, row=1, column=0, sticky=tk.NW)
    moviePresenter.addFilter(filters.DateFilter, row=2, column=0, sticky=tk.NW)
    moviePresenter.addFilter(filters.GenreFilter, row=0, column=1, rowspan=3, sticky=tk.NW)
    moviePresenter.addFilter(filters.CountryFilter, row=0, column=2, rowspan=3, sticky=tk.NW)
    moviePresenter.addFilter(filters.DirectorFilter, row=0, column=3, rowspan=3, sticky=tk.NW)
    moviePresenter.placeInTab('Filmy')
    moviePresenter.totalUpdate()
    self.presenters.append(moviePresenter)
    seriesDatabase = Database.restoreFromString('Series', data_s, self.api, self._setProgress)
    self.databases.append(seriesDatabase)
    seriesPresenter = Presenter(self, self.api, seriesDatabase, conf_s)
    seriesPresenter.addFilter(filters.YearFilter, row=0, column=0, sticky=tk.NW)
    seriesPresenter.addFilter(filters.RatingFilter, row=1, column=0, sticky=tk.NW)
    seriesPresenter.addFilter(filters.DateFilter, row=2, column=0, sticky=tk.NW)
    seriesPresenter.addFilter(filters.GenreFilter, row=0, column=1, rowspan=3, sticky=tk.NW)
    seriesPresenter.addFilter(filters.CountryFilter, row=0, column=2, rowspan=3, sticky=tk.NW)
    seriesPresenter.addFilter(filters.DirectorFilter, row=0, column=3, rowspan=3, sticky=tk.NW)
    seriesPresenter.placeInTab('Seriale')
    seriesPresenter.totalUpdate()
    self.presenters.append(seriesPresenter)
    gameDatabase = Database.restoreFromString('Game', data_g, self.api, self._setProgress)
    self.databases.append(gameDatabase)
    gamePresenter = Presenter(self, self.api, gameDatabase, conf_g)
    gamePresenter.addFilter(filters.YearFilter, row=0, column=0, sticky=tk.NW)
    gamePresenter.addFilter(filters.RatingFilter, row=1, column=0, sticky=tk.NW)
    gamePresenter.addFilter(filters.DateFilter, row=2, column=0, sticky=tk.NW)
    gamePresenter.addFilter(filters.GenreFilter, row=0, column=1, rowspan=3, sticky=tk.NW)
    gamePresenter.placeInTab('Gry')
    gamePresenter.totalUpdate()
    self.presenters.append(gamePresenter)
    #center window AFTER creating everything (including plot)
    self.centerWindow()
    #ensure a controlled exit no matter what user does (X-button, alt+f4)
    root.protocol('WM_DELETE_WINDOW', self._quit)
    if not userdata:
      self._reloadData() # first run
    #prevent resizing and run the app
    root.resizable(False, False)
    tk.mainloop()

  def centerWindow(self):
    self.root.update()
    ws = self.root.winfo_screenwidth()
    hs = self.root.winfo_screenheight()
    w = self.root.winfo_width()
    h = self.root.winfo_height()
    x = ws/2 - w/2
    y = hs/2 - h/2
    self.root.geometry('+{:.0f}+{:.0f}'.format(x, y))

  #USER DATA MANAGEMENT
  def loadUserData(self):
    # loads data and returns it as an externally-understandable dict
    if not os.path.exists(self.filename):
      return None
    with open(self.filename, 'r') as userfile:
      userdata = [line.strip('\n') for line in userfile.readlines() if not line.startswith('#')]
    # TODO: backwards compatibility; for now just reject legacy savefiles and reqcuire all data
    if userdata[0] != VERSION:
      return None
    # labels for each line
    keys = ['version', 'username', 'movies_cfg', 'movies_db', 'series_cfg', 'series_db', 'games_cfg', 'games_db']
    data = {key: value for key, value in zip(keys, userdata)}
    return data
  def saveUserData(self):
    # if for any reason the first update hasn't commenced - don't save anything
    if self.api.username is None:
      return
    # if there is no need to save anything - stop right there too
    if not (
        any([db.isDirty for db in self.databases]) or
        any([ps.isDirty for ps in self.presenters])):
      return
    # safety feature against failing to write new data and removing the old
    if os.path.exists(self.filename):
      os.rename(self.filename, self.filename + '.bak')
    with open(self.filename, 'w') as userfile:
      userfile.write('#VERSION\n')
      userfile.write(VERSION + '\n')
      userfile.write('#USERNAME\n')
      userfile.write(self.api.username + '\n')
      userfile.write('#MOVIES\n')
      userfile.write(self.presenters[0].storeToString() + '\n')
      userfile.write(self.databases[0].storeToString() + '\n')
      userfile.write('#SERIES\n')
      userfile.write(self.presenters[1].storeToString() + '\n')
      userfile.write(self.databases[1].storeToString() + '\n')
      userfile.write('#GAMES\n')
      userfile.write(self.presenters[2].storeToString() + '\n')
      userfile.write(self.databases[2].storeToString() + '\n')
      # games can be added sequentially right after
    # if there were no errors at point, new data has been successfully written
    if os.path.exists(self.filename + '.bak'):
      os.remove(self.filename + '.bak')
    # notify the objects that they were saved - maybe could be a method for this
    for db in self.databases:
      db.isDirty = False
    for ps in self.presenters:
      ps.isDirty = False

  #CALLBACKS
  def _setProgress(self, value:int):
    # allows the caller to set the percentage value of the progress bar
    # non-negative values cause the bar to show up, negative hides it
    if value < 0:
      self.progressbar.grid_remove()
      self.progressVar.set(0)
    else:
      self.progressbar.grid()
      self.progressVar.set(value)
    self.root.update()
  def _updateData(self):
    # call softUpdate on all the databases
    for db in self.databases:
      db.softUpdate()
    # update all the presenters
    for ps in self.presenters:
      ps.totalUpdate()
    # save data
    self.saveUserData()
  def _reloadData(self):
    for db in self.databases:
      db.hardUpdate()
    for ps in self.presenters:
      ps.totalUpdate()
    self.saveUserData()
  def _quit(self):
    self.saveUserData()
    self.root.quit()

Main()
