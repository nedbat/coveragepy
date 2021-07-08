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

// The f_lasti field changed meaning in 3.10.0a7. It had been bytes, but
// now is instructions, so we need to adjust it to use it as a byte index.
#if PY_VERSION_HEX >= 0x030A00A7
#define MyFrame_lasti(f)    (f->f_lasti * 2)
#else
#define MyFrame_lasti(f)    f->f_lasti
#endif // 3.10.0a7

// Access f_code should be done through a helper starting in 3.9.
#if PY_VERSION_HEX >= 0x03090000
#define MyFrame_GetCode(f)      (PyFrame_GetCode(f))
#else
#define MyFrame_GetCode(f)      ((f)->f_code)
#endif // 3.11

/* The values returned to indicate ok or error. */
#define RET_OK      0
#define RET_ERROR   -1

/* Nicer booleans */
typedef int BOOL;
#define FALSE   0
#define TRUE    1

/* Only for extreme machete-mode debugging! */
#define CRASH       { printf("*** CRASH! ***\n"); *((int*)1) = 1; }

#endif /* _COVERAGE_UTIL_H */
