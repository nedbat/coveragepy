@REM Build all the kits for coverage.py
@REM Add "upload" onto the command line to also upload.
for %%v in (23 24 25 26 27 31) do (
    call \ned\bin\switchpy %%v
    python setup.py bdist_wininst %1 
    )

call \ned\bin\switchpy 26
set TAR_OPTIONS=--group=100
python setup.py sdist --formats=gztar %1
set TAR_OPTIONS=
