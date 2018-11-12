from datetime import date

classByString = {}

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

  def __init__(self, name:str, colwidth:int, parsing:dict={}, display=None, store=True):
    self.display_name = name
    self.column_width = colwidth
    self.parsing_rule = parsing if parsing else None
    self.display_rule = display if display else self._default
    self.store = store
  def getParsing(self):
    return self.parsing_rule
  def getDisplay(self):
    return self.display_rule
  def getHeading(self):
    return self.display_name
  def getColWidth(self):
    return self.column_width

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
      self.parent.properties[key] = val
    #however, "dateOf" should be presented as a date
    dateOf = self.rating['dateOf']
    self.parent.properties['dateOf'] = date(
      year  = dateOf['y'],
      month = dateOf['m'],
      day   = dateOf['d']
    )
  def addWantTo(self, wantto):
    self.wantto = wantto
    #set the parent's attrs to allow access
    for key, val in self.wantto.items():
      self.parent.properties[key] = val
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

class BlueprintInheritance(type):
  """ This metaclass ensures that all classes derived from Item have proper
      access to all of the blueprints. Normally, iterating over cls.__dict__
      only yields variables directly belonging to the given cls, so NONE of
      the inherited class variables (including, most importantly, the most
      basic Blueprints) will be visible. Thus, caching Blueprints and getting
      presentation rules will not work in any derived classes, making them
      useless.
      The class constructor will perform all of said tasks (caching Blueprints,
      preparing a presentation rules dict) during construction of the derived
      classes, thus 1) enabling proper inheritance and 2) removing the need
      to call cls.cacheBlueprints after creating every class.
  """
  def __new__(cls, name, bases, dct):
    # Explicitly create the new class
    c = super(BlueprintInheritance, cls).__new__(cls, name, bases, dct)
    # Get all directly passed blueprints
    c.blueprints = {key: val for key, val in dct.items() if isinstance(val, Blueprint)}
    # Merge with the blueprints contained by the base classes
    for base in bases:
      for k, v in base.blueprints.items():
        # Allow overriding - only copy those which do not appear in base
        if k not in c.blueprints.keys():
          c.blueprints[k] = v
    # Keep track of the storable blueprints
    c.storables = [name for name, bp in c.blueprints.items() if bp.store]
    # Register the class
    classByString[name] = c
    # The new class is now ready
    return c

class Item(metaclass=BlueprintInheritance):
  TYPE_STRING = ''
  # Special ID field
  id = Blueprint(
    name='ID',
    colwidth=0
  )
  # General parsed fields
  title = Blueprint(
    name='Tytuł',
    colwidth=200,
    parsing={'tag':'h3', 'class':'filmPreview__title', 'text':True, 'list':False}
  )
  otitle = Blueprint(
    name='Tytuł oryginalny',
    colwidth=200,
    parsing={'tag':'div', 'class':'filmPreview__originalTitle', 'text':True, 'list':False}
  )
  year = Blueprint(
    name='Rok',
    colwidth=35,
    parsing={'tag':'span', 'class':'filmPreview__year', 'text':True, 'list':False}
  )
  link = Blueprint(
    name='URL',
    colwidth=200,
    parsing={'tag':'a', 'class':'filmPreview__link', 'text':False, 'attr':'href'}
  )
  imglink = Blueprint(
    name='ImgURL',
    colwidth=200,
    parsing={'tag':'img', 'class':'filmPoster__image', 'text':False, 'attr':'data-src'}
  )
  fwRating = Blueprint(
    name='Ocena FW',
    colwidth=50,
    parsing={'tag':'div', 'class':'filmPreview__rateBox', 'text':False, 'attr':'data-rate'},
    display=Blueprint._fwRating
  )
  plot = Blueprint(
    name='Zarys fabuły',
    colwidth=500,
    parsing={'tag':'div', 'class':'filmPreview__description', 'text':True, 'list':False}
  )
  genres = Blueprint(
    name='Gatunek',
    colwidth=200,
    parsing={'tag':'div', 'class':'filmPreview__info--genres', 'text':True, 'list':True},
    display=Blueprint._list
  )
  #rating fields are special, will be parsed and stored differently
  rating = Blueprint(
    name='Ocena',
    colwidth=150,
    display=Blueprint._rating,
    store=False
  )
  faved = Blueprint(
    name='Ulubione',
    colwidth=50,
    display=Blueprint._favourite,
    store=False
  )
  dateOf = Blueprint(
    name='Data obejrzenia',
    colwidth=100,
    store=False
  )
  comment = Blueprint(
    name='Komentarz',
    colwidth=500,
    store=False
  )

  def __init__(self, userdata:dict={}, **properties):
    self.properties = {}
    for prop, val in properties.items():
      # ignore any values that are not defined by the blueprints
      if prop in self.blueprints.keys():
        self.properties[prop] = val
    #construct the UserData object for rating/wantto information
    self.userdata = UserData(userdata, self)
  def __getitem__(self, prop):
    if prop in self.properties.keys():
      val = self.properties[prop]
      dsp = self.blueprints[prop].getDisplay()
      return dsp(val)
    else:
      return ''
  def getRawProperty(self, prop):
    if prop in self.properties.keys():
      return self.properties[prop]
    else:
      return ''
  def addRating(self, rating):
    self.userdata.addRating(rating)
  def addWantTo(self, wantto):
    self.userdata.addWantTo(wantto)
  def asDict(self):
    #store all properties as dict, the exact reverse of __init__
    _dict = {}
    for prop in self.storables:
      if prop in self.properties.keys():
        _dict[prop] = self.properties[prop]
    #also store the userdata
    _dict['userdata'] = self.userdata.serialize()
    return _dict

class Movie(Item):
  TYPE_STRING = 'FILM'
  duration = Blueprint(
    name='Długość',
    colwidth=50,
    parsing={'tag':'div', 'class':'filmPreview__filmTime', 'text':False, 'attr':'data-duration'},
    display=Blueprint._duration
  )
  countries = Blueprint(
    name='Kraj produkcji',
    colwidth=150,
    parsing={'tag':'div', 'class':'filmPreview__info--countries', 'text':True, 'list':True},
    display=Blueprint._list
  )
  directors = Blueprint(
    name='Reżyseria',
    colwidth=150,
    parsing={'tag':'div', 'class':'filmPreview__info--directors', 'text':True, 'list':True},
    display=Blueprint._list
  )
  cast = Blueprint(
    name='Obsada',
    colwidth=200,
    parsing={'tag':'div', 'class':'filmPreview__info--cast', 'text':True, 'list':True},
    display=Blueprint._list
  )

  def __init__(self, userdata:dict={}, **properties):
    super(Movie, self).__init__(userdata, **properties)
