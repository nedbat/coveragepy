@REM Copy the sources, convert to Py3k, and run the tests.

rmdir /s/q three ..\three
xcopy /s/h/i/e /exclude:notsource.txt . ..\three
move ..\three .
cd three
call switchpy 31
python \python31\Tools\Scripts\2to3.py --write --nobackups --no-diffs coverage test mock.py

make clean
make testdata

python setup.py install

@REM Run both modes of tracer
set COVERAGE_TEST_TRACER=c
python \python31\Scripts\nosetests3 %1
del \python31\lib\site-packages\coverage\tracer.pyd
set COVERAGE_TEST_TRACER=py
python \python31\Scripts\nosetests3 %1

cd ..
