from datetime import date

from bs4 import BeautifulSoup as BS
import requests_html

from blueprint import Blueprint

def login(username, password):
  credentials = {'j_username': username, 'j_password': password}

  session = requests_html.HTMLSession()
  log = session.post(Scraper.login_path, data=credentials)

  if Scraper.bad_login in log.text:
    print('FAILED TO LOG IN')
    return None
  else:
    return Scraper(session, username)

''' How does parsing work
  Filmweb's data is divided into two parts - movie information is stored in one
  place, while rating information is elsewhere. We parse movies first, as it is
  more complex. Each particular movie info is held in a div with a rather long
  class name - the first step is finding and extracting those divs, by string
  'userVotesPage__result'.
  Each of them contains more nested elements (divs, h3's, links etc.), each
  holding different kind of information. As a result of parsing, we would like
  to have a dict of our own making, with keys standardized to make integration
  with the GUI easier. For this reason we introduce a concept of parsing rules.
  The idea is that each datum we want to extract is held by a different element
  in the HTML. Those elements can differ by tag (most information is in divs,
  but some are also in other kind of tags), by class name (or a specific string
  in that name) and by means of embedding data in the element (it might be in
  the elements text directly, or in an attribute of some known name). Therefore
  each parsing rule will specify how to look for a given datum and then how to
  extract it. They shall be given by tuples (datum_name, rule), where datum_name
  is the name by which the datum should be stored in the parsed dict, and rule
  is a dict specifying the following information as keys:
    'tag':    name of the tag of element holding the data (div, h3, a, ...)
    'class':  string that the 'class' attribute of the element will contain
              <div class="blah blah name blah">
    'text':   bool, whether the interesting data is stored within the element as
              text - if not, it is then in one of the other attributes
    'array':  bool, required when 'text' is True, specifies whether the datum
              should be parsed into an array (NOTE: it is assumed that such
              datum is stored as several links "<a>")
    'attr':   bool, required when 'text' is False, specifies the name of the
              attribute which holds the interesting datum, eg. "data-duration":
              <div class=filmPreview__filmTime" data-duration="90">
  Those rules are given in the Blueprint, along with presentation rules.
  For faster processing, they are converted to an optimal structure.
  Consult Scraper::__init__ for details.
'''

class Scraper(object):
  login_path = 'https://ssl.filmweb.pl/j_login'
  bad_login = 'błędny e-mail lub hasło'
  base_path = 'https://www.filmweb.pl'

  def __init__(self, session, username):
    self.session = session
    self.username = username
    self.pagesLeft = False
    self.pageIndex = 0  #last processed page

    '''  Reorganize parsing rules for faster processing
      The notation given in the Blueprint is more manageable, but it's not very
      good for fast processing - for each element on that list would have to see
      what its class is, extract all elements of that class, see what the class
      name is, go through all the elements looking for that name and then parse.
      This process would repeat for each datum, which is far from fast.
      What we want to be doing instead, is to find all e.g. divs just once, go
      through all of them and see if their class name contains any keyword from
      the parsing rules, and then apply a rule to extract the relevant datum. In
      order to do that, we reorder the rules so that the class type and name are
      the first things to look at, and the processing rule and name of output
      value are the last ones.
      We achieve this by a dict tree: the root contains classes (i.e. all kinds
      of dicts we might look for are in one branch), then for each class there
      is a dict keyed by names, containing final parsing rules: name of output
      and means of processing.
      Consult Scraper::_parseSingleMovie for parsing logic.
    '''
    self.processedParsingRules = {} #a tree-like structure
    #populate the main dict - ignore the positions with no parsing rules
    classes = set( v['html_parsing']['tag'] for v in Blueprint.values() if v['html_parsing'] is not None)
    for c in classes:
      self.processedParsingRules[c] = {}
    #populate each class with names of interest and processing rules
    for c in classes:
      for key in Blueprint.keys():
        if Blueprint[key]['html_parsing'] is None:
          continue  #this is most likely a rating-related field with its own logic
        pr = Blueprint[key]['html_parsing']
        if pr['tag'] != c:
          continue
        p_class = pr['class']
        self.processedParsingRules[c][p_class] = {
          'outName': key,
          'text':  pr['text'],
          'array': pr['array'] if 'array' in pr.keys() else False,
          'attr':  pr['attr']  if 'attr'  in pr.keys() else None
        }

  def processPage(self, index=1):
    page = self._fetchPage(index)
    self.pagesLeft = self._checkPagination(page)
    movies = self._parseMovies(page)
    rating = self._parseRating(page)
    self.pageIndex = index
    return self._processResults(movies, rating)
  def processNext(self):
    return self.processPage(self.pageIndex + 1)
  def isThereMore(self):
    return self.pagesLeft

  #INTERNALS
  def _pageUrlByIndex(self, index):
    return self.base_path + '/user/' + self.username + '/films?page=' + str(index)
  def _fetchPage(self, index):
    url = self._pageUrlByIndex(index)
    page = self.session.get(url)
    page.html.render(reload=False)
    return BS(page.html.html, 'lxml')
  def _checkPagination(self, page):
    for a in page.find_all('a'):
      for p in a.parents:
        if p.has_attr('class') and 'pagination__item--next' in p.attrs['class']:
          return True
    return False
  def _parseMovies(self, page):
    #find divs that contain movie info and parse them
    movies = []
    for div in page.body.find_all('div'):
      if not div.has_attr('data-id') or not div.has_attr('class'):
        continue
      if not 'userVotesPage__result' in div.attrs['class']:
        continue
      movies.append(self._parseSingleMovie(div))
    return movies
  def _constructEmptyMovie(self):
    #constructs a bare-bones movie template according to the Blueprint
    #this ensures that every movie has all the standard dict keys
    movie = {}
    for key in Blueprint.keys():
      movie[key] = ''
    return movie
  def _parseSingleMovie(self, movie):
    #analyzes a given div by the parsing rules
    parsed = self._constructEmptyMovie()
    parsed['id'] = movie.attrs['data-id'] #our output-to-be
    for c in self.processedParsingRules.keys():
      #for each class of items we are only interested in the following class names:
      names = self.processedParsingRules[c].keys()
      #fetch all the items of a given class
      for item in movie.find_all(c):
        #ignore those which do not have any 'class' string
        if not item.has_attr('class'):
          continue
        #check if its class belongs to any of the classes of interest
        for coi in names:
          if coi in item.attrs['class']:
            #if so - it's a match, and we should parse accordingly
            rules = self.processedParsingRules[c][coi]
            keyName = rules['outName']  #store the datum under this key
            if rules['text']:
              #relevant information is stored within the element's text
              if rules['array']:
                #relevant information needs to be processed into a list
                parsed[keyName] = [x.text.strip() for x in item.find_all('a')]
              else:
                parsed[keyName] = item.text.strip()
            else:
              #relevant information is stored within an attribute
              parsed[keyName] = item.attrs[rules['attr']]
            break
    #fix for missing original titles
    if parsed['otitle'] == '':
      parsed['otitle'] = parsed['title']
    return parsed
  def _parseRating(self, page):
    ''' How are ratings parsed
      The ratings are held somewhere else than movies (i.e. the rating data for
      a movie is NOT stored in the same div as this movie). For this reason, we
      need to parse them in a different way. The information is stored in spans
      with an attribute 'data-source'. Inside it there's a plain text of a dict
      storing the individual values (btw, we could actually parse it by calling
      eval() on it directly).
      Processing is simple: find and extract those spans, then use custom logic
      to make a dict out of it. Standard of this dict is only internal, as the
      values will be appended to the main movie dict, along with its other data.
    '''
    ratings = {}  #keyed by movie id
    for span in page.body.find_all('span'):
      if not span.has_attr('id'):
        continue
      span_id = span.attrs['id']
      for p in span.parents:
        if p.has_attr('data-source') and 'userVotes' in p.attrs['data-source']:
          ratings[span_id] = self._parseSingleRating(span.text)
          break
    return ratings
  def _parseSingleRating(self, span:str):
    # NOTE: it is a bit messy
    #strip the surrounding spaces and curly braces
    r_ = span.split('{')
    r  = '{'.join(r_[1:])
    l_ = r.split('}')
    span = '}'.join(l_[:-1])
    span = span.strip() + ',' #comma is needed to stop parsing
    #tokenization with a state machine
    _dict = {}  #target, we add stuff to this dict
    key = str() #if we're currently parsing a key, chars are added here
    val = str() #if we're currently parsing a value, chars are added here
    in_dict = False   #if we're currently in a nested dict
    in_string = False #if we're currently in a string
    look_key = True   #if we're currently looking for a key
    for s in span:
      #control characters for strings and dicts
      if s=='"':
        in_string = False if in_string else True
      elif s=='{':
        in_dict = True
      elif s=='}':
        in_dict = False #can't handle multiple nested dicts (shouldn't be an issue)
      #if we're inside a string or a sub-dict - ignore anything, just raw copy
      if in_string or in_dict:
        if look_key:
          key += s
        else:
          val += s
        continue
      #deal with keys and values
      if s==':':
        #colon is a switching char
        look_key = False
      elif s==',':
        #comma means end of key-value pair (that's why we added it)
        #now, if a value was also a dict - has to be parsed now
        if '{' in val and val.find('{') < val.find('"'):
          #the AND protects against cases where { appears inside a string
          _dict[key.strip().strip('"')] = self._parseSingleRating(val)
        else:
          _dict[key.strip().strip('"')] = val.strip().strip('""')
        #switch back to looking for a key, reset values
        look_key = True
        key = str()
        val = str()
      else:
        #oh, a normal char - just add to whatever we're processing
        if look_key:
          key += s
        else:
          val += s
    return _dict
  def _processResults(self, movies:list, rating:list):
    #binds ratings to movies
    output = []
    for mov in movies:
      mov_id = mov['id']
      m_rate = rating[mov_id]
      #we don't need ALL the data, just those:
      mov['rating'] = m_rate['r'] if 'r' in m_rate.keys() else None
      mov['favourite'] = m_rate['a'] if 'a' in m_rate.keys() else None
      mov['comment'] = m_rate['c'] if 'c' in m_rate.keys() else ''
      #convert the date to an object
      if 'd' not in m_rate.keys():
        mov['timeSeen'] = None  #should never be the case
      else:
        mov['timeSeen'] = date(
          year  = int(m_rate['d']['y']),
          month = int(m_rate['d']['m']) if 'm' in m_rate['d'].keys() else 1,
          day   = int(m_rate['d']['d']) if 'd' in m_rate['d'].keys() else 1
        )
      #put this back to results
      output.append(mov)
    return output
