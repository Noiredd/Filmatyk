REM fw-local launch script

@ECHO OFF

REM Try to use python3 explicitly, only falling back to python.exe on problems
WHERE python3
IF %ERRORLEVEL% NEQ 0 (
  SET pyexe=python
) ELSE (
  SET pyexe=python3
)

REM First of all, execute the dependency check tool
%pyexe% filmatyk\dependency_test.py
REM If it left a list of packages to install - pass it to pip
IF EXIST install.txt (
  REM Tester can leave a list of missing packages. In this case - install them,
  REM and then remove the list file.
  %pyexe% -m pip install -r install.txt
  DEL install.txt
)

REM Only now trust the dependencies to be satisfied and launch
CD filmatyk
SET command=pythonw gui.py

IF [%1]==[] GOTO launch
IF %1==debug SET command=python gui.py debug

:launch
  START %command%
