#!/bin/sh
# Build with a native BlocksDS installation or the official Docker image.
set -eu
cd "$(dirname "$0")/.."
python3 tools/link_version.py

if [ -z "${BLOCKSDS:-}" ]; then
    if [ -f /opt/ordinatrice/bin/dsenv.sh ]; then
        . /opt/ordinatrice/bin/dsenv.sh
    elif [ -f /opt/wonderful/bin/wf-env ]; then
        . /opt/wonderful/bin/wf-env
    fi
fi

if [ -n "${BLOCKSDS:-}" ]; then
    exec make "$@"
fi

exec docker run --rm --user "$(id -u):$(id -g)" \
    --volume "$PWD:/work" --workdir /work --entrypoint make \
    "${BLOCKSDS_IMAGE:-skylyrac/blocksds:slim-latest}" "$@"
