FROM alpine:latest as builder

RUN apk add --no-cache git gcc python3-dev libc-dev
WORKDIR /schema_salad
COPY . .

RUN python3 -m venv env3
RUN source env3/bin/activate && python3 -m pip install -U pip setuptools wheel build
RUN export SETUPTOOLS_SCM_PRETEND_VERSION=$(grep __version__ schema_salad/_version.py  | awk -F\' '{ print $2 }') ; source env3/bin/activate && SCHEMA_SALAD_USE_MYPYC=1 MYPYPATH=mypy-stubs python3 -m build --wheel --outdir=/wheels
RUN source env3/bin/activate && python3 -m pip wheel -r requirements.txt --wheel-dir=/wheels
RUN source env3/bin/activate && python3 -m pip install --force-reinstall --no-index --no-warn-script-location --root=/pythonroot/ /wheels/*.whl

FROM alpine:latest as module
LABEL maintainer peter.amstutz@curoverse.com

RUN apk add --no-cache py3-six

COPY --from=builder /pythonroot/ /
