from datetime import date

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
    self.__cacheParsingRules(containers.Item)

  def __cacheParsingRules(self, class_):
    #get all the blueprints of a given class
    rawRules = {}
    for key, val in class_.__dict__.items():
      if type(val) is containers.Blueprint:
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
    self.parsingRules[class_.__name__] = pTree

  def getMoviesPage(self, page=1):
    url = self.Constants.getUserMoviePage(self.username)
    page = self.__fetchPage(url)
    return self.__parsePage(page, containers.Item)

  def getDemoPage(self):
    with open('unrendered.html', 'rb') as f:
      h = f.read()
      bs = BS(h, 'lxml')
    return self.__parsePage(bs, containers.Item)

  def __fetchPage(self, url):
    page = self.session.get(url)
    if not page.ok:
      status = page.status_code
      #we should probably do something about this
    else:
      return BS(page.html.html, 'lxml')

  def __parsePage(self, page, iType):
    #depending on the type of item to parse, select the correct parser
    if iType is containers.Item:
      parse = self.__parseItem
    else:
      exit() #this shouldn't ever happen, even after adding other item types
    parsed = []
    #this finds a voting div with all the item details (that need parsing)
    for div in page.body.find_all('div'):
      if not div.has_attr('data-id') or not div.has_attr('class'):
        continue
      if not self.Constants.item_class in div.attrs['class']:
        continue
      #use the parser on the each item (constructs an item object)
      parsed.append(parse(div))
    return parsed

  def __parseItem(self, div):
    #first we gather all results in a dict
    parsed = {'id': div.attrs['data-id']}
    #then we go through the parsing tree, tag by tag
    for tag, classes in self.parsingRules['Item'].items():
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
        # TEMP, until we sort out parsing ratings/wanna
        parsed['rating'] = '0'
        parsed['comment'] = ''
        #parsed['timeSeen'] = date(year=2000,month=9,day=22)
        parsed['favourite'] = '0'
    return containers.Item(**parsed)
