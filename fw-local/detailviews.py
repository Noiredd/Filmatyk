import tkinter as tk
from tkinter import ttk

class Fonts(object):
  default  = 'TkDefaultFont'
  title    = (default, 24)
  otitle   = (default, 12)
  headings = (default, 10, 'bold')
  details  = (default, 10)
  plot     = (default, 11)#, 'italic')
  fwRating = (default, 24)
  rating   = (default, 48)
  faved    = (default, 40)
  comment  = (default, 14, 'italic')
  FAV_SIGN = '♥'

class DetailView(object):
  def __init__(self, root):
    self.main = tk.Frame(root, relief=tk.GROOVE, bd=1)
    self.buildUI()
  def buildUI(self):
    # what does the view contain - use the given main frame, like in Filters
    pass
  def fillInDetails(self, item:object):
    # define this to take properties from the item and put them into the widgets
    pass
  # TK interface
  def grid(self, **args):
    self.main.grid(**args)

class DetailViewMovies(DetailView):
  def __init__(self, root):
    super(DetailViewMovies, self).__init__(root)
  def buildUI(self):
    # heading panel: year|country|genre|duration
    heading = tk.Frame(self.main)
    heading.grid(row=0, column=0, sticky=tk.NW)
    self.yearLabel = tk.Label(heading, text='', width=5, anchor=tk.NW, font=Fonts.headings)
    self.yearLabel.grid(row=0, column=0, sticky=tk.NW, padx=3)
    self.countryLabel = tk.Label(heading, text='', width=25, anchor=tk.N, font=Fonts.headings)
    self.countryLabel.grid(row=0, column=1, sticky=tk.NW)
    self.genreLabel = tk.Label(heading, text='', width=35, anchor=tk.N, font=Fonts.headings)
    self.genreLabel.grid(row=0, column=2, sticky=tk.NW)
    self.durationLabel = tk.Label(heading, text='', width=6, anchor=tk.NE, font=Fonts.headings)
    self.durationLabel.grid(row=0, column=3, sticky=tk.NW, padx=3)
    # details panel: director|cast\plot
    details = tk.Frame(self.main)
    details.grid(row=1, column=0, sticky=tk.NW)
    tk.Label(details, text='Reżyseria:', anchor=tk.NW, font=Fonts.details).grid(row=0, column=0, sticky=tk.NW)
    self.directorLabel = tk.Label(details, text='', width=25, anchor=tk.NW, font=Fonts.details)
    self.directorLabel.grid(row=0, column=1, sticky=tk.NW)
    tk.Label(details, text='Obsada:', anchor=tk.NW, font=Fonts.details).grid(row=0, column=2, sticky=tk.NW)
    self.castLabel = tk.Label(details, text='', width=30, anchor=tk.NW, font=Fonts.details)
    self.castLabel.grid(row=0, column=3, sticky=tk.NW)
    self.plotLabel = tk.Label(details, text='', width=65, wraplength=400, anchor=tk.CENTER, font=Fonts.plot)
    self.plotLabel.grid(row=1, column=0, columnspan=4)
    # filmweb rating
    rating = tk.Frame(self.main)
    rating.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky=tk.W)
    tk.Label(rating, text='Ocena\nFilmwebu:', anchor=tk.NW, font=Fonts.details).grid(row=0, column=0)
    self.ratingLabel = tk.Label(rating, text='', anchor=tk.NW, font=Fonts.fwRating)
    self.ratingLabel.grid(row=1, column=0)
  def fillInDetails(self, item:object):
    self.yearLabel['text'] = item['year']
    self.countryLabel['text'] = item['countries']
    self.genreLabel['text'] = item['genres']
    self.durationLabel['text'] = item['duration']
    self.directorLabel['text'] = item['directors']
    self.castLabel['text'] = item['cast']
    self.plotLabel['text'] = item['plot']
    self.ratingLabel['text'] = item['fwRating']

class DetailViewRating(DetailView):
  def __init__(self, root):
    super(DetailViewRating, self).__init__(root)
  def buildUI(self):
    tk.Label(self.main, text='Twoja ocena:', anchor=tk.NE, font=Fonts.details).grid(row=0, column=1, columnspan=2, sticky=tk.NE)
    self.rating = tk.Label(self.main, text='', anchor=tk.NE, font=Fonts.rating)
    self.rating.grid(row=1, column=1, sticky=tk.NE)
    self.faved = tk.Label(self.main, text=' ', anchor=tk.NE, font=Fonts.faved)
    self.faved.grid(row=1, column=2, sticky=tk.E)
    self.comment = tk.Label(self.main, text='', width=53, wraplength=500, anchor=tk.CENTER, font=Fonts.comment)
    self.comment.grid(row=0, column=0, rowspan=2, padx=9, sticky=tk.W)
  def fillInDetails(self, item:object):
    self.rating['text'] = item['rating'].split()[0] # only show the number
    self.faved['text'] = item['faved']
    self.comment['text'] = item['comment']

class DetailWindow(object):
  # A window that holds general information about the item
  # has an embedded frame, which is itself an object of a class derived from DetailView
  # this frame is specialized for displaying details of movie/show/game etc
  # whenever the window is brought up, fills the general fields on its own,
  # but to display detail information, it grids a specialized DetailView
  # Make sure there only exists a single window in the whole application.
  WINDOW = None
  @classmethod
  def getDetailWindow(cls):
    if cls.WINDOW is None:
      cls.WINDOW = DetailWindow()
    return cls.WINDOW

  def __init__(self):
    self.root = tk.Toplevel()
    self.__construct()
    self.root.resizable(0,0)
    self.root.title('Podgląd')
    self.root.withdraw()
  def __construct(self):
    # poster
    self.poster = tk.Label(self.root, text='POSTER', width=15, height=10, anchor=tk.NW)
    self.poster.grid(row=0, column=0, rowspan=3, sticky=tk.NW)
    # general info frame
    general = tk.Frame(self.root)
    general.grid(row=0, column=1, sticky=tk.NW)
    self.titleLabel = tk.Label(general, text='', width=30, anchor=tk.NW, font=Fonts.title)
    self.titleLabel.grid(row=0, column=0, sticky=tk.NW)
    self.otitleLabel = tk.Label(general, text='', anchor=tk.NW, font=Fonts.otitle)
    self.otitleLabel.grid(row=1, column=0, sticky=tk.NW)
    tk.Frame(general, height=10, width=20).grid(row=2, column=0) # padding
    # item type info
    self.itypeLabel = tk.Label(self.root, text='', anchor=tk.NE, font=Fonts.otitle)
    self.itypeLabel.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NE)
    # room for detailed information
    self.movieDetails = DetailViewMovies(self.root)
    self.movieDetails.grid(row=1, column=1, padx=5, pady=5, sticky=tk.NW)
    # room for rating information
    self.ratingDetails = DetailViewRating(self.root)
    self.ratingDetails.grid(row=2, column=1, padx=5, pady=5, sticky=tk.NW)
    # control panel
    control = tk.Frame(self.root)
    control.grid(row=3, column=1, sticky=tk.NE)
    tk.Button(control, text='Zamknij', command=self.root.withdraw).pack(side=tk.LEFT, padx=5, pady=5)
  # INTERFACE
  def launchPreview(self, item:object):
    self.titleLabel['text']  = item['title']
    self.otitleLabel['text'] = item['otitle']
    self.itypeLabel['text']  = item.TYPE_STRING
    # fill in details using a dedicated objects
    # TODO: when series/games/wanted things come in, there will be several detail
    # handlers; the unused ones (or: currently used one, if there is a change)
    # will have to be ungridded (grid_remove()) and the correct handler gridded
    self.movieDetails.fillInDetails(item)
    # same with rating/wantto
    self.ratingDetails.fillInDetails(item)
    # set the window title and bring it up
    self.root.title('{} ({})'.format(item['title'], item['year']))
    self.root.deiconify()
