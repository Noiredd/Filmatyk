import json
import os
from math import ceil

import containers
from filmweb import ConnectionError, FilmwebAPI


class Database(object):
  def __init__(self, itemtype:str, api:FilmwebAPI, callback:callable):
    self.itemtype = itemtype
    self.callback = callback
    self.items = []
    self.ids = set() # TODO: optimize using cached IDs
    self.api = api
    self.isDirty = False # are there any changes that need to be saved?

  # INTERFACE
  def getItems(self):
    return self.items.copy()

  def getItemByID(self, id:int):
    for item in self.items:
      if item.getRawProperty('id') == id:
        return item
    return None

  def __iter__(self):
    return self.items.__iter__()

  # Serialization-deserialization
  @staticmethod
  def restoreFromString(itemtype:str, string:str, api:FilmwebAPI, callback:callable):
    newDatabase = Database(itemtype, api, callback)
    if not string:
      # simply return a raw, empty DB
      return newDatabase
    listOfDicts = json.loads(string)
    itemclass = containers.classByString[itemtype]
    newDatabase.items = [itemclass(**dct) for dct in listOfDicts]
    return newDatabase

  def storeToString(self):
    return json.dumps([item.asDict() for item in self.items])

  # Data acquisition
  def softUpdate(self):
    """Quickly pull the most recent changes from Filmweb.

    The algorithm allows detecting additions and removals of items by comparing
    the total item count in the local and remote databases and keeping track of
    the items that differ between the two.
    There are two fundamental problems that it solves are related to the fact
    that getting to know the full state of the remote database is a very time-
    consuming operation (it can only be fetched in chunks of n items, usually
    n=25). Therefore the first problem is to determine how many pages to read
    from the remote database. The second problem is related to detecting when
    an item has been deleted remotely.
    The solution can be described in the following * steps:
    * compare the item counts between the databases - an update is to be made
      only if there is a difference,
    * fetch a new chunk of the remote database (a page),
    * detect which items have been added or changed with respect to the local
      (this makes use of a special HashedItem class, see its docs for details),
    * identify the last non-changed remote item and find its local counterpart,
    * split the local database into two parts:
      * a "changed" part comprises all items up to and including this last non-
        changed item - all these items are a potentially obsolete state of the
        database, and they could be simply replaced with the currently held
        remote items,
      * an "unchanged" part comprises all other items - nothing about their
        remote counterparts is known at this time.
    * check whether merging the currently held remote items with the possibly
      up-to-date unchanged part of the local database can satisfy the general
      condition (that the local and remote databases should count the same).
    At some point either the counts will even out, or all of the remote items
    will be loaded. In either case the update completes.

    The problem this algorithm solves has one special form that is impossible
    to overcome: when a symmetric change has occurred past a certain page. In
    this case, any count-based algorithm will stop at the first chance it can
    get (when it notices a count balance), ignoring any additions and removals
    that may happen on further pages, if they balance out.
    Example:
      total change: length += 3
      page 1: 4 additions, 1 removal
      page 2: 1 addition, 1 removal
    The algorithm will reach balance after page 1 and not move on to page 2.

    Returns True in case of success, False if it aborted before completion.
    """
    # Display the progress bar
    self.callback(0)
    # Ask the API how many items should there be (abort on network problems)
    try:
      num_request = self.api.getNumOf(self.itemtype)
    except ConnectionError:
      self.callback(-1, abort=True)
      return False
    # Exit if the user failed to log in
    if num_request is None:
      self.callback(-1, abort=True)
      return False
    # Workload estimation
    local_count = len(self.items)
    remote_count, items_per_page = num_request
    still_need = remote_count - local_count
    # Exit if nothing to download
    if not remote_count or not items_per_page or not still_need:
      self.callback(-1)
      return False
    # Convert the existing database to a hashed format
    local_hashed = list(HashedItem(item) for item in self.items)
    local_hashed_dict = {item.id: item for item in local_hashed}
    # Prepare to and run the main loop
    remote_page_no = 0
    remote_items = []
    local_changed = []
    local_unchanged = []
    while still_need:
      # Fetch a page and represent it in the hashed form
      remote_page_no += 1
      fetched_items = list(
        HashedItem(item) for item in
        self.api.getItemsPage(self.itemtype, page=remote_page_no)
      )
      # Detect additions and changes among the new items
      for item in fetched_items:
        local_item = local_hashed_dict.get(item.id, None)
        # If this ID was not among known items - it's a simple addition
        if not local_item:
          item.added = True
          item.changed = True
        else:
          # If it was, check if the data differs to detect a change
          item.added = False
          item.changed = item.hash != local_item.hash
          # Store its local counterpart for a safe update
          item.local_item = local_item
      # Join the new items with the previously acquired but unprocessed ones
      remote_items.extend(fetched_items)
      # One edge case is that all of the remote items have been just acquired.
      # This would happen when updating the Database for the first time.
      if len(remote_items) == remote_count:
        local_changed = local_hashed
        local_unchanged = []
        break
      # If the last remote item has been changed, it is difficult to figure out
      # how do the currently known remote items relate to the local database.
      # In such a case, another page is fetched, allowing a better view.
      if remote_items[-1].changed:
        continue
      # Otherwise, locate the item in the local Database and split it.
      last_unchanged_pos = local_hashed.index(remote_items[-1].id) + 1
      local_changed = local_hashed[:last_unchanged_pos]
      local_unchanged = local_hashed[last_unchanged_pos:]
      # Check if the databases would balance out if they were merged right now.
      still_need = remote_count - (len(remote_items) + len(local_unchanged))
    # At this point the database can be reconstructed from the two components.
    new_items = []
    # First, incorporate the changes from the remotely acquired items
    for item in remote_items:
      # If the item had a local counterpart, do not throw it away but instead
      # update it with the remotely acquired data (allows preserving any local
      # data that might not originate at the remote database).
      if item.local_item:
        local_item = item.local_item.parent
        local_item.update(item.parent)
        new_items.append(local_item)
      else:
        new_items.append(item.parent)
    # Then add the rest of unchanged items.
    new_items.extend(item.parent for item in local_unchanged)
    self.items = new_items
    # Finalize - notify the GUI and potential caller.
    self.callback(-1)
    self.isDirty = True
    return True

  def hardUpdate(self):
    """Drop all the Items and reload all the data.

    This uses softUpdate under the hood. In case of its failure, no data is
    lost as everything is backed up first.
    """
    old_items = self.items
    self.items = []
    if not self.softUpdate():
      self.items = old_items


class HashedItem():
  """A hashed representation of an Item that allows detecting changes.

  Computing a standard hash of the Item's UserData makes it possible to detect
  when an Item was not just added or removed but also whether it has changed
  with respect to the locally stored version of that Item.
  Flags indicating whether an item was added or changed are helpful in the
  process of performing an update.

  In theory, the Item class itself could implement the hashing functionality,
  but doing this in a separate technical class also allows storing the flags,
  which would only clutter the base class.

  Some caveats:
  * HashedItem also maintains a reference to the original item that it has been
    created from. This is convenient during the update operation, as it allows
    operating directly on the list of HashedItems instead of having to ensure
    that each list-changing operation happens both on the list of hashes and
    the list of the original items.
  * When used to hash a remotely acquired item, the corresponding local version
    of that item can be attached to the HashedItem. This saves an additional
    search operation later in the update process.
  * HashedItem can be equality-compared with not only instances of the same
    type, but also ints. This makes it possible to search for an integer ID in
    a list of HashedItems.
  """
  hash_data = ['rating', 'comment', 'dateOf']

  def __init__(self, item:containers.Item):
    self.parent = item
    self.id = item.getRawProperty('id')
    self.hash = self.computeHash(item)
    # Flags used to compare remote items with the local ones
    self.added = None
    self.changed = None
    self.local_item = None

  def computeHash(self, item:containers.Item):
    """Summarize UserData of an Item by a simple hash function."""
    userDataString = '#'.join(item[prop] for prop in self.hash_data)
    return hash(userDataString)

  def __eq__(self, other):
    if isinstance(other, int):
      return self.id == other
    else:
      return super(HashedItem, self).__eq__(other)
