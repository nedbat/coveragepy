/* Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0 */
/* For details: https://github.com/nedbat/coveragepy/blob/master/NOTICE.txt */

#ifndef _COVERAGE_UTIL_H
#define _COVERAGE_UTIL_H

#include <Python.h>

/* Compile-time debugging helpers */
#undef WHAT_LOG         /* Define to log the WHAT params in the trace function. */
#undef TRACE_LOG        /* Define to log our bookkeeping. */
#undef COLLECT_STATS    /* Collect counters: stats are printed when tracer is stopped. */
#undef DO_NOTHING       /* Define this to make the tracer do nothing. */

static inline Py_ssize_t MyFrame_lasti(PyFrameObject *frame)
{
    PyObject *obj = PyObject_GetAttrString((PyObject*)frame, "f_lasti");
    if (obj == NULL) {
        PyErr_Clear();
        return -1;
    }
    // f_lasti is an int, but using Py_ssize_t is more convenient in coverage
    Py_ssize_t lasti = PyLong_AsSsize_t(obj);
    if (lasti == -1 && PyErr_Occurred()) {
        PyErr_Clear();
        return -1;
    }
    return lasti;
}

// Access f_code should be done through a helper starting in 3.9.
#if PY_VERSION_HEX >= 0x03090000
#define MyFrame_GetCode(f)      (PyFrame_GetCode(f))
#else
#define MyFrame_GetCode(f)      ((f)->f_code)
#endif

/* The values returned to indicate ok or error. */
#define RET_OK      0
#define RET_ERROR   -1

/* Nicer booleans */
typedef int BOOL;
#define FALSE   0
#define TRUE    1

#if SIZEOF_LONG_LONG < 8
#error long long too small!
#endif
typedef unsigned long long uint64;

/* Only for extreme machete-mode debugging! */
#define CRASH       { printf("*** CRASH! ***\n"); *((int*)1) = 1; }

#endif /* _COVERAGE_UTIL_H */
