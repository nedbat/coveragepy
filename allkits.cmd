@REM Build all the kits for coverage.py
call \ned\bin\switchpy 23
python setup.py bdist_wininst
call \ned\bin\switchpy 24
python setup.py bdist_wininst
call \ned\bin\switchpy 25
python setup.py bdist_wininst
call \ned\bin\switchpy 26
python setup.py bdist_wininst

@REM Source kit: Py2k in "coverage", Py3k in "py3k"
del /q py3k\*.*
mkdir py3k
xcopy /s/h/i/e /exclude:notsource.txt three\coverage\*.py py3k
set TAR_OPTIONS=--group=100
python setup.py sdist --formats=gztar
set TAR_OPTIONS=

@REM py3k windows kit: code still needs to be in py3k, so move it.
cd three
call \ned\bin\switchpy 31
xcopy /s/h/i/e coverage py3k
python setup.py bdist_wininst
rmdir/s/q py3k
cd ..
copy three\dist\*.exe dist
