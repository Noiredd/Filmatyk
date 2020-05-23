"""Options is a globally accessible class holding all program options.

The only exported object is a singleton instance of the Options class. Usage:
  from options import Options
The instance has to be initialized (by passing a JSON string with serialized
initial values) or at least confirmed on assuming default values:
  Options.init(json_string)
After that - and ONLY after that - it can be used in two ways.
Access to an option value:
  Options.get('option_name')
Direct access to the underlying TkVar:
  Options.var('option_name')

This gives a convenient access to options from wherever in the program,
assuming the actual call to get or var happens AFTER the initialization of the
instance.
"""

import json
import os

import tkinter as tk
from tkinter import ttk


class _Options():
  """Stores program options as named Tk variables, allowing easy serialization.

  Options wraps around a simple dict of Tk vars, which enables the following:
  * easy access to option values (using get),
  * simple binding of option variables to Tk widgets (using var),
  * serialization and deserialization to JSON (using storeToString).
  Defining a new option is done simply by adding it to the prototypes list.
  """
  option_prototypes = [
    ('rememberLogin', tk.BooleanVar, True),
  ]

  def __init__(self):
    self.variables = {}
    self.isDirty = False
    self.isInit = False

  def init(self, json_string:str='{}'):
    """Restore the JSON-serialized values."""
    saved_values = json.loads(json_string)
    for name, vtype, default in self.option_prototypes:
      variable = vtype()
      value = saved_values[name] if name in saved_values.keys() else default
      variable.set(value)
      variable.trace('w', self.__touched_callback)
      self.variables[name] = variable
    self.isInit = True

  def storeToString(self):
    """Serialize the options to a JSON string."""
    return json.dumps({
      name: variable.get() for name, variable in self.variables.items()
    })

  def get(self, name):
    """Get the value of a named option."""
    if not self.isInit:
      raise AttributeError
    return self.variables[name].get()

  def var(self, name):
    """Get Tk variable object of a named option."""
    if not self.isInit:
      raise AttributeError
    return self.variables[name]

  def __touched_callback(self, *args):
    """Set the dirty flag whenever an option changes."""
    self.isDirty = True


Options = _Options()
