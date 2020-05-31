from __future__ import annotations
from datetime import date

# This is a globally used dict that binds Item classes to their names.
# It should remain empty, as the classes register themselves here.
classByString = {}


class Blueprint(object):
  """Blueprint is an abstraction of a property that an Item might have.

  Each property is a named piece of information that can be:
  * acquired,
  * stored,
  * and presented
  in a specific way, and is bound to the Item class.
  Blueprint defines acquisition (i.e. how to extract it from Filmweb HTML) and
  presentation (how to render it into presentable text) for that piece of
  information.

  Attributes:
  * display_name: str, presentable name of the property (used to name column
    headers in the Presenter)
  * column_width: int, default width of a Presenter column,
  * parsing_rule: dict, parsing rules for acquiring that property, for details
    see filmweb.py and read ../readme/HOWITWORKS.md,
  * display_rule: callable or None, (optional) function to convert raw property
    into a string representation,
  * store: bool, should that property be included when serializing a containing
    instance.

  Static methods define some basic, commonly used presentation functions for
  known types of properties.
  """

  # Presentation styling callables

  @staticmethod
  def _default(x): return str(x)

  @staticmethod
  def _list(x): return ', '.join(x)

  @staticmethod
  def _duration(x):
    h = x // 60
    m = x % 60
    return '{0!s}h {1!s}m'.format(h, m)

  @staticmethod
  def _fwRating(x):
    return str(round(x, 1))

  @staticmethod
  def _rating(x):
    if x == 0:
      return '-'
    else:
      return str(x) + ' ' + ''.join('★' for i in range(x))

  @staticmethod
  def _favourite(x):
    return '♥' if x == 1 else ' '

  # Functionality

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
  """Encapsulates user information associated with each Item instance.

  Works by holding a reference to the owning Item and modifying its attributes.
  """
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
    """Add rating information from a properly formatted dict.

    This trusts that the following 4 keys will be provided:
    * rating
    * comment
    * dateOf
    * faved
    and modifies the owner.
    """
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
    """Add want-to-see information. Currently not used."""
    self.wantto = wantto
    #set the parent's attrs to allow access
    for key, val in self.wantto.items():
      self.parent.properties[key] = val

  def hasRating(self):
    return True if self.rating is not None else False

  def hasWantTo(self):
    return True if self.wantto is not None else False

  def serialize(self):
    """Converts self into a compact dict representation.

    If:
      s = x.serialize()
      y = UserData(s, x.parent)
    then
      x == y
    shall always be true.
    """
    serial = {}
    if self.rating is not None:
      serial['rating'] = self.rating
    if self.wantto is not None:
      serial['rating'] = self.wantto
    return serial


class BlueprintInheritance(type):
  """Changes the way inheritance works for Blueprints. Crucial for Item class.

  This metaclass ensures that all classes derived from Item have proper access
  to all of the blueprints. Normally, iterating over cls.__dict__ only yields
  variables directly belonging to the given cls, so NONE of the inherited class
  variables (including, most importantly, the most basic Blueprints) will be
  visible. Thus, caching Blueprints and getting presentation rules will not
  work in any derived classes, making them useless.
  The class constructor will perform all of said tasks (caching Blueprints,
  preparing a presentation rules dict) during construction of the derived
  classes, thus 1) enabling proper inheritance and 2) removing the need to call
  cls.cacheBlueprints after creating every class.
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
  """Base for all types of records used by Filmweb and in the program.

  Item has a dual use: one as a class itself, another as an instance.
  As a class, Item consists of a set of Blueprint instances, bound to it as
  class attributes. These are used by the API to construct effective parsing
  rules for each property (Blueprint) - see filmweb.py/FilmwebAPI.parseOne()
  As an instance, Item is a collection of property data, stored as a dict
  (self.properties) in which Blueprint attribute names serve as keys. This
  allows easy extraction of actual data by names in two ways:
  * by calling item['property'], which returns property data formatted into its
    display format as defined by the corresponding Blueprint,
  * by calling item.getRawProperty('property'), which returns the raw property.

  Each Item instance can be "serialized" into a dict representation. Here, if:
    x: Item
    d = x.asDict()
    y = Item(**d)
  then it shall always be true that:
    x == y

  Special kind of non-storable properties is defined to allow separate
  serialization of some properties, in this case the user data.

  IMPORTANT: the Item class itself is never used directly (although it might).
  Only its descendants, implementing specific details for each concrete type,
  are ever used in the program.
  """
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
    parsing={'tag':'h2', 'class':'filmPreview__title', 'text':True, 'list':False}
  )
  otitle = Blueprint(
    name='Tytuł oryginalny',
    colwidth=200,
    parsing={'tag':'div', 'class':'filmPreview__originalTitle', 'text':True, 'list':False}
  )
  year = Blueprint(
    name='Rok',
    colwidth=35,
    parsing={'tag':'div', 'class':'filmPreview__year', 'text':True, 'list':False, 'type':int}
  )
  link = Blueprint(
    name='URL',
    colwidth=200,
    parsing={'tag':'a', 'class':'filmPreview__link', 'text':False, 'attr':'href'}
  )
  imglink = Blueprint(
    name='ImgURL',
    colwidth=200,
    parsing={'tag':'div', 'class':'poster--auto', 'text':False, 'attr':'data-image'}
  )
  fwRating = Blueprint(
    name='Oc. FW',
    colwidth=50,
    parsing={'tag':'div', 'class':'filmPreview__rateBox', 'text':False, 'attr':'data-rate', 'type':float},
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
  # Rating fields are special, will be parsed and stored differently.
  rating = Blueprint(
    name='Moja ocena',
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
    """Return a properly formatted value of a requested property."""
    if prop in self.properties.keys():
      val = self.properties[prop]
      dsp = self.blueprints[prop].getDisplay()
      return dsp(val)
    else:
      return ''

  def getRawProperty(self, prop):
    """Return raw data of a requested property."""
    if prop in self.properties.keys():
      return self.properties[prop]
    else:
      return ''

  def addRating(self, rating):
    self.userdata.addRating(rating)

  def addWantTo(self, wantto):
    self.userdata.addWantTo(wantto)

  def asDict(self):
    """Store all properties as dict, the exact reverse of __init__."""
    _dict = {}
    for prop in self.storables:
      if prop in self.properties.keys():
        _dict[prop] = self.properties[prop]
    # Serialize the userdata separately.
    _dict['userdata'] = self.userdata.serialize()
    return _dict

  def update(self, other:Item):
    """Update own properties from another Item.

    This is useful if the Item's Blueprinted properties have been altered (e.g.
    because the remote data was updated) but there is also some custom data
    attached to the Item that should not be removed.

    Important note: currently there are no properties requiring this behavior.
    """
    for prop in self.storables:
      if prop in other.properties.keys():
        self.properties[prop] = other.properties[prop]
    self.userdata.addRating(other.userdata.rating)


class Movie(Item):
  """Item subclass specialized to hold Movie instances."""
  TYPE_STRING = 'FILM'
  duration = Blueprint(
    name='Długość',
    colwidth=50,
    parsing={'tag':'div', 'class':'filmPreview__filmTime', 'text':False, 'attr':'data-duration', 'type':int},
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


class Series(Movie):
  """Item subclass specialized to hold Series instances.

  Everything is the same as with movies, except the duration field which has a
  different meaning and thus can be named clearer.
  """
  TYPE_STRING = 'SERIAL'
  duration = Blueprint(
    name='Dł. odc.',
    colwidth=50,
    parsing={'tag':'div', 'class':'filmPreview__filmTime', 'text':False, 'attr':'data-duration', 'type':int},
    display=Blueprint._duration
  )

  def __init__(self, userdata:dict={}, **properties):
    super(Series, self).__init__(userdata, **properties)


class Game(Item):
  """Item subclass specialized to hold Game instances.

  Raw HTML representations of Games also have a countries div, but it has never
  been observed to contain any data.
  """
  TYPE_STRING = 'GRA'
  developers = Blueprint(
    name='Deweloper',
    colwidth=150,
    parsing={'tag':'div', 'class':'filmPreview__info--developers', 'text':True, 'list':True},
    display=Blueprint._list
  )
  publishers = Blueprint(
    name='Wydawca',
    colwidth=150,
    parsing={'tag':'div', 'class':'filmPreview__info--publishers', 'text':True, 'list':True},
    display=Blueprint._list
  )
  platforms = Blueprint(
    name='Platformy',
    colwidth=100,
    parsing={'tag':'div', 'class':'filmPreview__info--platforms', 'text':True, 'list':True},
    display=Blueprint._list
  )

  def __init__(self, userdata:dict={}, **properties):
    super(Game, self).__init__(userdata, **properties)
