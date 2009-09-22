call \ned\bin\switchpy 23
python setup.py -q develop
set COVERAGE_TEST_TRACER=c
nosetests %1
del coverage\tracer.pyd
set COVERAGE_TEST_TRACER=py
nosetests %1

call \ned\bin\switchpy 24
python setup.py -q develop
set COVERAGE_TEST_TRACER=c
nosetests %1
del coverage\tracer.pyd
set COVERAGE_TEST_TRACER=py
nosetests %1

call \ned\bin\switchpy 25
python setup.py -q develop
set COVERAGE_TEST_TRACER=c
nosetests %1
del coverage\tracer.pyd
set COVERAGE_TEST_TRACER=py
nosetests %1

call \ned\bin\switchpy 26
python setup.py -q develop
set COVERAGE_TEST_TRACER=c
nosetests %1
del coverage\tracer.pyd
set COVERAGE_TEST_TRACER=py
nosetests %1

call \ned\bin\switchpy 31
python setup.py -q install
set COVERAGE_TEST_TRACER=c
python \python31\Scripts\nosetests3 %1
del \python31\lib\site-packages\coverage\tracer.pyd
set COVERAGE_TEST_TRACER=py
python \python31\Scripts\nosetests3 %1
