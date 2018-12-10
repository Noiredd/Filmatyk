cd fw-local
rem For some users, python3.exe would not exist.
rem In this case, use a fall-back python.exe and hope that it's version 3.6+
where python3
if $errorlevel$ neq 0 (
  set python=python
) else (
  set python=python3
)
echo %python%
%python% -m pip install requests_html
%python% -m pip install matplotlib
%python% -m pip install pillow
