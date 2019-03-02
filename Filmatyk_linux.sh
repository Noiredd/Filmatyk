#!/bin/bash
# Filmatyk launch script

# It is much easier under Linux, since we don't have to deal with pythonw, just
# try for python3 or python and check their versions. Plus, bash has functions.
# Also, we don't print detailed error messages here.
test_cmd_ver () {
  # Tests whether $1 points to a proper Python 3.6 interpreter.
  _p=$(which $1)
  if [ $? -ne 0 ]; then
    status=3
  else
    $1 tools/pytest.py
    status=$?
  fi
  echo $status
}
# Try python3
found=$(test_cmd_ver python3)
if [ $found -ne 0 ]; then
  # In case of failure - python as last resort
  found=$(test_cmd_ver python)
  if [ $found -ne 0]; then
    echo "Unable to find a Python 3.6+ interpreter"
    exit $found
  else
    pycmd=python
  fi
else
  pycmd=python3
fi

# Check dependencies
$pycmd tools/deptest.py
if [ -f install.txt ]; then
  $pycmd -m pip install -r install.txt
  rm install.txt
fi

# Ready to launch
cd filmatyk
$pycmd gui.py linux $1 # pass $1 as it might be a debug flag
