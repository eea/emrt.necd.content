#!/bin/bash
BUILDCMD='cd /io/egg/; for PYBIN in /opt/python/cp2*/bin; do "${PYBIN}/python" setup.py bdist_wheel; "${PYBIN}/python" setup.py bdist_egg; done && for WHL in ./dist/*.whl; do auditwheel repair "${WHL}" -w ./dist/; done';

docker run --rm -v `pwd`:/io/egg/ quay.io/pypa/manylinux1_x86_64 bash -c "$BUILDCMD"
docker run --rm -v `pwd`:/io/egg/ quay.io/pypa/manylinux1_i686 linux32 bash -c "$BUILDCMD"
