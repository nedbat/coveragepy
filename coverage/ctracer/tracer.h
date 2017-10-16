/* Licensed under the Apache License: http://www.apache.org/licenses/LICENSE-2.0 */
/* For details: https://bitbucket.org/ned/coveragepy/src/default/NOTICE.txt */

#ifndef _COVERAGE_TRACER_H
#define _COVERAGE_TRACER_H

#include "util.h"
#include "structmember.h"
#include "frameobject.h"
#include "opcode.h"
#include <stdint.h>

#include "datastack.h"


/*
We use normal Python objects as keys for writing into the file_data
dictionaries.

This ends up creating the same duplicate objects over and over again inside the
hot loop of the trace function, which is not ideal!

In order to avoid that, we intern our keys global to the tracer. This means
that in the common case where the tracer has already seen the key somewhere we
don't need to allocate a new one. This can significantly speed up tracing.
*/
typedef struct InternEntry {
    uint64_t key;
    PyObject *value;
} InternEntry;

typedef struct InternTable {
    /* Store the value keyed off zero separately. This allows us to use a key
       of zero as a not-set indicator. */ 
    PyObject * zero_value;

    /* The number of elements in our entries array (including absent elements).
       Always a power of two. */
    size_t capacity;

    /* The number of entries which have a key set. Always strictly less than
       capacity. Does not count the zero key. */
    size_t current_fill;

    /* When the fill exceeds this value, increase the capacity. Always roughly
       the same fraction of capacity. */
    size_t max_fill;

    /* Essentially (key, value) tuples where keys are uint64_t and values are
      *PyObject. Values are owned by the tracer and will have their refcount
      decremented appropriately on release.*/
    InternEntry * entries;
} InternTable;


/* We expose a Python interface to the InternTable, but it's purely intended for
   purposes of testing the InternTable itself and you shouldn't use it for anything
   else.
*/
typedef struct InternTableObject{
    PyObject_HEAD
    InternTable table;
} InternTableObject;

/* The CTracer type. */

typedef struct CTracer {
    PyObject_HEAD

    /* Python objects manipulated directly by the Collector class. */
    PyObject * should_trace;
    PyObject * check_include;
    PyObject * warn;
    PyObject * concur_id_func;
    PyObject * data;
    PyObject * file_tracers;
    PyObject * should_trace_cache;
    PyObject * trace_arcs;
    PyObject * should_start_context;
    PyObject * switch_context;
    PyObject * context;

    /* Has the tracer been started? */
    BOOL started;
    /* Are we tracing arcs, or just lines? */
    BOOL tracing_arcs;
    /* Have we had any activity? */
    BOOL activity;

    /*
        The data stack is a stack of dictionaries.  Each dictionary collects
        data for a single source file.  The data stack parallels the call stack:
        each call pushes the new frame's file data onto the data stack, and each
        return pops file data off.

        The file data is a dictionary whose form depends on the tracing options.
        If tracing arcs, the keys are line number pairs.  If not tracing arcs,
        the keys are line numbers.  In both cases, the value is irrelevant
        (None).
    */

    DataStack data_stack;           /* Used if we aren't doing concurrency. */

    PyObject * data_stack_index;    /* Used if we are doing concurrency. */
    DataStack * data_stacks;
    int data_stacks_alloc;
    int data_stacks_used;
    DataStack * pdata_stack;

    /* The current file's data stack entry. */
    DataStackEntry * pcur_entry;

    /* The parent frame for the last exception event, to fix missing returns. */
    PyFrameObject * last_exc_back;
    int last_exc_firstlineno;

    Stats stats;

    InternTable intern_table;
} CTracer;

int CTracer_intern_strings(void);

extern PyTypeObject CTracerType;
extern PyTypeObject InternTableType;

#endif /* _COVERAGE_TRACER_H */
