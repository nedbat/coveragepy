call \ned\bin\switchpy 23
python setup.py -q develop
nosetests
del coverage\tracer.pyd
nosetests
call \ned\bin\switchpy 24
python setup.py -q develop
nosetests
del coverage\tracer.pyd
nosetests
call \ned\bin\switchpy 25
python setup.py -q develop
nosetests
del coverage\tracer.pyd
nosetests
call \ned\bin\switchpy 26
python setup.py -q develop
nosetests
del coverage\tracer.pyd
nosetests
