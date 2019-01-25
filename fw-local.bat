CD fw-local
SET command=pythonw gui.py

IF [%1]==[] GOTO launch
IF %1==debug SET command=python gui.py debug

:launch
  START %command%
