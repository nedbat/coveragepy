@REM Build all the kits for coverage.py
call \ned\bin\switchpy 23
python setup.py bdist_wininst
call \ned\bin\switchpy 24
python setup.py bdist_wininst
call \ned\bin\switchpy 25
python setup.py bdist_wininst
call \ned\bin\switchpy 26
python setup.py bdist_wininst

set TAR_OPTIONS=--group=100
python setup.py sdist --formats=gztar
set TAR_OPTIONS=

@REM Py3k
call \ned\bin\switchpy 31
python setup.py bdist_wininst
