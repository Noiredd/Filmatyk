from datetime import date
import json

from bs4 import BeautifulSoup as BS
import html
import requests_html

import containers

class FilmwebAPI(object):
  class Constants(object):
    login_path = 'https://ssl.filmweb.pl/j_login'
    base_path  = 'https://www.filmweb.pl'
    auth_error = 'błędny e-mail lub hasło' #TODO: be a bit more intelligent here
    main_class = 'userVotesPage__results'
    item_class = 'userVotesPage__result'
    rating_source = 'userVotes'
    rating_stype = 'application/json'
    m_count_span = 'blockHeader__titleInfoCount'
    s_count_span = 'blockHeader__titleInfoCount'
    g_count_span = 'blockHeader__titleInfoCount'
    @classmethod
    def getUserPage(self, username):
      return self.base_path + '/user/' + username
    @classmethod
    def getUserMoviePage(self, username, page=1):
      userpage = self.getUserPage(username)
      return userpage + '/films?page={}'.format(page)
    @classmethod
    def getUserSeriesPage(self, username, page=1):
      userpage = self.getUserPage(username)
      return userpage + '/serials?page={}'.format(page)
    @classmethod
    def getUserGamePage(self, username, page=1):
      userpage = self.getUserPage(username)
      return userpage + '/games?page={}'.format(page)

  ConnectionError = requests_html.requests.ConnectionError

  @staticmethod
  def login(username, password):
    session = requests_html.HTMLSession()
    try:
      log = session.post(
        FilmwebAPI.Constants.login_path,
        data={'j_username': username, 'j_password': password}
      )
    except FilmwebAPI.ConnectionError:
      return (False, True) # login error, connection error
    if FilmwebAPI.Constants.auth_error in log.text:
      print('BŁĄD LOGOWANIA')
      return (False, False)
    else:
      return (True, session)

  #@staticmethod -- but not actually a static method, see:
  # https://stackoverflow.com/q/21382801/6919631
  # https://stackoverflow.com/q/11058686/6919631
  #in short: THIS METHOD SHOULD NEVER BE CALLED DIRECTLY
  def enforceSession(fun):
    #this decorator makes the function being called cause the caller
    #(assumed to be the first object in the argument list) to call the
    #session check method (which in turn can request a new session)
    def wrapper(*args, **kwargs):
      self = args[0]
      if self.checkSession():
        return fun(*args, **kwargs)
      else:
        return None
    return wrapper

  def __init__(self, callback, username:str=''):
    self.username = username
    self.requestLogin = callback
    self.session = None
    self.parsingRules = {}
    self.__cacheAllParsingRules()
    # bind specific methods and constants to their item types
    self.urlGenerationMethods = {
      'Movie':  self.Constants.getUserMoviePage,
      'Series': self.Constants.getUserSeriesPage,
      'Game':   self.Constants.getUserGamePage
    }
    self.countSpanClasses = {
      'Movie':  self.Constants.m_count_span,
      'Series': self.Constants.s_count_span,
      'Game':   self.Constants.g_count_span
    }

  def __cacheAllParsingRules(self):
    for container in containers.classByString.keys():
      self.__cacheParsingRules(container)

  def __cacheParsingRules(self, itemtype:str):
    #get all the blueprints of a given class
    rawRules = {}
    for key, val in containers.classByString[itemtype].blueprints.items():
      rawRules[key] = val.getParsing()
    #convert them to a parsing tree
    pTree = {}
    classes = set(rule['tag'] for rule in rawRules.values() if rule is not None)
    for c in classes:
      pTree[c] = {}
      for key, rule in rawRules.items():
        #ignore any non-parsable fields
        if rule is None:
          continue
        #process only the rules of class c
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
    #store the result
    self.parsingRules[itemtype] = pTree

  def checkSession(self):
    #check if there is a session and acquire one if not
    if not self.session:
      self.requestSession()
    #check again - in case the user cancelled a login
    if not self.session:
      return False
    #at this point everything is definitely safe
    return True

  def requestSession(self):
    #call the GUI callback for login handling
    #it will halt execution until the user logs in or cancels
    session, username = self.requestLogin(self.username)
    #if the session wasn't acquired, don't care about username
    #but for good session, check if it agrees with the existing one (or set it)
    if session:
      if not self.username:
        self.username = username
      else:
        if username != self.username:
          #this should never happen, if GUI is to be trusted
          #returning is not as important as *not* setting self.session
          return None
    self.session = session

  @enforceSession
  def getNumOf(self, itemtype:str):
    #return a tuple: (number of rated movies, number of movies per page)
    try:
      getURL = self.urlGenerationMethods[itemtype]
      spanClass = self.countSpanClasses[itemtype]
    except KeyError:
      return 0, 0 # should never happen though
    url  = getURL(self.username)
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
      if not self.Constants.item_class in div.attrs['class']:
        continue
      per_page += 1
    return items, per_page

  @enforceSession
  def getItemsPage(self, itemtype:str, page:int=1):
    # Get the URL of a page containing items of requested type, fetch and parse
    # it and return data (as list of objects). Instead of several ifs, retrieve
    # the proper methods from a dict prepared during init.
    try:
      getURL  = self.urlGenerationMethods[itemtype]
    except KeyError:
      return [] # should never happen though
    url  = getURL(self.username, page)
    page = self.fetchPage(url)
    data = self.parsePage(page, itemtype)
    return data

  def fetchPage(self, url):
    """Fetch the page and return its BeautifulSoup representation."""
    try:
      page = self.session.get(url)
    except:
      raise ConnectionError
    if not page.ok:
      status = page.status_code
      print("FETCH ERROR {}".format(status))
      raise ConnectionError
    else:
      return BS(page.html.html, 'lxml')

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
    return page.find('div', attrs={'class': self.Constants.main_class})

  def extractItems(self, div):
    """From the main div, extract all divs holding item details."""
    sub_divs = div.find_all('div', attrs={'class': self.Constants.item_class})
    sub_divs = [div for div in sub_divs if div.has_attr('data-id')]
    return sub_divs

  def extractRatings(self, div):
    """From the main div, extract all item ratings.

    They're held in a specific span as <script> contents.
    """
    span = div.find('span', attrs={'data-source': self.Constants.rating_source})
    scripts = span.find_all('script', attrs={'type': self.Constants.rating_stype})
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
    #ensure all date keys are present
    try:
      date_ = origDict['d']
    except KeyError:
      # once I've seen a bugged span in which this key was not present
      date_ = {'y':2000, 'm':1, 'd':1}
    if 'm' not in date_.keys():
      date_['m'] = 1
    if 'd' not in date_.keys():
      date_['d'] = 1
    # unescape HTML-coded characters from the comment
    comment = html.unescape(origDict['c'] if 'c' in origDict.keys() else '')
    # translate that dict to more readable standard
    iid = origDict['eId']
    isFaved = origDict['f'] if 'f' in origDict.keys() else 0
    ratingDict = {
      'rating':  int(origDict['r']),
      'comment': comment,
      'dateOf':  date_,
      'faved':   isFaved
    }
    return ratingDict, iid
