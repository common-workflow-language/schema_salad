FROM python:3.9-alpine as builder

RUN apk add --no-cache git gcc python3-dev libc-dev

WORKDIR /schema_salad
COPY . .

RUN pip install toml -rmypy-requirements.txt "$(grep ruamel requirements.txt)"
RUN SCHEMA_SALAD_USE_MYPYC=1 MYPYPATH=typeshed python3 setup.py bdist_wheel --dist-dir=/wheels
RUN pip wheel -r requirements.txt --wheel-dir=/wheels
RUN pip install --force-reinstall --no-index --no-warn-script-location --root=/pythonroot/ /wheels/*.whl

FROM python:3.9-alpine as module
LABEL maintainer peter.amstutz@curoverse.com

COPY --from=builder /pythonroot/ /
