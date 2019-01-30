import os
from collections import OrderedDict
from semantic_version import Version

class UserData(object):
  """ User data wrapper with simple semantics (simpler than a dict). """
  def __init__(
    self,
    username='',
    movies_conf='',
    movies_data='',
    series_conf='',
    series_data='',
    games_conf='',
    games_data=''
  ):
    self.username = username
    self.movies_conf = movies_conf
    self.movies_data = movies_data
    self.series_conf = series_conf
    self.series_data = series_data
    self.games_conf = games_conf
    self.games_data = games_data

class DataManager(object):
  """ Backwards-compatibility preserving interface for user data management. """
  loaders = OrderedDict()

  def __init__(self, userDataPath:str):
    self.path = userDataPath

  def load(self):
    if not os.path.exists(self.path):
      return UserData() # default constructor is empty
    user_data = self.__readFile()
    data_version = self.__checkVersion(user_data)
    loader = self.__selectLoader(data_version)
    try:
      parsed_data = loader(user_data)
    except:
      print("User data parsing error.")
      exit()
    return parsed_data
  def __readFile(self):
    with open(self.path, 'r') as user_file:
      user_data = [
        line.strip('\n')
        for line in user_file.readlines()
        if not line.startswith('#')
      ]
    return user_data
  def __checkVersion(self, data):
    """ Tries to find a version string in the user data robustly. """
    for datum in data:
      # Don't expect version strings larger than that (most likely data)
      if len(datum) > 20:
        continue
      # Try to make a semantic version out of this
      try:
        version = Version(datum)
      except:
        continue
      else:
        return version
  def __selectLoader(self, version):
    """ Iterate over registered loaders for as long as the data version is more
        recent than the loader. This will stop when a loader version is too new
        for the data. The previous (matching) lodaer will be returned.
    """
    loader = None
    for v, p in self.loaders.items():
      if version >= v:
        loader = p
      else:
        break
    return loader

  @classmethod
  def registerLoader(self, loader, version):
    """ Add a new loader to the ODict, resorting for easy version matching. """
    # Get the existing loaders and their corresponding version numbers
    versions = list(self.loaders.keys())
    loaders = list(self.loaders.values())
    # Add the new one
    versions.append(version)
    loaders.append(loader)
    # Reconstruct the ODict with new version&loader in the correct order
    self.loaders.clear()
    for v, p in sorted(zip(versions, loaders), key=lambda x: x[0]):
      self.loaders[v] = p
  def registerLoaderSince(version:str):
    version = Version(version)
    def decorator(loader):
      DataManager.registerLoader(loader, version)
      return loader
    return decorator

class Loaders(object):
  """ Just a holder for different data loading functions.
  
      It's friends with DataManager class, that is: updates its "loaders" ODict
      with any loader defined here.
  """
  @DataManager.registerLoaderSince('1.0.0-beta.1')
  def loader100b(user_data):
    return UserData(
      username=user_data[1],
      movies_conf=user_data[2],
      movies_data=user_data[3],
      series_conf=user_data[4],
      series_data=user_data[5],
      games_conf=user_data[6],
      games_data=user_data[7]
    )
