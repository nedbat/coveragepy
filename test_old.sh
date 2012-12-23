# Steps to prepare and run coverage.py tests, for Pythons < 2.5
# This should do the same steps as tox.ini
easy_install nose==1.2.1 mock==0.6.0
python setup.py --quiet clean develop
python igor.py zip_mods install_egg remove_extension 
python igor.py test_with_tracer py
python setup.py --quiet build_ext --inplace
python igor.py test_with_tracer c
