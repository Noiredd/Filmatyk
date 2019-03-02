REM Filmatyk launch script

@ECHO OFF

REM Now the following behavior of the Windows shell makes it understandable why
REM why most sane people despise it (just in case having to say "REM" to denote
REM comments was not enough). Turns out that - by default - ERRORLEVEL variable
REM will NOT be updated when within an IF clause. So when we want to check some
REM situation and - while handling that one - check some different one, results
REM of that other check will NOT be readable.
REM Solution to that is to enable a "delayed expansion" which, simply speaking,
REM makes the shell behave as a sane programmer with prior experience with sane
REM languages would expect.
REM http://batcheero.blogspot.com/2007/06/how-to-enabledelayedexpansion.html
SETLOCAL ENABLEDELAYEDEXPANSION

REM Check Python version.
REM It would be best if we could use pythonw as it does not open any additional
REM terminal, so we check for that first. If this is not found, we look for the
REM default python executable. In both cases, a version check is made to ensure
REM that they satisfy the minimum version (3.6). If neither does, one final try
REM is to search for python3 and hope that will be a valid interpreter.
REM Python executable search order:
SET versions=pythonw python python3
REM Remember the closest we got to a working version. Worst to least dangerous:
REM no Python found at all (3), Python 3 not found (2), found but minor version
REM is below 6 (1), working Python 3.6 found (0).
SET python_status=3
REM Iterate over versions
(FOR %%p IN (%versions%) DO (
  REM Check for existence of the executable
  WHERE %%p /q
  IF !ERRORLEVEL! EQU 0 (
    REM Executable found. Launch the version checker
    %%p tools\pytest.py %%p
    SET test_result=!ERRORLEVEL!
    REM Keep track of the least serious error encountered yet
    IF !test_result! LSS %python_status% (
      SET python_status=!test_result!
    )
    REM If the error code was zero, means the version matches
    IF !test_result! EQU 0 (
      SET pyexe=%%p
      GOTO exit_loop
    )
  ) ELSE (
    REM Executable not found - might need to set status too
    IF 3 LSS %python_status% (
      SET python_status=3
    )
  )
))
:exit_loop
REM Check status and jump to failure handler if it is positive
IF %python_status% NEQ 0 (
  GOTO failure
)

REM Check dependencies
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
SET command=%pyexe% gui.py

IF [%1]==[] GOTO launch
IF %1==debug SET command=python gui.py debug

:launch
  START %command%
  GOTO end

:failure
  REM Basing on the error status, print the right diagnostic message
  IF %python_status% EQU 1 (
    SET ermsg=Python 3 found but version below 3.6
  ) ELSE IF %python_status% EQU 2 (
    SET ermsg=Python 3 not found
  ) ELSE IF %python_status% EQU 3 (
    SET ermsg=Python not found. Perhaps it is not in the PATH?
  )
  ECHO Failed to launch program, %ermsg%
  GOTO end

:end
