def construct(filters:dict):
  #instantiate callable objects for each item in the dict
  #assemble them into a function
  #constructor for each filter validates the filter parameter
  #call method for each filter validates the argument
  filter_map = {
    'year_from':  YearFromFilter,
    'year_to':    YearToFilter,
    'genre':      GenreFilter
  }
  def _filterFunction(movie):
    status = True
    for f in _filterFunction.filters:
      status = f(movie)
      if not status: break
    return status
  _filterFunction.filters = []
  for key in filters.keys():
    try:
      f = filter_map[key](filters[key])
    except:
      continue
    else:
      _filterFunction.filters.append(f)
  return _filterFunction


class InvalidParameter(Exception):
  pass

class BaseFilter(object):
  def __init__(self, parameter):
    try:
      self.validateParameter(parameter)
    except:
      self.param = None
    if self.param == None:
      raise InvalidParameter
  def __call__(self, movie):
    return self.filteringLogic(movie)
  #OVERRIDE BELOW
  def validateParameter(self, parameter):
    #custom logic for initial param validation
    pass
  def filteringLogic(self, movie):
    #custom logic for filtering using given parameter
    #must return bool
    pass

class YearFromFilter(BaseFilter):
  def validateParameter(self, parameter):
    self.param = int(parameter.get())
  def filteringLogic(self, movie):
    return True if int(movie['year']) >= self.param else False

class YearToFilter(BaseFilter):
  def validateParameter(self, parameter):
    self.param = int(parameter.get())
  def filteringLogic(self, movie):
    return True if int(movie['year']) <= self.param else False

class GenreFilter(BaseFilter):
  def validateParameter(self, parameter):
    #parameter is a dict: {'mode':IntVar, 'list':list}
    self.param = parameter['mode'].get()
    if self.param == 0:
      self.filter = self.filterAtLeast
    elif self.param == 1:
      self.filter = self.filterAll
    elif self.param == 2:
      self.filter = self.filterExactly
    else:
      self.param = None
    self.genres = parameter['list']
    if len(self.genres)==0:
      self.param = None
  def filterAtLeast(self, item):
    #at least one of given values
    for genre in self.genres:
      if genre in item['genres']:
        return True
    return False
  def filterAll(self, item):
    #all of the given values
    ok = True
    for genre in self.genres:
      if genre not in item['genres']:
        ok = False
        break
    return ok
  def filterExactly(self, item):
    #exactly the given values and none more
    return True if self.filterAll(item) and len(self.genres)==len(item['genres']) else False
  def filteringLogic(self, item):
    return self.filter(item)
