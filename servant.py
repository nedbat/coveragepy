import os
import sys
import zipfile

from nose import core as nose_core

if sys.argv[1] == "remove_extension":
    so_names = """
        tracer.so
        tracer.cpython-32m.so
        """.split()

    for filename in so_names:
        try:
            os.remove(os.path.join("coverage", filename))
        except OSError:
            pass

elif sys.argv[1] == "test_with_tracer":
    os.environ["COVERAGE_TEST_TRACER"] = sys.argv[2]
    del sys.argv[1:3]
    nose_core.main()

elif sys.argv[1] == "zip_mods":
    zipfile.ZipFile("test/zipmods.zip", "w").write("test/covmodzip1.py", "covmodzip1.py")
