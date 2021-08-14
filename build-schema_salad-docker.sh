#!/bin/bash
set -ex
docker build --file=schema_salad.Dockerfile --tag=quay.io/commonwl/schema_salad .
docker run quay.io/commonwl/schema_salad /bin/sh -c \
	'pip install pytest-xdist && pytest --pyargs schema_salad -n auto'

version=$(git describe --tags)
if echo "$version" | grep -vq '\-' >& /dev/null ; then
    docker tag quay.io/commonwl/schema_salad quay.io/commonwl/schema_salad:"$version"
fi
