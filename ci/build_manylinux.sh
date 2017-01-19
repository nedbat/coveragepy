#!/bin/bash
# From: https://github.com/pypa/python-manylinux-demo/blob/master/travis/build-wheels.sh
# which is in the public domain.
#
# This is run inside a Centos 5 virtual machine to build manylinux wheels.

set -e -x

# Install a system package required by our library
yum install -y atlas-devel

# Compile wheels
for PYBIN in /opt/python/*/bin; do
    "${PYBIN}/pip" install -r /io/requirements/wheel.pip
    "${PYBIN}/pip" wheel /io/ -w wheelhouse/
done

# Bundle external shared libraries into the wheels
for whl in wheelhouse/*.whl; do
    auditwheel repair "$whl" -w /io/dist/
done

# Install packages and test
# for PYBIN in /opt/python/*/bin/; do
#     "${PYBIN}/pip" install python-manylinux-demo --no-index -f /io/dist
#     (cd "$HOME"; "${PYBIN}/nosetests" pymanylinuxdemo)
# done
