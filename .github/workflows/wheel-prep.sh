export SCHEMA_SALAD_USE_MYPYC=1
export MYPYPATH=mypy-stubs
export SETUPTOOLS_SCM_PRETEND_VERSION=$(grep __version__ schema_salad/_version.py  | awk -F\' '{ print $2 }')
