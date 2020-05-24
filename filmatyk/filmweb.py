from datetime import date
import binascii
import html
import json
import pickle

from bs4 import BeautifulSoup as BS
import requests_html

import containers


ConnectionError = requests_html.requests.ConnectionError


class UnauthenticatedError(ConnectionError):
  """Raised by API functions if they detect the active session was refused."""


class Constants():
  """URLs and HTML component names for data acquisition.

  Create an instance for a given user to generate their specific URLs.
  """
  login_path = 'https://ssl.filmweb.pl/j_login'
  base_path  = 'https://www.filmweb.pl'
  main_class = 'userVotesPage__results'
  item_class = 'userVotesPage__result'
  rating_source = 'userVotes'
  rating_stype = 'application/json'
  no_access_class = 'noResultsPlaceholder'
  movie_count_span = 'blockHeader__titleInfoCount'
  series_count_span = 'blockHeader__titleInfoCount'
  game_count_span = 'blockHeader__titleInfoCount'

  def __init__(self, username):
    self.username = username
    self.userpage = self.getUserPage()

  def getUserPage(self):
    return self.base_path + '/user/' + self.username

  def getUserMoviePage(self, page=1):
    return self.userpage + '/films?page={}'.format(page)

  def getUserSeriesPage(self, page=1):
    return self.userpage + '/serials?page={}'.format(page)

  def getUserGamePage(self, page=1):
    return self.userpage + '/games?page={}'.format(page)


class FilmwebAPI():
  """HTML-based API for acquiring data from Filmweb."""
  @staticmethod
  def login(username, password):
    """Attempt to acquire an authenticated user session."""
    session = requests_html.HTMLSession()
    auth_package = {
      'j_username': username,
      'j_password': password,
      '_login_redirect_url': '',
      '_prm': True,
    }
    # Catch connection errors
    try:
      log = session.post(Constants.login_path, data=auth_package)
    except ConnectionError:
      return (False, True)
    # Catch authentication errors
    if len(session.cookies) == 0:
      print('BŁĄD LOGOWANIA')
      return (False, False)
    else:
      return (True, session)

  def enforceSession(fun):
    """Decorator to mark API functions that require an authenticated session.

    This safeguards the calls to ensure they do not fail due to a lack of
    authentication with Filmweb. To achieve this goal, two checks are made:
    * before calling the decorated function, a check whether a live HTMLSession
      exists is made; if not, a login is requested,
    * the call itself is guarded against UnauthenticatedError, also resulting
      in a request for login and re-calling of the function.
    Additionally, session cookies are watched for changes, in order to set the
    isDirty flag in case that happens.

    Because it assumes that the first argument of the wrapped function is
    a bound FilmwebAPI instance ("self"), it shall only be used with FilmwebAPI
    methods.
    Because it is meant to be used as a class-level function decorator, it has
    no real "self" argument. It is effectively something like a static method.
    See the following links for more info:
      https://stackoverflow.com/q/21382801/6919631
      https://stackoverflow.com/q/11058686/6919631
    The bottom line is that it should NEVER be called directly.
    """
    def wrapper(*args, **kwargs):
      # Extract the bound FilmwebAPI instance
      self = args[0]
      # First check: for presence of a live session
      if not self.checkSession():
        return None
      old_cookies = set(self.session.cookies.values())
      # Second check: whether the call failed due to lack of authentication
      try:
        result = fun(*args, **kwargs)
      except UnauthenticatedError:
        # Request login and call again
        print('Session was stale! Requesting login...')
        self.requestSession()
        if not self.session:
          return None
        result = fun(*args, **kwargs)
      # Session change detection
      new_cookies = set(self.session.cookies.values())
      if old_cookies != new_cookies:
        self.isDirty = True
      # Finally the produced data is returned
      return result
    return wrapper

  def __init__(self, login_handler, username:str=''):
    self.username = username
    self.constants = Constants(username)
    self.login_handler = login_handler
    self.session = None
    self.isDirty = False
    self.parsingRules = {}
    for container in containers.classByString.keys():
      self.__cacheParsingRules(container)
    # bind specific methods and constants to their item types
    self.urlGenerationMethods = {
      'Movie': self.constants.getUserMoviePage,
      'Series': self.constants.getUserSeriesPage,
      'Game': self.constants.getUserGamePage
    }
    self.countSpanClasses = {
      'Movie': self.constants.movie_count_span,
      'Series': self.constants.series_count_span,
      'Game': self.constants.game_count_span
    }

  def __cacheParsingRules(self, itemtype:str):
    """Converts parsing rules for a given type into a neater representation.

    The rules for each Blueprint are expressed in a human-readable and human-
    writable form that makes them easy to modify if need be, but not very
    convenient for the parser. This method groups rules in a parser-friendly
    representation that makes its job easier.
    """
    # Get all the blueprints of a given class
    rawRules = {}
    for key, val in containers.classByString[itemtype].blueprints.items():
      rawRules[key] = val.getParsing()
    # Convert them to a parsing tree
    pTree = {}
    classes = set(rule['tag'] for rule in rawRules.values() if rule is not None)
    for c in classes:
      pTree[c] = {}
      for key, rule in rawRules.items():
        # Ignore any non-parsable fields
        if rule is None:
          continue
        # Process only the rules of class c
        if rule['tag'] != c:
          continue
        pClass = rule['class']
        pTree[c][pClass] = {
          'name': key,
          'text': rule['text'],
          'list': rule['list'] if 'list' in rule.keys() else False,
          'attr': rule['attr'] if 'attr' in rule.keys() else None,
          'type': rule['type'] if 'type' in rule.keys() else None
        }
    # Bind the result to a type name
    self.parsingRules[itemtype] = pTree

  def checkSession(self):
    """Check if there exists a session instance and acquire a new one if not."""
    session_requested = False
    if not self.session:
      self.requestSession()
      session_requested = True
    # Check again - in case the user cancelled a login
    if not self.session:
      return False
    # If a new session was requested in the process - set the dirty flag
    if session_requested:
      self.isDirty = True
    # At this point everything is definitely safe
    return True

  def requestSession(self):
    """Call the GUI to handle a login and bind a session object to self."""
    # This pauses execution until the user logs in or cancels
    session, username = self.login_handler(self.username)
    if session:
      # Set the username in case it's a first run (it will be empty)
      if not self.username:
        self.username = username
      else:
        # If it's not the first log in, make sure the user has logged as the
        # same user. If the GUI is to be trusted, it shouldn't be possible, but
        # we can still check in case of an accident during external usage.
        # Returned value isn't important. *NOT* setting self.session is.
        if username != self.username:
          return None
    self.session = session

  def storeSession(self):
    """Stores the sessions cookies to a base64-encoded pickle string."""
    if self.session:
      cookies_bin = pickle.dumps(self.session.cookies)
      cookies_str = binascii.b2a_base64(cookies_bin).decode('utf-8').strip()
      return cookies_str
    else:
      return 'null'

  def restoreSession(self, pickle_str:str):
    """Restores the session cookies from a base64-encoded pickle string."""
    if pickle_str == 'null':
      return
    self.session = requests_html.HTMLSession()
    cookies_bin = binascii.a2b_base64(pickle_str.encode('utf-8'))
    cookies_obj = pickle.loads(cookies_bin)
    self.session.cookies = cookies_obj

  @enforceSession
  def getNumOf(self, itemtype:str):
    """Return the number of items of a given type that the user has rated.

    Returns a tuple: (number of rated items, number of items per page).
    """
    getURL = self.urlGenerationMethods[itemtype]
    spanClass = self.countSpanClasses[itemtype]
    url = getURL()
    page = self.fetchPage(url)
    # TODO: in principle, this page could be cached for some small time
    #the number of user's movies is inside a span of a specific class
    items = 0
    for span in page.body.find_all('span'):
      if not span.has_attr('class'):
        continue
      if spanClass not in span.attrs['class']:
        continue
      items = int(span.text)
    #find all voting divs, like during parsing
    per_page = 0
    for div in page.body.find_all('div'):
      if not div.has_attr('data-id') or not div.has_attr('class'):
        continue
      if not self.constants.item_class in div.attrs['class']:
        continue
      per_page += 1
    return items, per_page

  @enforceSession
  def getItemsPage(self, itemtype:str, page:int=1):
    """Acquire items of a given type from a given page number.

    The user's ratings are displayed on pages. This fetches a page by number,
    parses it and returns a list of Item-based objects. URL is delivered by a
    cached dict, binding URL-generating functions to respective item types.
    """
    getURL = self.urlGenerationMethods[itemtype]
    url = getURL(page)
    page = self.fetchPage(url)
    data = self.parsePage(page, itemtype)
    return data

  @enforceSession
  def fetchPage(self, url):
    """Fetch the page and return its BeautifulSoup representation.

    ConnectionError is raised in case of any failure to get HTML data or page
    status being not-ok after get.
    UnauthenticatedError is raised if the response contains a span indicating
    that the session used to obtain it is no longer valid.
    """
    try:
      page = self.session.get(url)
    except:
      raise ConnectionError
    if not page.ok:
      status = page.status_code
      print("FETCH ERROR {}".format(status))
      raise ConnectionError
    else:
      bspage = BS(page.html.html, 'lxml')
    # If a request required an active session but the one we had happened to be
    # stale, this magical span will be found in the page data:
    span = bspage.find('span', attrs={'class': self.constants.no_access_class})
    if span:
      raise UnauthenticatedError
    return bspage

  def parsePage(self, page, itemtype:str):
    """Parse items and ratings, returning constructed Item objects."""
    data_div = self.extractDataSource(page)
    sub_divs = self.extractItems(data_div)
    parsed_items = [self.parseOne(div, itemtype) for div in sub_divs]
    ratings = [self.parseRating(txt) for txt in self.extractRatings(data_div)]
    for rating, iid in ratings:
      for item in parsed_items:
        if item.getRawProperty('id') == iid:
          item.addRating(rating)
    return parsed_items

  def extractDataSource(self, page):
    """Extract the div that holds all the data."""
    return page.find('div', attrs={'class': self.constants.main_class})

  def extractItems(self, div):
    """From the main div, extract all divs holding item details."""
    sub_divs = div.find_all('div', attrs={'class': self.constants.item_class})
    sub_divs = [div for div in sub_divs if div.has_attr('data-id')]
    return sub_divs

  def extractRatings(self, div):
    """From the main div, extract all item ratings.

    They're held in a specific span as <script> contents.
    """
    span = div.find('span', attrs={'data-source': self.constants.rating_source})
    scripts = span.find_all('script', attrs={'type': self.constants.rating_stype})
    ratings = [script.getText() for script in scripts]
    return ratings

  def parseOne(self, div, itemtype:str):
    """Parse a single item, constructing its container representation."""
    #first, gather all results in a dict
    parsed = {'id': int(div.attrs['data-id'])}
    #then, select the right set of parsing rules
    parsing_rules = self.parsingRules[itemtype]
    #finally, we go through the parsing tree, tag by tag
    for tag, classes in parsing_rules.items():
      #fetch all the items of this tag
      for item in div.find_all(tag):
        #ignore those which do not belong to any class
        if not item.has_attr('class'):
          continue
        #scan through the list of Classes Of Interest for this tag
        for coi, rule in classes.items():
          if coi in item.attrs['class']:
            #if the given item is of a class of interest - parse it
            key = rule['name']
            if rule['text']:
              #data is stored withing a 'text' field
              if rule['list']:
                #data is actually a list of things
                value = [x.text.strip() for x in item.find_all('li')]
              else:
                value = item.text.strip()
            else:
              #data is stored in the attribute
              value = item.attrs[rule['attr']]
            #finally, convert the datum to a specified type, if any
            rtype = rule['type']
            parsed[key] = rtype(value) if rtype else value
            break
    #fetch the right class and construct the object
    constructObject = containers.classByString[itemtype]
    return constructObject(**parsed)

  def parseRating(self, text):
    """Parse the rating information into compatible dict.

    FW stores the ratings as simple dict serialized to JSON, this only ensures
    all the entries are present and translates them to a standard expected by
    Item's addRating method.
    """
    origDict = json.loads(text)
    # Ensure all date keys are present
    try:
      date_ = origDict['d']
    except KeyError:
      # I've seen a bugged span once, which didn't have this key
      date_ = {'y':2000, 'm':1, 'd':1}
    if 'm' not in date_.keys():
      date_['m'] = 1
    if 'd' not in date_.keys():
      date_['d'] = 1
    # Unescape HTML-coded characters from the comment
    comment = html.unescape(origDict['c'] if 'c' in origDict.keys() else '')
    # Translate that dict to a more readable standard
    iid = origDict['eId']
    isFaved = origDict['f'] if 'f' in origDict.keys() else 0
    ratingDict = {
      'rating':  int(origDict['r']),
      'comment': comment,
      'dateOf':  date_,
      'faved':   isFaved
    }
    return ratingDict, iid
