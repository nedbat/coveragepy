@REM Build all the kits for coverage.py
call \ned\bin\switchpy 23
python setup.py bdist_wininst
call \ned\bin\switchpy 24
python setup.py bdist_wininst
call \ned\bin\switchpy 25
python setup.py bdist_wininst
call \ned\bin\switchpy 26
python setup.py bdist_wininst

del /q py3k\*.*
mkdir py3k
copy three\coverage\*.py py3k
set TAR_OPTIONS=--group=100
python setup.py sdist --formats=gztar
set TAR_OPTIONS=

cd three
call \ned\bin\switchpy 31
python setup.py bdist_wininst
cd ..
copy three\dist\*.exe dist
