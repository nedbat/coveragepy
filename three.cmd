@REM Copy the sources, convert to Py3k, and run the tests.

rmdir/s/q ..\three
xcopy /s/h/i/e /exclude:notsource.txt . ..\three
cd ..\three
call switchpy 31
python \python31\Tools\Scripts\2to3.py -w coverage test setup.py mock.py
make clean
make testdata

@REM We run coverage out of the source directory, so put built stuff there.
python setup.py build
copy build\lib.win32-3.1\coverage\tracer.pyd coverage

@REM Run both modes of tracer
set COVERAGE_TEST_TRACER=c
python \python31\Scripts\nosetests3 %1
del coverage\tracer.pyd
set COVERAGE_TEST_TRACER=py
python \python31\Scripts\nosetests3 %1
