@echo off
set PATH=.;%HOME%\bin
set PATH=%PATH%;c:\windows\system32;c:\windows
set PATH=%PATH%;%1\scripts;%1
set PATH=%PATH%;C:\Program Files\Mercurial\bin
set PATH=%PATH%;c:\cygwin\bin
set PATH=%PATH%;c:\app\MinGW\bin
set PYTHONPATH=;c:\ned\py
set PYHOME=%1
rem title Py %1
if "%2"=="quiet" goto done
python -c "import sys; print ('\n=== Python %%s %%s' %% (sys.version.split()[0], '='*80))"

:done
