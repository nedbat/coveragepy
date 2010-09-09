@REM Build all the kits for coverage.py
@REM Add "upload" onto the command line to also upload.
for %%v in (23 24 25 26 27 31 32) do (
    call \ned\bin\switchpy c:\vpy\coverage\%%v
    python setup.py bdist_wininst %1 
    )

call \ned\bin\switchpy c:\vpy\coverage\26
python setup.py --command-packages=distcmd sdist --keep-temp --formats=gztar fixtar --owner=ned --group=coverage --clean %1
