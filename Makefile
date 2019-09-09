# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

# Makefile for utility work on coverage.py.

default:
	@echo "* No default action *"

clean:
	-pip uninstall -y coverage
	-rm -f *.pyd */*.pyd
	-rm -f *.so */*.so
	-rm -rf build coverage.egg-info dist htmlcov
	-rm -rf __pycache__ */__pycache__ */*/__pycache__ */*/*/__pycache__ */*/*/*/__pycache__ */*/*/*/*/__pycache__
	-rm -f *.pyc */*.pyc */*/*.pyc */*/*/*.pyc */*/*/*/*.pyc */*/*/*/*/*.pyc
	-rm -f *.pyo */*.pyo */*/*.pyo */*/*/*.pyo */*/*/*/*.pyo */*/*/*/*/*.pyo
	-rm -f *.bak */*.bak */*/*.bak */*/*/*.bak */*/*/*/*.bak */*/*/*/*/*.bak
	-rm -f *$$py.class */*$$py.class */*/*$$py.class */*/*/*$$py.class */*/*/*/*$$py.class */*/*/*/*/*$$py.class
	-rm -f coverage/*,cover
	-rm -f MANIFEST
	-rm -f .coverage .coverage.* coverage.xml .metacov*
	-rm -f .tox/*/lib/*/site-packages/zzz_metacov.pth
	-rm -f */.coverage */*/.coverage */*/*/.coverage */*/*/*/.coverage */*/*/*/*/.coverage */*/*/*/*/*/.coverage
	-rm -f tests/zipmods.zip
	-rm -rf tests/eggsrc/build tests/eggsrc/dist tests/eggsrc/*.egg-info
	-rm -f setuptools-*.egg distribute-*.egg distribute-*.tar.gz
	-rm -rf doc/_build doc/_spell doc/sample_html_beta
	-rm -rf .tox_kits
	-rm -rf .cache .pytest_cache .hypothesis
	-rm -rf $$TMPDIR/coverage_test

sterile: clean
	-rm -rf .tox*
	-docker image rm -f quay.io/pypa/manylinux1_i686 quay.io/pypa/manylinux1_x86_64


CSS = coverage/htmlfiles/style.css
SCSS = coverage/htmlfiles/style.scss

css: $(CSS)
$(CSS): $(SCSS)
	sass --style=compact --sourcemap=none --no-cache $(SCSS) $@
	cp $@ tests/gold/html/styled

LINTABLE = coverage tests igor.py setup.py __main__.py

lint:
	tox -e lint

todo:
	-grep -R --include=*.py TODO $(LINTABLE)

pep8:
	pycodestyle --filename=*.py --repeat $(LINTABLE)

test:
	tox -e py27,py35 $(ARGS)

PYTEST_SMOKE_ARGS = -n 6 -m "not expensive" --maxfail=3 $(ARGS)

smoke:
	# Run tests with the C tracer in the lowest supported Python versions.
	COVERAGE_NO_PYTRACER=1 tox -q -e py27,py35 -- $(PYTEST_SMOKE_ARGS)

pysmoke:
	# Run tests with the Python tracer in the lowest supported Python versions.
	COVERAGE_NO_CTRACER=1 tox -q -e py27,py35 -- $(PYTEST_SMOKE_ARGS)

metacov:
	COVERAGE_COVERAGE=yes tox $(ARGS)

metahtml:
	python igor.py combine_html

# Kitting

kit:
	python setup.py sdist

wheel:
	tox -c tox_wheels.ini $(ARGS)

manylinux:
	docker run -it --init --rm -v `pwd`:/io quay.io/pypa/manylinux1_x86_64 /io/ci/manylinux.sh build
	docker run -it --init --rm -v `pwd`:/io quay.io/pypa/manylinux1_i686 /io/ci/manylinux.sh build

kit_upload:
	twine upload --verbose dist/*

test_upload:
	twine upload --verbose --repository testpypi dist/*

kit_local:
	# pip.conf looks like this:
	#   [global]
	#   find-links = file:///Users/ned/Downloads/local_pypi
	cp -v dist/* `awk -F "//" '/find-links/ {print $$2}' ~/.pip/pip.conf`
	# pip caches wheels of things it has installed. Clean them out so we
	# don't go crazy trying to figure out why our new code isn't installing.
	find ~/Library/Caches/pip/wheels -name 'coverage-*' -delete

download_appveyor:
	python ci/download_appveyor.py nedbat/coveragepy

build_ext:
	python setup.py build_ext

install:
	python setup.py install

uninstall:
	-rm -rf $(PYHOME)/lib/site-packages/coverage*
	-rm -rf $(PYHOME)/scripts/coverage*

# Documentation

SPHINXOPTS = -aE
SPHINXBUILD = .tox/doc/bin/sphinx-build $(SPHINXOPTS)
WEBHOME = ~/web/stellated/
WEBSAMPLE = $(WEBHOME)/files/sample_coverage_html
WEBSAMPLEBETA = $(WEBHOME)/files/sample_coverage_html_beta

docreqs:
	tox -q -e doc --notest

dochtml: docreqs
	.tox/doc/bin/python doc/check_copied_from.py doc/*.rst
	$(SPHINXBUILD) -b html doc doc/_build/html
	@echo
	@echo "Build finished. The HTML pages are in doc/_build/html."

docspell: docreqs
	$(SPHINXBUILD) -b spelling doc doc/_spell

publish:
	rm -f $(WEBSAMPLE)/*.*
	mkdir -p $(WEBSAMPLE)
	cp doc/sample_html/*.* $(WEBSAMPLE)

publishbeta:
	rm -f $(WEBSAMPLEBETA)/*.*
	mkdir -p $(WEBSAMPLEBETA)
	cp doc/sample_html_beta/*.* $(WEBSAMPLEBETA)

upload_relnotes: docreqs
	$(SPHINXBUILD) -b rst doc /tmp/rst_rst
	pandoc -frst -tmarkdown_strict --atx-headers /tmp/rst_rst/changes.rst > /tmp/rst_rst/changes.md
	python ci/upload_relnotes.py /tmp/rst_rst/changes.md pypi/coverage
