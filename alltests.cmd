call \ned\bin\switchpy 23
python setup.py -q develop
set COVERAGE_TEST_TRACER=c
nosetests
del coverage\tracer.pyd
set COVERAGE_TEST_TRACER=py
nosetests

call \ned\bin\switchpy 24
python setup.py -q develop
set COVERAGE_TEST_TRACER=c
nosetests
del coverage\tracer.pyd
set COVERAGE_TEST_TRACER=py
nosetests

call \ned\bin\switchpy 25
python setup.py -q develop
set COVERAGE_TEST_TRACER=c
nosetests
del coverage\tracer.pyd
set COVERAGE_TEST_TRACER=py
nosetests

call \ned\bin\switchpy 26
python setup.py -q develop
set COVERAGE_TEST_TRACER=c
nosetests
del coverage\tracer.pyd
set COVERAGE_TEST_TRACER=py
nosetests
