class Blueprint(object):
  @staticmethod
  def _default(x): return x
  @staticmethod
  def _list(x): return ', '.join(x)
  @staticmethod
  def _duration(x):
    v = int(x)
    h = v // 60
    m = v % 60
    return '{0!s}h {1!s}m'.format(h, m)
  @staticmethod
  def _fwRating(x):
    return str(round(float(x), 1))
  @staticmethod
  def _rating(x):
    v = int(x)
    if v == 0:
      return '-'
    else:
      return x + ' ' + ''.join('★' for i in range(v))
  @staticmethod
  def _favourite(x):
    return '♥' if x == 1 else ''

  def __init__(self, name:str, parsing:dict={}, display:dict={}):
    self.parsing_rule = parsing if parsing else None
    self.display_rule = display if display else self._default
  def getParsing(self):
    return self.parsing_rule
  def getDisplay(self):
    return self.display_rule

class RawAccess(object):
  #allows access to raw values of properties
  # "Item.title"        requires the caller to have the prop name hard-coded
  # "Item['title']"     returns formatted value
  # "Item.raw['title']" returns raw value of the same attribute
  def __init__(self, parent):
    self.parent = parent  #store where do values come from
  def __getitem__(self, prop):
    if prop in self.parent.__dict__.keys():
      return self.parent.__dict__[prop]
    else:
      return '' #still don't know what to do with possible missing props

class Item(object):
  title = Blueprint(
    name='Tytuł',
    parsing={'tag':'h3', 'class':'filmPreview__title', 'text':True, 'list':False}
  )
  otitle = Blueprint(
    name='Tytuł oryginalny',
    parsing={'tag':'div', 'class':'filmPreview__originalTitle', 'text':True, 'list':False}
  )
  year = Blueprint(
    name='Rok',
    parsing={'tag':'span', 'class':'filmPreview__year', 'text':True, 'list':False}
  )
  link = Blueprint(
    name='URL',
    parsing={'tag':'a', 'class':'filmPreview__link', 'text':False, 'attr':'href'}
  )
  imglink = Blueprint(
    name='ImgURL',
    parsing={'tag':'img', 'class':'filmPoster__image', 'text':False, 'attr':'data-src'}
  )
  duration = Blueprint(
    name='Długość',
    parsing={'tag':'div', 'class':'filmPreview__filmTime', 'text':False, 'attr':'data-duration'},
    display=Blueprint._duration
  )
  fwRating = Blueprint(
    name='Ocena FW',
    parsing={'tag':'div', 'class':'filmPreview__rateBox', 'text':False, 'attr':'data-rate'},
    display=Blueprint._fwRating
  )
  plot = Blueprint(
    name='Zarys fabuły',
    parsing={'tag':'div', 'class':'filmPreview__description', 'text':True, 'list':False}
  )
  genres = Blueprint(
    name='Gatunek',
    parsing={'tag':'div', 'class':'filmPreview__info--genres', 'text':True, 'list':True},
    display=Blueprint._list
  )
  countries = Blueprint(
    name='Kraj produkcji',
    parsing={'tag':'div', 'class':'filmPreview__info--countries', 'text':True, 'list':True},
    display=Blueprint._list
  )
  directors = Blueprint(
    name='Reżyseria',
    parsing={'tag':'div', 'class':'filmPreview__info--directors', 'text':True, 'list':True},
    display=Blueprint._list
  )
  cast = Blueprint(
    name='Obsada',
    parsing={'tag':'div', 'class':'filmPreview__info--cast', 'text':True, 'list':True},
    display=Blueprint._list
  )
  #rating and ID fields are special, will be parsed differently
  id = Blueprint(
    name='ID'
  )
  rating = Blueprint(
    name='Ocena',
    display=Blueprint._rating
  )
  favourite = Blueprint(
    name='Ulubione',
    display=Blueprint._favourite
  )
  timeSeen = Blueprint(
    name='Data obejrzenia'
  )
  comment = Blueprint(
    name='Komentarz'
  )

  @classmethod
  def cacheBlueprints(cls):
    properties = []
    for key, val in cls.__dict__.items():
      if type(val) is Blueprint:
        properties.append(key)
    cls.properties = properties
  @classmethod
  def getDisplayRules(cls, prop):
    if prop in cls.__dict__.keys():
      return cls.__dict__[prop].getDisplay()
    else:
      #this shouldn't happen unless there is a bug somewhere
      return lambda x: x

  def __init__(self, **properties):
    #if some of the properties haven't been parsed and passed, this will cause
    #problems in the future; some code to automatically fill with some default
    #value might be useful here
    for prop, val in properties.items():
      self.__dict__[prop] = val
    self.raw = RawAccess(self)
  def __getitem__(self, prop):
    if prop in self.__dict__.keys():
      val = self.__dict__[prop]
      dsp = self.getDisplayRules(prop)
      return dsp(val)
    else:
      return ''
  def asDict(self):
    _dict = {}
    for prop in self.properties:
      if prop in self.__dict__.keys():
        _dict[prop] = self.__dict__[prop]
    return _dict

Item.cacheBlueprints()
