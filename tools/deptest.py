""" Attempts to import given modules, generating a list of packages to install,
    which can be later passed to pip during installation (-r).
"""

import importlib

dependencies = {
  #package name:      import module
  'beautifulsoup4':   'bs4',
  'matplotlib':       'matplotlib',
  'pillow':           'PIL',
  'requests':         'requests',
  'requests_html':    'requests_html',
  'semantic_version': 'semantic_version'
}

missing_packages = []

for package, module in dependencies.items():
  try:
    importlib.import_module(module)
  except ImportError:
    missing_packages.append(package)
    print("{} MISSING".format(module))
  else:
    print("{} OK".format(module))

if missing_packages:
  with open('install.txt', 'w') as install:
    for package in missing_packages:
      install.write('{}\n'.format(package))
