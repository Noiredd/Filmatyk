from datetime import date
import json

from bs4 import BeautifulSoup as BS
import requests_html

import containers

class FilmwebAPI(object):
  class Constants(object):
    login_path = 'https://ssl.filmweb.pl/j_login'
    base_path  = 'https://www.filmweb.pl'
    auth_error = 'błędny e-mail lub hasło' #TODO: be a bit more intelligent here
    item_class = 'userVotesPage__result'
    f_cnt_span = 'blockHeader__titleInfoCount'
    def getUserPage(username):
      return FilmwebAPI.Constants.base_path + '/user/' + username
    def getUserMoviePage(username, page=1):
      userpage = FilmwebAPI.Constants.getUserPage(username)
      return userpage + '/films?page=' + str(page)
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
    self.__cacheParsingRules('Movie')

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

  def getNumOf(self, itemtype:str):
    if itemtype == 'Movie':
      return self.getNumOfMovies()
    else:
      raise KeyError

  @enforceSession
  def getNumOfMovies(self):
    #return a tuple: (number of rated movies, number of movies per page)
    url = self.Constants.getUserMoviePage(self.username)
    page = self.__fetchPage(url)
    # TODO: in principle, this page could be cached for some small time
    #the number of user's movies is inside a span of a specific class
    movies = 0
    for span in page.body.find_all('span'):
      if not span.has_attr('class'):
        continue
      if self.Constants.f_cnt_span not in span.attrs['class']:
        continue
      movies = int(span.text)
    #find all voting divs, like during parsing
    per_page = 0
    for div in page.body.find_all('div'):
      if not div.has_attr('data-id') or not div.has_attr('class'):
        continue
      if not self.Constants.item_class in div.attrs['class']:
        continue
      per_page += 1
    return movies, per_page

  def getItemsPage(self, itemtype:str, page:int=1):
    if itemtype == 'Movie':
      return self.getMoviesPage(page=page)
    else:
      raise KeyError #should never happen though

  @enforceSession
  def getMoviesPage(self, page=1):
    url = self.Constants.getUserMoviePage(self.username, page)
    page = self.__fetchPage(url)
    return self.__parsePage(page, 'Movie')

  def __fetchPage(self, url):
    #fetch the page and return its parsed representation
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

  def __parsePage(self, page, itemtype:str):
    parsed = []
    #find all voting divs with the item details (that will be parsed)
    for div in page.body.find_all('div'):
      if not div.has_attr('data-id') or not div.has_attr('class'):
        continue
      if not self.Constants.item_class in div.attrs['class']:
        continue
      #parse each single item (constructs an item object)
      parsed.append(self.__parseOne(div, itemtype))
    #ratings are stored elsewhere, but fortunately they are just JSONs
    for span in page.body.find_all('span'):
      if not span.has_attr('id'):
        continue
      span_id = span.attrs['id']
      for p in span.parents:
        if p.has_attr('data-source') and 'userVotes' in p.attrs['data-source']:
          #get a formatted dict from the JSON and ID of the item it belongs to
          rating, id = self.__parseRating(span.text)
          #among the parsed items, find one with matching ID and attach
          for item in parsed:
            if item.properties['id'] == id:
              item.addRating(rating)
    return parsed

  def __parseOne(self, div, itemtype:str):
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
                value = [x.text.strip() for x in item.find_all('a')]
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

  def __parseRating(self, text):
    #FW stores the ratings as simple dict serialized to JSON
    origDict = json.loads(text)
    #ensure all date keys are present
    date_ = origDict['d']
    if 'm' not in date_.keys():
      date_['m'] = 1
    if 'd' not in date_.keys():
      date_['d'] = 1
    #translate that dict to more readable standard
    id = origDict['eId']
    isFaved = origDict['f'] if 'f' in origDict.keys() else 0
    ratingDict = {
      'rating':  int(origDict['r']),
      'comment': origDict['c'] if 'c' in origDict.keys() else '',
      'dateOf':  date_,
      'faved':   isFaved
    }
    return ratingDict, id
