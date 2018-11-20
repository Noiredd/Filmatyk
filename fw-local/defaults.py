from collections import OrderedDict

DEFAULT_CONFIGS = {
  'Movie': OrderedDict(
    title   = None,
    year    = None,
    genres  = None,
    dateOf  = None,
    rating  = None
  )
}
DEFAULT_SORTING = {
  'Movie': ('dateOf', False) # column name, ascending
}
