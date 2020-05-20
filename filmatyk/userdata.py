"""System for preserving backwards-compatibility for user data.

We store quite a lot of user data, and there's always only one right way to
write it to file. But when an update is released, we need to ensure that a new
version can read data stored by any previous version. Hence, this module stores
all prior loaders, binding them to their respective versions, so that we can
always read user data saved sometime in the past.

The mechanism relies on 3 classes:
* UserData defines the current representation of user data,
* DataManager provides a high-level interface for loading (any past format) and
  saving (current format) user data,
* Loaders stores all known loader functions together with version strings that
  indicate the earliest user data file version they are capable of reading.

The writing logic is simple: Main constructs the UserData object and puts there
all the user data serialized to strings, then calls DataManager to save that
object to a file. The save method writes a file in the current format.

Loading logic is a little more complicated, as it happens in two stages. First,
all the loaders for all previous versions of the program are prepared in an
OrderedDict. Second, Main requests the DataManager to load a given user data
file. DataManager reads the file and attempts to find a version string in its
data (on any failure it defaults to returning a default-constructed UserData
instance). When a version string is found, it finds the first loader capable of
reading it, and passes the file contents to that function, which constructs a
UserData instance and fills it with data. This function is responsible for
translation of the old data format (as seen in the file) to the current format
(as required by UserData and thus Main).

If a new version changes the UserData layout, the DataManager.save method must
be updated to reflect that. Additionally, all previously registered loaders
must be able to return the new object. When adding a new element to UserData,
it should go without problems (just provide a default argument), but if a new
layout removes some fields... this will need special handling - probably for
*all* legacy loaders.
"""

import os
from collections import OrderedDict
from semantic_version import Version


class UserData(object):
  """User data wrapper with simple semantics (simpler than a dict)."""
  def __init__(
    self,
    username='',
    movies_conf='',
    movies_data='',
    series_conf='',
    series_data='',
    games_conf='',
    games_data='',
    options_json='{}',
    is_empty=True
  ):
    self.username = username
    self.movies_conf = movies_conf
    self.movies_data = movies_data
    self.series_conf = series_conf
    self.series_data = series_data
    self.games_conf = games_conf
    self.games_data = games_data
    self.options_json = options_json
    self.is_empty = is_empty


class DataManager(object):
  """Backwards-compatibility preserving interface for user data management.

  Loaders should put themselves in the "loaders" list as tuples:
    (callable, version)
  so that we can construct an OrderedDict from them at init. The class method
  registerLoaderSince does it automatically and is designed to be used as a
  decorator around a loader.
  """
  all_loaders = []

  def __init__(self, userDataPath:str, version:str):
    self.path = userDataPath
    self.version = version
    self.loaders = self.__orderLoaders()

  def __orderLoaders(self):
    """Create an OrderedDict of loaders, ordered by version strings."""
    ordered_loaders = OrderedDict()
    # Sort by version
    self.all_loaders.sort(key=lambda x: x[1])
    for loader, version in self.all_loaders:
      ordered_loaders[version] = loader
    return ordered_loaders

  def save(self, userData):
    """Save the user data in the most recent format."""
    # Safety feature against failing to write new data and removing the old
    if os.path.exists(self.path):
      os.rename(self.path, self.path + '.bak')
    # Now actually write data to disk
    with open(self.path, 'w') as user_file:
      user_file.write('#VERSION\n')
      user_file.write(self.version + '\n')
      user_file.write('#USERNAME\n')
      user_file.write(userData.username + '\n')
      user_file.write('#OPTIONS\n')
      user_file.write(userData.options_json + '\n')
      user_file.write('#MOVIES\n')
      user_file.write(userData.movies_conf + '\n')
      user_file.write(userData.movies_data + '\n')
      user_file.write('#SERIES\n')
      user_file.write(userData.series_conf + '\n')
      user_file.write(userData.series_data + '\n')
      user_file.write('#GAMES\n')
      user_file.write(userData.games_conf + '\n')
      user_file.write(userData.games_data + '\n')
    # If there were no errors at point, new data has been successfully written
    if os.path.exists(self.path + '.bak'):
      os.remove(self.path + '.bak')

  def load(self):
    """Load user data from a file, with backwards-compatibility.

    Always returns a current format UserData, either with the content upgraded
    from a legacy format, or a default-constructed instance in case of failure.
    """
    # Check if the file exists
    if not os.path.exists(self.path):
      return UserData()
    # Read data and attempt to locate the version string
    user_data = self.readFile()
    data_version = self.checkVersion(user_data)
    if not data_version:
      return UserData()
    # Attempt to match loader to that string
    loader = self.selectLoader(data_version)
    if not loader:
      return UserData()
    # Attempt to parse the user data using that loader
    try:
      parsed_data = loader(user_data)
    except:
      print("User data parsing error.")
      return UserData()
    # If we got this far, mark the UserData object as successfully loaded.
    # This flag is used by Main to determine whether the program is being ran
    # for the first time.
    parsed_data.is_empty = False
    return parsed_data

  def readFile(self):
    """Simply read lines from the user data file.

    This always has to be done first (independent of the actual content), as
    the version string must be extracted before doing anything further.
    Lines starting with '#' are always ignored as comments.
    """
    with open(self.path, 'r') as user_file:
      user_data = [
        line.strip('\n')
        for line in user_file.readlines()
        if not line.startswith('#')
      ]
    return user_data

  def checkVersion(self, data):
    """Try to find a version string in the user data robustly."""
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
    # If no version string is present
    return None

  def selectLoader(self, data_version):
    """Select the loader that matches the version of the given user data file.

    Iterate over registered loaders for as long as the data version is more
    recent than the loader. This will stop when a loader version is too new
    for the data. The previous (matching) loader will be returned.
    """
    matching_loader = None
    for loader_version, loader in self.loaders.items():
      if data_version >= loader_version:
        matching_loader = loader
      else:
        break
    return matching_loader

  def registerLoaderSince(version:str):
    """Add the given loader to the loaders list."""
    version = Version(version)
    def decorator(loader):
      DataManager.all_loaders.append((loader, version))
      return loader
    return decorator


class Loaders(object):
  """Just a holder for different data loading functions.

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

  @DataManager.registerLoaderSince('1.0.0-beta.4')
  def loader100b4(user_data):
    return UserData(
      username=user_data[1],
      options_json=user_data[2],
      movies_conf=user_data[3],
      movies_data=user_data[4],
      series_conf=user_data[5],
      series_data=user_data[6],
      games_conf=user_data[7],
      games_data=user_data[8],
    )
