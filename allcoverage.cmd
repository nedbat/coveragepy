@echo off
make --quiet testdata

del .coverage.*
set COVERAGE_PROCESS_START=c:\ned\coverage\trunk\covcov.ini
set COVERAGE_COVERAGE=1

for %%v in (23 24 25 26 27 31 32) do (
    call \ned\bin\switchpy c:\vpy\coverage\%%v
    python setup.py -q develop
    set COVERAGE_TEST_TRACER=c
    python test\coverage_coverage.py run %1 %2 %3 %4 %5 %6 %7 %8 %9
    del coverage\tracer.pyd
    )

set COVERAGE_PROCESS_START=
set COVERAGE_COVERAGE=

python test\coverage_coverage.py report
