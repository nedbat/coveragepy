@REM Copy the sources, convert to Py3k, and run the tests.

rmdir/s/q ..\three
xcopy /s/h/i/e . ..\three
cd ..\three
call switchpy 31
python \python31\Tools\Scripts\2to3.py -w coverage test setup.py
make testready
python \python31\Scripts\nosetests3
