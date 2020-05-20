import json
import os

import tkinter as tk
from tkinter import ttk


class Options():
  """Stores program options as named Tk variables, allowing easy serialization.

  Options wraps around a simple dict of Tk vars, which enables the following:
  * easy access to option values (using get),
  * simple binding of option variables to Tk widgets (using variable),
  * serialization and deserialization to JSON (using storeToString).
  Defining a new option is done simply by adding it to the prototypes list.
  """
  option_prototypes = [
  ]

  def __init__(self, json_string:str='{}'):
    self.variables = {}
    self.isDirty = False
    saved_values = json.loads(json_string)
    for name, vtype, default in self.option_prototypes:
      variable = vtype()
      value = saved_values[name] if name in saved_values.keys() else default
      variable.set(value)
      variable.trace('w', self.__touched_callback)
      self.variables[name] = variable

  def storeToString(self):
    """Serialize the options to a JSON string."""
    return json.dumps({
      name: variable.get() for name, variable in self.variables.items()
    })

  def get(self, name):
    """Get the value of a named option."""
    return self.variables[name].get()

  def variable(self, name):
    """Get Tk variable object of a named option."""
    return self.variables[name]

  def __touched_callback(self, *args):
    """Set the dirty flag whenever an option changes."""
    self.isDirty = True
