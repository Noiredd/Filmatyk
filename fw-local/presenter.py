import tkinter as tk
from tkinter import ttk


class Presenter(object):
  """ TODO MAJOR
      3. GUI stores the savefile by serializing Presenter and Database separately
      4. Presenter retrieves objects from DB and only displays selected attrs
      5. Presenter is semi-configurable (i.e. stores and restores column config,
         but without GUI window for controlling it)
      6. Presenter only has a handle to the Database which is instantiated by the
         GUI, and a switch whether to display ratings or want-tos', as well as a
         flag whether to allow database updates (so that the unified underlying
         database wasn't updated twice)
      7. GUI calls update on Presenter, which calls DB
      7. Session management - API is constructed immediately, but only asks for
         login (GUI callback) when executing commands that need a session
      9. Presenter handles sorting and preview callbacks
  """
  def __init__(self, root, api, database, username:str, displayRating=True, allowUpdate=True):
    self.root = root
    self.main = tk.Frame(root)
    self.database = database
    self.constructTreeView()
    # LEGACY: config
    self.config = [
      ('title', None),
      ('year', None),
      ('rating', None)
    ]

  def constructTreeView(self):
    # TODO: column display configuration
    self.tree = tree = ttk.Treeview(
      self.main,
      height=32,
      selectmode='none',
      columns=['id', 'title', 'year', 'rating']
    )
    tree['displaycolumns'] = [c for c in tree['columns'] if c not in ['#0', 'id']]
    # TODO: column headings
    # TODO: column width configuration
    # TODO: sorting and preview spawn callbacks
    tree.grid(row=0, column=0)
    yScroll = ttk.Scrollbar(self.main, command=tree.yview)
    yScroll.grid(row=0, column=1, sticky=tk.NS)
    # TODO: column width and x-scrolling
    tree.configure(yscrollcommand=yScroll.set)#, xscrollcommand=xScroll.set)

  # TK interface for GUI placement
  def pack(self, **kw):
    self.main.pack(**kw)
  def grid(self, **kw):
    self.main.grid(**kw)
