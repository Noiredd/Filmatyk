import tkinter as tk
from tkinter import ttk

import database2 as db

class Presenter(object):
  """ TODO MAJOR
      1. Disable gui.py drawing so that the program starts using Presenter
      2. GUI creates a hacked API object and instantiates Presenter with it
      3. GUI stores the savefile by serializing Presenter (Presenter serializes
         the database and is able to either restore it from string, or recreate)
      4. Presenter retrieves objects from DB and only displays selected attrs
      5. Presenter is semi-configurable (i.e. stores and restores column config,
         but without GUI window for controlling it)
      6. Presenter handles sorting and preview callbacks
  """
  def __init__(self, root, api, itemclass, username:str, dbstring:str=''):
    self.root = root
    self.main = tk.Frame(root)
    self.database = db.Database.restoreFromString(username, itemclass, dbstring, api)
    self.constructTreeView()
    # LEGACY: config
    self.config = [
      ('title', None),
      ('year', None),
      ('rating', None)
    ]

  def constructTreeView(self):
    wrap = tk.Frame(self.root)
    # TODO: column display configuration
    self.tree = tree = ttk.Treeview(
      wrap,
      height=32,
      selectmode='none',
      columns=['id', 'title', 'year', 'rating']
    )
    tree['displaycolumns'] = [c for c in tree['columns'] if c not in ['#0', 'id']]
    # TODO: column headings
    # TODO: column width configuration
    # TODO: sorting and preview spawn callbacks
    tree.grid(row=0, column=0)
    yScroll = ttk.Scrollbar(wrap, command=tree.yview)
    yScroll.grid(row=0, column=1, sticky=tk.NS)
    # TODO: column width and x-scrolling
    tree.configure(yscrollcommand=yScroll.set)#, xscrollcommand=xScroll.set)
    wrap.grid(row=0, column=0, rowspan=2, padx=5, pady=5, sticky=tk.NW)

  # TK interface for GUI placement
  def pack(self, **kw):
    self.main.pack(**kw)
  def grid(self, **kw):
    self.main.grid(**kw)
