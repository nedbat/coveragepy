import os
import sys
import zipfile

from nose import core as nose_core

if sys.argv[1] == "remove_extension":
    try:
        os.remove("coverage/tracer.so")
    except OSError:
        pass

elif sys.argv[1] == "test_with_tracer":
    os.environ["COVERAGE_TEST_TRACER"] = sys.argv[2]
    del sys.argv[1:3]
    nose_core.main()

elif sys.argv[1] == "zip_mods":
    zipfile.ZipFile("test/zipmods.zip", "w").write("test/covmodzip1.py", "covmodzip1.py")
