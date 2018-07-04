import os
import pickle

import filtering

#TODO: we could read the number of movies from the main profile page
#TODO: we could add a progress bar to let the user know what's going on

DATABASE = '../database.pkl'

def checkDataExists():
  return True if os.path.isfile(DATABASE) else False

def restoreFromFile():
  with open(DATABASE,'rb') as dbf:
    un, mv = pickle.load(dbf)
    db = Database(un)
    db.movies = mv
    return db


class Database(object):
  def __init__(self, username):
    self.username = username
    self.movies = []
    self.filtered = []
    self.sorted = []

  #PUBLIC
  def setConfig(self, config):
    self.config = config
  def softUpdate(self, scraper):
    #safety check
    if scraper.username != self.username:
      print("LOGGED IN AS DIFFERENT USER")
      return False
    #collect ids of movies we already know
    known_ids = [movie['id'] for movie in self.movies]
    #run scraper until we load a page containing some movie we already have
    new_movies = []
    fetched = scraper.processNext()
    found = False
    while scraper.isThereMore():
      #scan the loaded movies and compare against our library
      for movie in fetched:
        if movie['id'] in known_ids:
          #if we have this movie - break out of the loops and merge the lists
          found = True
          break
      #we load from the website in batches ('fetched'), so that we only look at
      #a single batch of movies at once, not all the movies we've loaded
      #we need to update the list by the fresh batch
      new_movies += fetched
      if found: break
    #now, if we've found a movie that we already knew, we have to merge the
    #gathered list with the known ones
    #most likely there will be some overlap between movies and self.movies; in
    #this case we will overwrite with the fresh values
    old_movies = self.movies
    self.movies = new_movies
    new_ids = [movie['id'] for movie in new_movies]
    for movie in old_movies:
      if movie['id'] not in new_ids:
        self.movies.append(movie)
    print("UPDATED")
    self._save()
  def hardUpdate(self, scraper):
    #safety check
    if scraper.username != self.username:
      print("LOGGED IN AS DIFFERENT USER")
      return False
    #run scraper until there are no more pages left
    #get the first page and see if it went okay
    movies = scraper.processPage()
    if len(movies) == 0:
      print("PROBABLE ERROR SCRAPING MOVIES. ARE YOU LOGGED IN?")
      return False
    while scraper.isThereMore():
      print("SCRAPING PAGE", scraper.pageIndex)
      movies += scraper.processNext()
    #only forget the existing one if we have the full thing
    self.movies = movies
    print("READ", scraper.pageIndex-1, "PAGES")
    self._save()
  def filterMovies(self, filters:dict={}):
    #convert the dict of variables into a callable criteria-checking function
    checker = filtering.construct(filters)
    #then select only those movies that pass the criteria
    self.filtered = [movie for movie in self.movies if checker(movie)]
  def sortMovies(self, sorting):
    key = sorting['key']
    ord = sorting['descending']
    #if the field we sort over has a formatter - ensure we sort over formatted values
    formatter = None
    for conf in self.config:
      if conf[0]==key:
        formatter = conf[1]['format']
    if formatter is not None:
      sorter = lambda m: formatter(m[key])
    else:
      sorter = lambda m: m[key]
    #except for rating - string sorting results in 10<1 this way
    if key=='rating':
      sorter = lambda m: int(m['rating'])
    #sort the filtered list in-place
    self.filtered.sort(key=sorter, reverse=not ord)
  def returnMovies(self):
    #extract presentation-ready values: config contains the order of values and
    #formatting functions
    display = []
    histogram = [0 for i in range(11)]
    for movie in self.filtered:
      mov = []
      mov.append(movie['id'])
      for conf in self.config:
        #Each conf is a 2-tuple containing key name and presentation rule
        if conf[1]['format'] is not None:
          mov.append(conf[1]['format'](movie[conf[0]]))
        else:
          mov.append(movie[conf[0]])
      display.append(mov)
      rating = int(movie['rating'])
      histogram[rating] += 1
    return display, histogram
  def getListOfAll(self, what):
    all_what = set()
    for movie in self.movies:
      for x in movie[what]:
        all_what.add(x)
    return sorted(list(all_what))
  def getYearsSeen(self):
    all_years = set()
    for movie in self.movies:
      all_years.add(movie['timeSeen'].year)
    return sorted(list(all_years))
  def getMovieByID(self, id):
    for movie in self.movies:
      if movie['id'] == str(id):
        return movie
    return None

  #INTERNALS
  def _save(self):
    with open(DATABASE, 'wb') as dbf:
      pickle.dump((self.username, self.movies), dbf)
