@echo off
make --quiet testdata

del .coverage.*
set COVERAGE_PROCESS_START=c:\ned\coverage\trunk\covcov.ini
set COVERAGE_COVERAGE=1

call \ned\bin\switchpy 23
python setup.py -q develop
set COVERAGE_TEST_TRACER=c
python test\coverage_coverage.py run %1 %2 %3 %4 %5 %6 %7 %8 %9
del coverage\tracer.pyd

call \ned\bin\switchpy 24
python setup.py -q develop
set COVERAGE_TEST_TRACER=c
python test\coverage_coverage.py run %1 %2 %3 %4 %5 %6 %7 %8 %9
del coverage\tracer.pyd

call \ned\bin\switchpy 25
python setup.py -q develop
set COVERAGE_TEST_TRACER=c
python test\coverage_coverage.py run %1 %2 %3 %4 %5 %6 %7 %8 %9
del coverage\tracer.pyd

call \ned\bin\switchpy 26
python setup.py -q develop
set COVERAGE_TEST_TRACER=c
python test\coverage_coverage.py run %1 %2 %3 %4 %5 %6 %7 %8 %9
del coverage\tracer.pyd

call \ned\bin\switchpy 31
python setup.py -q develop
set COVERAGE_TEST_TRACER=c
python test\coverage_coverage.py run %1 %2 %3 %4 %5 %6 %7 %8 %9
del coverage\tracer.pyd

set COVERAGE_PROCESS_START=
set COVERAGE_COVERAGE=

python test\coverage_coverage.py report
