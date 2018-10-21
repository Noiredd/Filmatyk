from datetime import date

class Blueprint(object):
  @staticmethod
  def _default(x): return str(x)
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
      return str(x) + ' ' + ''.join('★' for i in range(v))
  @staticmethod
  def _favourite(x):
    return '♥' if x == 1 else ''

  def __init__(self, name:str, parsing:dict={}, display:dict={}, store=True):
    self.parsing_rule = parsing if parsing else None
    self.display_rule = display if display else self._default
    self.store = store
  def getParsing(self):
    return self.parsing_rule
  def getDisplay(self):
    return self.display_rule

class UserData(object):
  def __init__(self, data, parent):
    #"parent" is needed for setting attrs
    self.parent = parent
    self.rating = None
    self.wantto = None
    #"data" is used at deserialization
    if 'rating' in data.keys():
      self.addRating(data['rating'])
    if 'wannto' in data.keys():
      self.addRating(data['wantto'])
  def addRating(self, rating:dict):
    #trusts that these 4 keys will be provided: rating, comment, dateOf, faved
    self.rating = rating
    #set the parent's attrs to allow access
    for key, val in self.rating.items():
      self.parent.__dict__[key] = val
    #however, "dateOf" should be presented as a date
    dateOf = self.rating['dateOf']
    self.parent.__dict__['dateOf'] = date(
      year  = dateOf['y'],
      month = dateOf['m'],
      day   = dateOf['d']
    )
  def addWantTo(self, wantto):
    self.wantto = wantto
    #set the parent's attrs to allow access
    for key, val in self.wantto.items():
      self.parent.__dict__[key] = val
  def hasRating(self):
    return True if self.rating is not None else False
  def hasWantTo(self):
    return True if self.wantto is not None else False
  def serialize(self):
    #actually means "convert to dict", but whatever
    serial = {}
    if self.rating is not None:
      serial['rating'] = self.rating
    if self.wantto is not None:
      serial['rating'] = self.wantto
    return serial

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
  #rating and ID fields are special, will be parsed and stored differently
  id = Blueprint(
    name='ID',
    display=lambda x: x,
    store=False
  )
  rating = Blueprint(
    name='Ocena',
    display=Blueprint._rating,
    store=False
  )
  faved = Blueprint(
    name='Ulubione',
    display=Blueprint._favourite,
    store=False
  )
  dateOf = Blueprint(
    name='Data obejrzenia',
    store=False
  )
  comment = Blueprint(
    name='Komentarz',
    store=False
  )

  @classmethod
  def cacheBlueprints(cls):
    #cache those Blueprints that will be stored in dict during serialization
    #special ones are excluded, as the internal UserData obj will serialize them
    cls.properties = []
    for key, val in cls.__dict__.items():
      if type(val) is Blueprint and val.store:
        cls.properties.append(key)
  @classmethod
  def getDisplayRules(cls, prop):
    if prop in cls.__dict__.keys():
      return cls.__dict__[prop].getDisplay()
    else:
      #this shouldn't happen unless there is a bug somewhere
      return lambda x: x

  def __init__(self, userdata:dict={}, **properties):
    #if some of the properties haven't been parsed and passed, this will cause
    #problems in the future; some code to automatically fill with some default
    #value might be useful here
    for prop, val in properties.items():
      self.__dict__[prop] = val
    self.raw = RawAccess(self)
    #construct the UserData object for rating/wantto information
    self.userdata = UserData(userdata, self)
  def __getitem__(self, prop):
    if prop in self.__dict__.keys():
      val = self.__dict__[prop]
      dsp = self.getDisplayRules(prop)
      return dsp(val)
    else:
      return ''
  def addRating(self, rating):
    self.userdata.addRating(rating)
  def addWantTo(self, wantto):
    self.userdata.addWantTo(wantto)
  def asDict(self):
    #store all properties as dict, the exact reverse of __init__
    _dict = {}
    for prop in self.properties:
      if prop in self.__dict__.keys():
        _dict[prop] = self.__dict__[prop]
    #also store the userdata
    _dict['userdata'] = self.userdata.serialize()
    return _dict

Item.cacheBlueprints()
