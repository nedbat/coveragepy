@echo off
make --quiet testdata

call \ned\bin\switchpy 23
python setup.py -q develop
set COVERAGE_TEST_TRACER=c
python test\coverage_coverage.py run %1 %2 %3 %4 %5 %6 %7 %8 %9
del coverage\tracer.pyd
set COVERAGE_TEST_TRACER=py
python test\coverage_coverage.py run %1 %2 %3 %4 %5 %6 %7 %8 %9

call \ned\bin\switchpy 24
python setup.py -q develop
set COVERAGE_TEST_TRACER=c
python test\coverage_coverage.py run %1 %2 %3 %4 %5 %6 %7 %8 %9
del coverage\tracer.pyd
set COVERAGE_TEST_TRACER=py
python test\coverage_coverage.py run %1 %2 %3 %4 %5 %6 %7 %8 %9

call \ned\bin\switchpy 25
python setup.py -q develop
set COVERAGE_TEST_TRACER=c
python test\coverage_coverage.py run %1 %2 %3 %4 %5 %6 %7 %8 %9
del coverage\tracer.pyd
set COVERAGE_TEST_TRACER=py
python test\coverage_coverage.py run %1 %2 %3 %4 %5 %6 %7 %8 %9

call \ned\bin\switchpy 26
python setup.py -q develop
set COVERAGE_TEST_TRACER=c
python test\coverage_coverage.py run %1 %2 %3 %4 %5 %6 %7 %8 %9
del coverage\tracer.pyd
set COVERAGE_TEST_TRACER=py
python test\coverage_coverage.py run %1 %2 %3 %4 %5 %6 %7 %8 %9

call \ned\bin\switchpy 31
python setup.py -q develop
set COVERAGE_TEST_TRACER=c
python test\coverage_coverage.py run %1 %2 %3 %4 %5 %6 %7 %8 %9
del coverage\tracer.pyd
set COVERAGE_TEST_TRACER=py
python test\coverage_coverage.py run %1 %2 %3 %4 %5 %6 %7 %8 %9

python test\coverage_coverage.py report
