#!/bin/bash
set -ex
engine=${ENGINE:-docker}  # example: `ENGINE=podman ./build-schema_salad-docker.sh`
${engine} build --file=schema_salad.Dockerfile --tag=quay.io/commonwl/schema_salad .
${engine} run quay.io/commonwl/schema_salad /bin/sh -c \
	'apk add --no-cache py3-pip && pip install --break-system-packages pytest-xdist && cd /tmp && pytest --pyargs schema_salad -n auto'

# version=$(git describe --tags)
# if echo "$version" | grep -vq '\-' >& /dev/null ; then
#     docker tag quay.io/commonwl/schema_salad quay.io/commonwl/schema_salad:"$version"
# fi
