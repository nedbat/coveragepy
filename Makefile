# Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0
# For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt

# Makefile for utility work on coverage.py.

.DEFAULT_GOAL := help

##@ Utilities

.PHONY: help clean_platform clean sterile

clean_platform:
	@rm -f *.so */*.so
	@rm -f *.pyd */*.pyd
	@rm -rf __pycache__ */__pycache__ */*/__pycache__ */*/*/__pycache__ */*/*/*/__pycache__ */*/*/*/*/__pycache__
	@rm -f *.pyc */*.pyc */*/*.pyc */*/*/*.pyc */*/*/*/*.pyc */*/*/*/*/*.pyc
	@rm -f *.pyo */*.pyo */*/*.pyo */*/*/*.pyo */*/*/*/*.pyo */*/*/*/*/*.pyo
	@rm -f *$$py.class */*$$py.class */*/*$$py.class */*/*/*$$py.class */*/*/*/*$$py.class */*/*/*/*/*$$py.class

clean: clean_platform			## Remove artifacts of test execution, installation, etc.
	@echo "Cleaning..."
	@-pip uninstall -yq coverage
	@chmod -R 777 build
	@rm -rf build coverage.egg-info dist htmlcov
	@rm -f *.bak */*.bak */*/*.bak */*/*/*.bak */*/*/*/*.bak */*/*/*/*/*.bak
	@rm -f coverage/*,cover
	@rm -f MANIFEST
	@rm -f .coverage .coverage.* coverage.xml coverage.json .metacov*
	@rm -f .tox/*/lib/*/site-packages/zzz_metacov.pth
	@rm -f */.coverage */*/.coverage */*/*/.coverage */*/*/*/.coverage */*/*/*/*/.coverage */*/*/*/*/*/.coverage
	@rm -f tests/covmain.zip tests/zipmods.zip tests/zip1.zip
	@rm -rf doc/_build doc/_spell doc/sample_html_beta
	@rm -rf tmp
	@rm -rf .cache .hypothesis .mypy_cache .pytest_cache
	@rm -rf tests/actual
	@-make -C tests/gold/html clean

sterile: clean				## Remove all non-controlled content, even if expensive.
	rm -rf .tox
	rm -f cheats.txt

help:					## Show this help.
	@# Adapted from https://www.thapaliya.com/en/writings/well-documented-makefiles/
	@echo Available targets:
	@awk -F ':.*##' '/^[^: ]+:.*##/{printf "  \033[1m%-20s\033[m %s\n",$$1,$$2} /^##@/{printf "\n%s\n",substr($$0,5)}' $(MAKEFILE_LIST)

##@ Tests and quality checks

.PHONY: lint smoke

lint:					## Run linters and checkers.
	tox -q -e lint

PYTEST_SMOKE_ARGS = -n auto -m "not expensive" --maxfail=3 $(ARGS)

smoke: 					## Run tests quickly with the C tracer in the lowest supported Python versions.
	COVERAGE_NO_PYTRACER=1 tox -q -e py37 -- $(PYTEST_SMOKE_ARGS)


##@ Metacov: coverage measurement of coverage.py itself
# 	See metacov.ini for details.

.PHONY: metacov metahtml metasmoke

metacov:				## Run meta-coverage, measuring ourself.
	COVERAGE_COVERAGE=yes tox -q $(ARGS)

metahtml:				## Produce meta-coverage HTML reports.
	python igor.py combine_html

metasmoke:
	COVERAGE_NO_PYTRACER=1 ARGS="-e py39" make metacov metahtml


##@ Requirements management

# When updating requirements, a few rules to follow:
#
# 1) Don't install more than one .pip file at once. Always use pip-compile to
# combine .in files onto a single .pip file that can be installed where needed.
#
# 2) Check manual pins before `make upgrade` to see if they can be removed. Look
# in requirements/pins.pip, and search for "windows" in .in files to find pins
# and extra requirements that have been needed, but might be obsolete.

.PHONY: upgrade

PIP_COMPILE = pip-compile --upgrade --allow-unsafe --resolver=backtracking
upgrade: export CUSTOM_COMPILE_COMMAND=make upgrade
upgrade: 				## Update the *.pip files with the latest packages satisfying *.in files.
	pip install -q -r requirements/pip-tools.pip
	$(PIP_COMPILE) -o requirements/pip-tools.pip requirements/pip-tools.in
	$(PIP_COMPILE) -o requirements/pip.pip requirements/pip.in
	$(PIP_COMPILE) -o requirements/pytest.pip requirements/pytest.in
	$(PIP_COMPILE) -o requirements/kit.pip requirements/kit.in
	$(PIP_COMPILE) -o requirements/tox.pip requirements/tox.in
	$(PIP_COMPILE) -o requirements/dev.pip requirements/dev.in
	$(PIP_COMPILE) -o requirements/light-threads.pip requirements/light-threads.in
	$(PIP_COMPILE) -o doc/requirements.pip doc/requirements.in
	$(PIP_COMPILE) -o requirements/lint.pip doc/requirements.in requirements/dev.in
	$(PIP_COMPILE) -o requirements/mypy.pip requirements/mypy.in

diff_upgrade:				## Summarize the last `make upgrade`
	@# The sort flags sort by the package name first, then by the -/+, and
	@# sort by version numbers, so we get a summary with lines like this:
	@#	-bashlex==0.16
	@#	+bashlex==0.17
	@#	-build==0.9.0
	@#	+build==0.10.0
	@git diff -U0 | grep -v '^@' | grep == | sort -k1.2,1.99 -k1.1,1.1r -u -V

##@ Pre-builds for prepping the code

.PHONY: css workflows prebuild

CSS = coverage/htmlfiles/style.css
SCSS = coverage/htmlfiles/style.scss

css: $(CSS)				## Compile .scss into .css.
$(CSS): $(SCSS)
	pysassc --style=compact $(SCSS) $@
	cp $@ tests/gold/html/styled

workflows:				## Run cog on the workflows to keep them up-to-date.
	python -m cogapp -crP .github/workflows/*.yml

prebuild: css workflows cogdoc		## One command for all source prep.


##@ Sample HTML reports

.PHONY: _sample_cog_html sample_html sample_html_beta

_sample_cog_html: clean
	python -m pip install -e .
	cd ~/cog; \
		rm -rf htmlcov; \
		PYTEST_ADDOPTS= coverage run --branch --source=cogapp -m pytest -k CogTestsInMemory; \
		coverage combine; \
		coverage html

sample_html: _sample_cog_html		## Generate sample HTML report.
	rm -f doc/sample_html/*.*
	cp -r ~/cog/htmlcov/ doc/sample_html/
	rm doc/sample_html/.gitignore

sample_html_beta: _sample_cog_html	## Generate sample HTML report for a beta release.
	rm -f doc/sample_html_beta/*.*
	cp -r ~/cog/htmlcov/ doc/sample_html_beta/
	rm doc/sample_html_beta/.gitignore


##@ Kitting: making releases

.PHONY: kit kit_upload test_upload kit_local build_kits download_kits check_kits tag
.PHONY: update_stable comment_on_fixes

REPO_OWNER = nedbat/coveragepy

edit_for_release:			## Edit sources to insert release facts.
	python igor.py edit_for_release

cheats:					## Create some useful snippets for releasing.
	python igor.py cheats | tee cheats.txt

relbranch:				## Create the branch for releasing.
	git switch -c nedbat/release-$$(date +%Y%m%d)

relcommit1:				## Commit the first release changes.
	git commit -am "docs: prep for $$(python setup.py --version)"

relcommit2:				## Commit the latest sample HTML report.
	git commit -am "docs: sample HTML for $$(python setup.py --version)"

kit:					## Make the source distribution.
	python -m build

kit_upload:				## Upload the built distributions to PyPI.
	twine upload --verbose dist/*

test_upload:				## Upload the distributions to PyPI's testing server.
	twine upload --verbose --repository testpypi --password $$TWINE_TEST_PASSWORD dist/*

kit_local:
	# pip.conf looks like this:
	#   [global]
	#   find-links = file:///Users/ned/Downloads/local_pypi
	cp -v dist/* `awk -F "//" '/find-links/ {print $$2}' ~/.pip/pip.conf`
	# pip caches wheels of things it has installed. Clean them out so we
	# don't go crazy trying to figure out why our new code isn't installing.
	find ~/Library/Caches/pip/wheels -name 'coverage-*' -delete

build_kits:				## Trigger GitHub to build kits
	python ci/trigger_build_kits.py $(REPO_OWNER)

download_kits:				## Download the built kits from GitHub.
	python ci/download_gha_artifacts.py $(REPO_OWNER)

check_kits:				## Check that dist/* are well-formed.
	python -m twine check dist/*

tag:					## Make a git tag with the version number.
	git tag -a -m "Version $$(python setup.py --version)" $$(python setup.py --version)
	git push --follow-tags

update_stable:				## Set the stable branch to the latest release.
	git branch -f stable $$(python setup.py --version)
	git push origin stable

bump_version:				## Edit sources to bump the version after a release.
	git switch -c nedbat/bump-version
	python igor.py bump_version
	git commit -a -m "build: bump version"
	git push -u origin @


##@ Documentation

.PHONY: cogdoc dochtml docdev docspell

DOCBIN = .tox/doc/bin
SPHINXOPTS = -aE
SPHINXBUILD = $(DOCBIN)/sphinx-build $(SPHINXOPTS)
SPHINXAUTOBUILD = $(DOCBIN)/sphinx-autobuild --port 9876 --ignore '.git/**' --open-browser
WEBHOME = ~/web/stellated
WEBSAMPLE = $(WEBHOME)/files/sample_coverage_html
WEBSAMPLEBETA = $(WEBHOME)/files/sample_coverage_html_beta

$(DOCBIN):
	tox -q -e doc --notest

cogdoc: $(DOCBIN)			## Run docs through cog.
	$(DOCBIN)/python -m cogapp -crP --verbosity=1 doc/*.rst

dochtml: cogdoc $(DOCBIN)		## Build the docs HTML output.
	$(SPHINXBUILD) -b html doc doc/_build/html

docdev: dochtml				## Build docs, and auto-watch for changes.
	PATH=$(DOCBIN):$(PATH) $(SPHINXAUTOBUILD) -b html doc doc/_build/html

docspell: $(DOCBIN)			## Run the spell checker on the docs.
	$(SPHINXBUILD) -b spelling doc doc/_spell


##@ Publishing docs

.PHONY: publish publishbeta relnotes_json github_releases

publish:				## Publish the sample HTML report.
	rm -f $(WEBSAMPLE)/*.*
	mkdir -p $(WEBSAMPLE)
	cp doc/sample_html/*.* $(WEBSAMPLE)

publishbeta:
	rm -f $(WEBSAMPLEBETA)/*.*
	mkdir -p $(WEBSAMPLEBETA)
	cp doc/sample_html_beta/*.* $(WEBSAMPLEBETA)

CHANGES_MD = tmp/rst_rst/changes.md
RELNOTES_JSON = tmp/relnotes.json

$(CHANGES_MD): CHANGES.rst $(DOCBIN)
	$(SPHINXBUILD) -b rst doc tmp/rst_rst
	pandoc -frst -tmarkdown_strict --markdown-headings=atx --wrap=none tmp/rst_rst/changes.rst > $(CHANGES_MD)

relnotes_json: $(RELNOTES_JSON)		## Convert changelog to JSON for further parsing.
$(RELNOTES_JSON): $(CHANGES_MD)
	$(DOCBIN)/python ci/parse_relnotes.py tmp/rst_rst/changes.md $(RELNOTES_JSON)

github_releases: $(DOCBIN)		## Update GitHub releases.
	$(DOCBIN)/python -m scriv github-release

comment_on_fixes: $(RELNOTES_JSON)	## Add a comment to issues that were fixed.
	python ci/comment_on_fixes.py $(REPO_OWNER)
