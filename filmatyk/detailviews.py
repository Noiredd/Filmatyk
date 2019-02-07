from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk

import containers
import posterman

class Fonts(object):
  default  = 'TkDefaultFont'
  title    = (default, 24)
  otitle   = (default, 12)
  headings = (default, 10, 'bold')
  details  = (default, 10)
  plot     = (default, 11)
  fwRating = (default, 24)
  rating   = (default, 48)
  faved    = (default, 40)
  comment  = (default, 14, 'italic')

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
  def grid_remove(self, **args):
    self.main.grid_remove(**args)

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

class DetailViewSeries(DetailViewMovies):
  def __init__(self, root):
    super(DetailViewSeries, self).__init__(root)

class DetailViewGames(DetailView):
  def __init__(self, root):
    super(DetailViewGames, self).__init__(root)
  def buildUI(self):
    # heading panel: year|country|genre|duration
    heading = tk.Frame(self.main)
    heading.grid(row=0, column=0, sticky=tk.NW)
    self.yearLabel = tk.Label(heading, text='', width=5, anchor=tk.NW, font=Fonts.headings)
    self.yearLabel.grid(row=0, column=0, sticky=tk.NW, padx=3)
    self.genreLabel = tk.Label(heading, text='', width=27, anchor=tk.N, font=Fonts.headings)
    self.genreLabel.grid(row=0, column=1, sticky=tk.NW)
    self.platformLabel = tk.Label(heading, text='', width=40, anchor=tk.NE, font=Fonts.headings)
    self.platformLabel.grid(row=0, column=2, sticky=tk.NW, padx=2)
    # details panel: developer|publisher\plot
    details = tk.Frame(self.main)
    details.grid(row=1, column=0, sticky=tk.NW)
    tk.Label(details, text='Deweloper:', anchor=tk.NW, font=Fonts.details).grid(row=0, column=0, sticky=tk.NW)
    self.developerLabel = tk.Label(details, text='', width=25, anchor=tk.NW, font=Fonts.details)
    self.developerLabel.grid(row=0, column=1, sticky=tk.NW)
    tk.Label(details, text='Wydawca:', anchor=tk.NW, font=Fonts.details).grid(row=0, column=2, sticky=tk.NW)
    self.publisherLabel = tk.Label(details, text='', width=25, anchor=tk.NW, font=Fonts.details)
    self.publisherLabel.grid(row=0, column=3, sticky=tk.NW)
    self.plotLabel = tk.Label(details, text='', width=65, wraplength=550, anchor=tk.CENTER, font=Fonts.plot)
    self.plotLabel.grid(row=1, column=0, columnspan=4)
    # filmweb rating
    rating = tk.Frame(self.main)
    rating.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky=tk.W)
    tk.Label(rating, text='Ocena\nFilmwebu:', anchor=tk.NW, font=Fonts.details).grid(row=0, column=0)
    self.ratingLabel = tk.Label(rating, text='', anchor=tk.NW, font=Fonts.fwRating)
    self.ratingLabel.grid(row=1, column=0)
  def fillInDetails(self, item:object):
    self.yearLabel['text'] = item['year']
    self.genreLabel['text'] = item['genres']
    self.platformLabel['text'] = item['platforms']
    self.developerLabel['text'] = item['developers']
    self.publisherLabel['text'] = item['publishers']
    self.plotLabel['text'] = item['plot']
    self.ratingLabel['text'] = item['fwRating']

class DetailViewRating(DetailView):
  def __init__(self, root):
    super(DetailViewRating, self).__init__(root)
  def buildUI(self):
    tk.Label(self.main, text='Twoja ocena:', anchor=tk.NE, font=Fonts.details).grid(row=0, column=2, columnspan=2, sticky=tk.NE)
    self.rating = tk.Label(self.main, text='', width=2, anchor=tk.NE, font=Fonts.rating)
    self.rating.grid(row=1, column=2, sticky=tk.NE)
    self.faved = tk.Label(self.main, text=' ', width=1, anchor=tk.NE, font=Fonts.faved)
    self.faved.grid(row=1, column=3, sticky=tk.E)
    self.date = tk.Label(self.main, text='', anchor=tk.NW, font=Fonts.plot)
    self.date.grid(row=0, column=0, sticky=tk.NW)
    self.comment = tk.Label(self.main, text='', width=50, wraplength=500, anchor=tk.CENTER, font=Fonts.comment)
    self.comment.grid(row=0, column=0, rowspan=3, columnspan=2, padx=7, pady=20, sticky=tk.NW)
  def fillInDetails(self, item:object):
    self.rating['text'] = item['rating'].split()[0] # only show the number
    self.faved['text'] = item['faved']
    self.date['text'] = item['dateOf']
    self.comment['text'] = item['comment']

TYPE_TO_VIEW_BINDINGS = {
  containers.Movie.TYPE_STRING:  DetailViewMovies,
  containers.Series.TYPE_STRING: DetailViewSeries,
  containers.Game.TYPE_STRING:   DetailViewGames
}

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
    self.detailViews = {} # for displaying the right DetailView
    self.activeView = None
    self.posterManager = posterman.PosterManager()
    self.__construct()
    self.root.protocol('WM_DELETE_WINDOW', self.root.withdraw)
    self.root.resizable(0,0)
    self.root.title('Podgląd')
    self.root.withdraw()
  def __construct(self):
    # poster
    self.poster = tk.Label(self.root, text='POSTER', anchor=tk.NW)
    self.poster.grid(row=0, column=0, rowspan=4, sticky=tk.NW)
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
    for type_string, view_class in TYPE_TO_VIEW_BINDINGS.items():
      view = view_class(self.root)
      # place the frames temporarily, just to let them remember where they should be
      view.grid(row=1, column=1, padx=5, pady=5, sticky=tk.NW)
      view.grid_remove()
      self.detailViews[type_string] = view
    # during the first run we might not have any view placed, so to be safe we'd have
    # to ask for it every time - it feels simpler to just place one View instead
    view.grid()
    self.activeView = type_string
    # room for rating information
    self.ratingDetails = DetailViewRating(self.root)
    self.ratingDetails.grid(row=2, column=1, padx=5, pady=5, sticky=tk.NW)
    # control panel
    control = tk.Frame(self.root)
    control.grid(row=3, column=1, sticky=tk.NE)
    ttk.Button(control, text='Zamknij', command=self.root.withdraw).pack(side=tk.LEFT, padx=5, pady=5)
  # INTERFACE
  def launchPreview(self, item:object):
    self.titleLabel['text']  = item['title']
    self.otitleLabel['text'] = item['otitle']
    self.itypeLabel['text']  = item.TYPE_STRING
    # get the poster
    posterURL = item.getRawProperty('imglink')
    posterPath = self.posterManager.getPosterByURL(posterURL)
    image = Image.open(posterPath)
    self.image = ImageTk.PhotoImage(image)
    self.poster.configure(image=self.image)
    # fill in details using a dedicated objects
    # select the right View for the item type
    if item.TYPE_STRING != self.activeView:
      # ungrid the previously used View, if there was any
      self.detailViews[self.activeView].grid_remove()
      # grid the new one instead
      self.detailViews[item.TYPE_STRING].grid()
      self.activeView = item.TYPE_STRING
    self.detailViews[self.activeView].fillInDetails(item)
    # TODO: similar with rating/wantto
    self.ratingDetails.fillInDetails(item)
    # set the window title and bring it up
    self.root.title('{} ({})'.format(item['title'], item['year']))
    self.root.deiconify()
