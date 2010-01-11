@REM Build all the kits for coverage.py
@REM Add "upload" onto the command line to also upload.
call \ned\bin\switchpy 23
python setup.py bdist_wininst %1 
call \ned\bin\switchpy 24
python setup.py bdist_wininst %1
call \ned\bin\switchpy 25
python setup.py bdist_wininst %1
call \ned\bin\switchpy 26
python setup.py bdist_wininst %1
call \ned\bin\switchpy 27
python setup.py bdist_wininst %1

set TAR_OPTIONS=--group=100
python setup.py sdist --formats=gztar %1
set TAR_OPTIONS=

@REM Py3k
call \ned\bin\switchpy 31
python setup.py bdist_wininst %1
