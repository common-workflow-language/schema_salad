#!/bin/bash

set -e
set -x

package=schema-salad
module=schema_salad
if [ "$GITHUB_ACTIONS" = "true" ]; then
    # We are running as a GH Action
    repo=${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}.git
    HEAD=${GITHUB_REF}
else
    repo=https://github.com/common-workflow-language/schema_salad.git
    HEAD=$(git rev-parse HEAD)
fi
run_tests="bin/py.test --pyargs ${module}"
pipver=18 # minimum required version of pip
setupver=41.1.0 # minimum required version of setuptools
PYVER=${PYVER:=3}

rm -Rf "testenv${PYVER}_"? || /bin/true

if [ "${RELEASE_SKIP}" != "head" ]
then
	"python${PYVER}" -m venv "testenv${PYVER}_1"
	# First we test the head
	# shellcheck source=/dev/null
	source "testenv${PYVER}_1/bin/activate"
	rm -f "testenv${PYVER}_1/lib/python-wheels/setuptools"*
	pip install --force-reinstall -U pip==${pipver}
	pip install setuptools==${setupver} wheel
	pip install pytest\<7 pytest-xdist -rrequirements.txt
	make test
	pip uninstall -y ${package} || true; pip uninstall -y ${package} \
		|| true; make install
	mkdir "testenv${PYVER}_1/not-${module}"
	# if there is a subdir named '${module}' py.test will execute tests
	# there instead of the installed module's tests
	
	pushd "testenv${PYVER}_1/not-${module}"
	# shellcheck disable=SC2086
	../${run_tests}; popd
fi


"python${PYVER}" -m venv "testenv${PYVER}_2"
"python${PYVER}" -m venv "testenv${PYVER}_3"
"python${PYVER}" -m venv "testenv${PYVER}_4"
"python${PYVER}" -m venv "testenv${PYVER}_5"


# Secondly we test via pip

pushd "testenv${PYVER}_2"
# shellcheck source=/dev/null
source bin/activate
rm -f lib/python-wheels/setuptools* \
	&& pip install --force-reinstall -U pip==${pipver} \
        && pip install setuptools==${setupver} wheel
# The following can fail if you haven't pushed your commits to ${repo}
pip install -e "git+${repo}@${HEAD}#egg=${package}"
pushd src/${package}
pip install pytest\<7 pytest-xdist
make dist
make test
cp dist/${package}*tar.gz "../../../testenv${PYVER}_3/"
cp dist/${module}*whl "../../../testenv${PYVER}_4/"
pip uninstall -y ${package} || true; pip uninstall -y ${package} || true; make install
popd # ../.. no subdir named ${proj} here, safe for py.testing the installed module
# shellcheck disable=SC2086
${run_tests}
popd

# Is the source distribution in testenv${PYVER}_2 complete enough to build
# another functional distribution?

pushd "testenv${PYVER}_3/"
# shellcheck source=/dev/null
source bin/activate
rm -f lib/python-wheels/setuptools* \
	&& pip install --force-reinstall -U pip==${pipver} \
        && pip install setuptools==${setupver} wheel
pip install ${package}*tar.gz
pip install pytest\<7 pytest-xdist
mkdir out
tar --extract --directory=out -z -f ${package}*.tar.gz
pushd out/${package}*
make dist
make test
pip uninstall -y ${package} || true; pip uninstall -y ${package} || true; make install
mkdir ../not-${module}
pushd ../not-${module}
# shellcheck disable=SC2086
../../${run_tests}; popd
popd
popd

# Is the wheel in testenv${PYVER}_2 installable and will it pass the tests

pushd "testenv${PYVER}_4/"
# shellcheck source=/dev/null
source bin/activate
rm -f lib/python-wheels/setuptools* \
	&& pip install --force-reinstall -U pip==${pipver} \
        && pip install setuptools==${setupver} wheel
pip install ${module}*.whl
pip install pytest\<7 pytest-xdist
mkdir not-${module}
pushd not-${module}
# shellcheck disable=SC2086
../${run_tests}; popd
popd
