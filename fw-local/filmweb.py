from datetime import date
import json

from bs4 import BeautifulSoup as BS
import requests_html

import containers

class FilmwebAPI(object):
  @staticmethod
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
      if page == 1:
        return userpage + '/films'
      else:
        return userpage + '/films?page=' + str(page)

  @staticmethod
  def login(username, password):
    credentials = {'j_username': username, 'j_password': password}

    session = requests_html.HTMLSession()
    log = session.post(FilmwebAPI.Constants.login_path, data=credentials)

    if FilmwebAPI.Constants.auth_error in log.text:
      print('BŁĄD LOGOWANIA')
      return None
    else:
      return FilmwebAPI(session, username)

  ## HACK
  @staticmethod
  def hackin():
    with open('creds.txt', 'r') as p:
      creds = p.read().split(',')
    return FilmwebAPI.login(*creds)

  def __init__(self, session, username):
    self.session = session
    self.username = username
    self.parsingRules = {}
    self.itemClasses = {}
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
          'attr': rule['attr'] if 'attr' in rule.keys() else None
        }
    #store the result
    self.parsingRules[itemtype] = pTree

  def getNumOf(self, itemtype:str):
    if itemtype == 'Movie':
      return self.getNumOfMovies()
    else:
      raise KeyError

  def getNumOfMovies(self):
    #return a tuple: (number of rated movies, number of movies per page)
    url = self.Constants.getUserMoviePage(self.username)
    page = self.__fetchPage(url)
    # TODO: in principle, this page could be cached for some small time
    #the number of user's movies is inside a span of a specific class
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

  def getMoviesPage(self, page=1):
    url = self.Constants.getUserMoviePage(self.username)
    page = self.__fetchPage(url)
    return self.__parsePage(page, 'Movie')

  def getDemoPage(self):
    with open('unrendered.html', 'rb') as f:
      h = f.read()
      bs = BS(h, 'lxml')
    return self.__parsePage(bs, 'Movie')

  def __fetchPage(self, url):
    page = self.session.get(url)
    if not page.ok:
      status = page.status_code
      #we should probably do something about this
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
                parsed[key] = [x.text.strip() for x in item.find_all('a')]
              else:
                parsed[key] = item.text.strip()
            else:
              #data is stored in the attribute
              parsed[key] = item.attrs[rule['attr']]
            #we're done with this one
            break
    #fetch the right class and construct the object
    constructObject = containers.classByString[itemtype]
    return constructObject(**parsed)

  def __parseRating(self, text):
    #FW stores the ratings as simple dict serialized to JSON
    origDict = json.loads(text)
    #translate that dict to more readable standard
    id = origDict['eId']
    ratingDict = {
      'rating':  origDict['r'],
      'comment': origDict['c'] if 'c' in origDict.keys() else '',
      'dateOf':  origDict['d'],
      'faved':   origDict['a']
    }
    return ratingDict, id
