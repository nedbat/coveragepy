#!/usr/bin/env bash
#
# Create virtualenvs needed to test coverage.
# Invoke with command args, a list of python installations to make virtualenvs
# from.  COVERAGE_VE should point to the directory to hold them. For example:
#
#   COVERAGE_VE=../ve ./build_ve.sh /opt/python*
#

ve=${COVERAGE_VE:-../ve}

echo "Constructing virtualenvs in $ve"

rm -rf $ve
mkdir $ve

for p in $*
do
    echo --- $p -------------------------
    if [ -f $p/bin/python ]; then
        suff=
    elif [ -f $p/bin/python3 ]; then
        suff=3
    else
        echo "*** There's no Python in $p"
        exit
    fi

    # Figure out what version we are
    ver=`$p/bin/python$suff -c "import sys; print('%s%s' % sys.version_info[:2])"`
    echo The version is $ver

    # Make the virtualenv
    $p/bin/virtualenv$suff $ve/$ver

    # Activate the virtualenv
    source $ve/$ver/bin/activate

    # Install nose
    easy_install nose

    # Write the .pth file that lets us import our test zips.
    libdir=`echo $ve/$ver/lib/python*/site-packages/`
    echo `pwd`/test/eggsrc/dist/covtestegg1-0.0.0-py2.6.egg > $libdir/coverage_test_egg.pth

    # Install ourselves
    python setup.py develop
done
