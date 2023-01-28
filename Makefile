# This file is part of schema-salad,
# https://github.com/common-workflow-language/schema-salad/, and is
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Contact: common-workflow-language@googlegroups.com

# make format to fix most python formatting errors
# make pylint to check Python code for enhanced compliance including naming
#  and documentation
# make coverage-report to check coverage of the python scripts by the tests

MODULE=schema_salad
PACKAGE=schema-salad
EXTRAS=[pycodegen]

# `SHELL=bash` doesn't work for some, so don't use BASH-isms like
# `[[` conditional expressions.
PYSOURCES=$(wildcard ${MODULE}/**.py ${MODULE}/avro/*.py ${MODULE}/tests/*.py) setup.py
DEVPKGS=-rdev-requirements.txt -rtest-requirements.txt -rmypy-requirements.txt
COVBASE=coverage run --append
PYTEST_EXTRA ?= -rs

# Updating the Major & Minor version below?
# Don't forget to update setup.py as well
VERSION=8.4.$(shell date +%Y%m%d%H%M%S --utc --date=`git log --first-parent \
	--max-count=1 --format=format:%cI`)

## all                    : default task (install schema-salad in dev mode)
all: dev

## help                   : print this help message and exit
help: Makefile
	@sed -n 's/^##//p' $<

## cleanup                : shortcut for "make sort_imports format flake8 diff_pydocstyle_report"
cleanup: sort_imports format flake8 diff_pydocstyle_report

## install-dep            : install most of the development dependencies via pip
install-dep: install-dependencies

install-dependencies: FORCE
	pip install --upgrade $(DEVPKGS)

## install                : install the schema-salad package and scripts
install: FORCE
	pip install .$(EXTRAS)

## dev                    : install the schema-salad package in dev mode
dev: install-dep
	pip install -U pip setuptools wheel
	pip install -e .$(EXTRAS)

## dist                   : create a module package for distribution
dist: dist/${MODULE}-$(VERSION).tar.gz

dist/${MODULE}-$(VERSION).tar.gz: $(SOURCES)
	python -m build

## docs                   : make the docs
docs: FORCE
	cd docs && $(MAKE) html

## clean                  : clean up all temporary / machine-generated files
clean: FORCE
	rm -rf ${MODULE}/__pycache__ ${MODULE}/tests/__pycache__ schema_salad/_version.py
	rm -f *.so ${MODULE}/*.so ${MODULE}/tests/*.so ${MODULE}/avro/*.so
	python setup.py clean --all || true
	rm -Rf .coverage
	rm -f diff-cover.html

# Linting and code style related targets
## sort_import            : sorting imports using isort: https://github.com/timothycrosley/isort
sort_imports: $(filter-out schema_salad/metaschema.py,$(PYSOURCES)) mypy-stubs
	isort $^

remove_unused_imports: $(filter-out schema_salad/metaschema.py,$(PYSOURCES))
	autoflake --in-place --remove-all-unused-imports $^

pep257: pydocstyle
## pydocstyle             : check Python docstring style
pydocstyle: $(filter-out schema_salad/metaschema.py,$(PYSOURCES))
	pydocstyle --add-ignore=D100,D101,D102,D103 $^ || true

pydocstyle_report.txt: $(filter-out schema_salad/metaschema.py,$(PYSOURCES))
	pydocstyle setup.py $^ > $@ 2>&1 || true

## diff_pydocstyle_report : check Python docstring style for changed files only
diff_pydocstyle_report: pydocstyle_report.txt
	diff-quality --compare-branch=main --violations=pydocstyle --fail-under=100 $^

## codespell              : check for common misspellings
codespell:
	codespell -w $(shell git ls-files | grep -v mypy-stubs | grep -v gitignore | grep -v EDAM.owl | grep -v pre.yml | grep -v test_schema)

## format                 : check/fix all code indentation and formatting (runs black)
format:
	black --force-exclude metaschema.py --exclude _version.py schema_salad setup.py mypy-stubs

format-check:
	black --diff --check --force-exclude metaschema.py --exclude _version.py schema_salad setup.py mypy-stubs

## pylint                 : run static code analysis on Python code
pylint: $(PYSOURCES)
	pylint --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" \
                $^ -j0|| true

pylint_report.txt: $(PYSOURCES)
	pylint --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" \
		$^ -j0> $@ || true

diff_pylint_report: pylint_report.txt
	diff-quality --compare-branch=main --violations=pylint pylint_report.txt

.coverage:
	python setup.py test --addopts "--cov --cov-config=.coveragerc --cov-report= ${PYTEST_EXTRA}"
	$(COVBASE) -m schema_salad.main \
		--print-jsonld-context schema_salad/metaschema/metaschema.yml \
		> /dev/null
	$(COVBASE) -m schema_salad.main \
		--print-rdfs schema_salad/metaschema/metaschema.yml \
		> /dev/null
	$(COVBASE) -m schema_salad.main \
		--print-avro schema_salad/metaschema/metaschema.yml \
		> /dev/null
	$(COVBASE) -m schema_salad.makedoc --debug \
		schema_salad/metaschema/metaschema.yml \
		> /dev/null

coverage.xml: .coverage
	coverage xml

coverage.html: htmlcov/index.html

htmlcov/index.html: .coverage
	coverage html
	@echo Test coverage of the Python code is now in htmlcov/index.html

coverage-report: .coverage
	coverage report

diff-cover: coverage.xml
	diff-cover --compare-branch=main $^

diff-cover.html: coverage.xml
	diff-cover --compare-branch=main $^ --html-report $@

## test                   : run the schema-salad test suite
test: $(PYSOURCES)
	python -m pytest -rs ${PYTEST_EXTRA}

## testcov                : run the schema-salad test suite and collect coverage
testcov: $(PYSOURCES)
	python setup.py test --addopts "--cov" ${PYTEST_EXTRA}

sloccount.sc: $(PYSOURCES) Makefile
	sloccount --duplicates --wide --details $^ > $@

## sloccount              : count lines of code
sloccount: $(PYSOURCES) Makefile
	sloccount $^

list-author-emails:
	@echo 'name, E-Mail Address'
	@git log --format='%aN,%aE' | sort -u | grep -v 'root'

mypy3: mypy
mypy: $(filter-out setup.py,$(PYSOURCES))
	MYPYPATH=$$MYPYPATH:mypy-stubs mypy $^

mypy_3.6: $(filter-out setup.py,$(PYSOURCES))
	MYPYPATH=$$MYPYPATH:mypy-stubs mypy --python-version 3.6 $^

mypyc: $(PYSOURCES)
	MYPYPATH=mypy-stubs SCHEMA_SALAD_USE_MYPYC=1 python setup.py test --addopts "${PYTEST_EXTRA}"

mypyi:
	MYPYPATH=mypy-stubs SCHEMA_SALAD_USE_MYPYC=1 python setup.py install

check-metaschema-diff:
	docker run \
		-v "$(realpath ${MODULE}/metaschema/):/tmp/:ro" \
		"quay.io/commonwl/cwltool_module:latest" \
		schema-salad-doc /tmp/metaschema.yml \
		> /tmp/metaschema.orig.html
	schema-salad-doc \
		"$(realpath ${MODULE}/metaschema/metaschema.yml)" \
		> /tmp/metaschema.new.html
	diff -a --color /tmp/metaschema.orig.html /tmp/metaschema.new.html || true

compute-metaschema-hash:
	@python -c 'import hashlib; from schema_salad.tests.test_makedoc import generate_doc; hasher = hashlib.sha256(); hasher.update(generate_doc().encode("utf-8")); print(hasher.hexdigest());'

shellcheck: FORCE
	shellcheck build-schema_salad-docker.sh release-test.sh

pyupgrade: $(filter-out schema_salad/metaschema.py,$(PYSOURCES))
	pyupgrade --exit-zero-even-if-changed --py36-plus $^

release-test: FORCE
	git diff-index --quiet HEAD -- || ( echo You have uncommitted changes, please commit them and try again; false )
	./release-test.sh

release:
	export SETUPTOOLS_SCM_PRETEND_VERSION=${VERSION} && \
	./release-test.sh && \
	. testenv2/bin/activate && \
		pip install build && \
		python -m build testenv2/src/${PACKAGE} && \
		pip install twine && \
		twine upload testenv2/src/${PACKAGE}/dist/* && \
		git tag ${VERSION} && git push --tags

flake8: FORCE
	flake8 $(PYSOURCES)

schema_salad/metaschema.py: schema_salad/codegen_base.py schema_salad/python_codegen_support.py schema_salad/python_codegen.py schema_salad/metaschema/*.yml
	schema-salad-tool --codegen python schema_salad/metaschema/metaschema.yml > $@

FORCE:

# Use this to print the value of a Makefile variable
# Example `make print-VERSION`
# From https://www.cmcrossroads.com/article/printing-value-makefile-variable
print-%  : ; @echo $* = $($*)
