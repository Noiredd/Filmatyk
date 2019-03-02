import sys
if sys.version_info.major != 3:
  sys.exit(2)
if sys.version_info.minor < 6:
  sys.exit(1)
sys.exit(0)
