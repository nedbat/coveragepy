# Makefile for utility work on coverage.py

default:
	@echo "* No default action *"

TEST_ZIP = test/zipmods.zip

clean:
	python test/test_farm.py clean
	-rm -rf build
	-rm -rf dist
	-rm -rf coverage.egg-info
	-rm -f *.pyd */*.pyd 
	-rm -f *.pyc */*.pyc */*/*.pyc */*/*/*.pyc */*/*/*/*.pyc */*/*/*/*/*.pyc
	-rm -f *.pyo */*.pyo */*/*.pyo */*/*/*.pyo */*/*/*/*.pyo */*/*/*/*/*.pyo
	-rm -f *.bak */*.bak */*/*.bak */*/*/*.bak */*/*/*/*.bak */*/*/*/*/*.bak
	-rm -f coverage/*,cover
	-rm -f MANIFEST
	-rm -f .coverage .coverage.*
	-rm -f $(TEST_ZIP)
	-rm -f setuptools-*.egg

LINTABLE_TESTS = \
	test/coveragetest.py \
	test/test_cmdline.py \
	test/test_data.py \
	test/test_execfile.py \
	test/test_farm.py \
	test/test_templite.py

lint: clean
	-python -x /Python25/Scripts/pylint.bat --rcfile=.pylintrc coverage
	-python -x /Python25/Scripts/pylint.bat --rcfile=.pylintrc $(LINTABLE_TESTS)
	python /Python25/Lib/tabnanny.py coverage
	python checkeol.py

testready: $(TEST_ZIP) devinst

tests: testready
	nosetests

$(TEST_ZIP): test/covmodzip1.py
	zip -j $@ $+

coverage:
	python coverage_coverage.py

WEBHOME = c:/ned/web/stellated/pages/code/modules

publish:
	cp doc/coverage.px $(WEBHOME)
	cp dist/coverage-* $(WEBHOME)

kit:
	python setup.py sdist --formats=gztar
	python setup.py bdist_wininst

pypi:
	python setup.py register

install:
	python setup.py install

DEVINST_FILE = coverage.egg-info/PKG-INFO
devinst: $(DEVINST_FILE)
$(DEVINST_FILE): coverage/tracer.c 
	python setup.py develop

uninstall:
	-rm -rf $(PYHOME)/lib/site-packages/coverage*
	-rm -rf $(PYHOME)/scripts/coverage*
