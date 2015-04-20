/* C-based Tracer for Coverage. */

#include "Python.h"
#include "structmember.h"
#include "frameobject.h"
#include "opcode.h"

/* Compile-time debugging helpers */
#undef WHAT_LOG         /* Define to log the WHAT params in the trace function. */
#undef TRACE_LOG        /* Define to log our bookkeeping. */
#undef COLLECT_STATS    /* Collect counters: stats are printed when tracer is stopped. */

#if COLLECT_STATS
#define STATS(x)        x
#else
#define STATS(x)
#endif

/* Py 2.x and 3.x compatibility */

#if PY_MAJOR_VERSION >= 3

#define MyText_Type         PyUnicode_Type
#define MyText_AS_BYTES(o)  PyUnicode_AsASCIIString(o)
#define MyBytes_AS_STRING(o) PyBytes_AS_STRING(o)
#define MyText_AsString(o)  PyUnicode_AsUTF8(o)
#define MyText_FromFormat   PyUnicode_FromFormat
#define MyInt_FromInt(i)    PyLong_FromLong((long)i)
#define MyInt_AsInt(o)      (int)PyLong_AsLong(o)

#define MyType_HEAD_INIT    PyVarObject_HEAD_INIT(NULL, 0)

#else

#define MyText_Type         PyString_Type
#define MyText_AS_BYTES(o)  (Py_INCREF(o), o)
#define MyBytes_AS_STRING(o) PyString_AS_STRING(o)
#define MyText_AsString(o)  PyString_AsString(o)
#define MyText_FromFormat   PyUnicode_FromFormat
#define MyInt_FromInt(i)    PyInt_FromLong((long)i)
#define MyInt_AsInt(o)      (int)PyInt_AsLong(o)

#define MyType_HEAD_INIT    PyObject_HEAD_INIT(NULL)  0,

#endif /* Py3k */

/* The values returned to indicate ok or error. */
#define RET_OK      0
#define RET_ERROR   -1

/* Python C API helpers. */

static int
pyint_as_int(PyObject * pyint, int *pint)
{
    int the_int = MyInt_AsInt(pyint);
    if (the_int == -1 && PyErr_Occurred()) {
        return RET_ERROR;
    }

    *pint = the_int;
    return RET_OK;
}


/* An entry on the data stack.  For each call frame, we need to record all
 * the information needed for CTracer_handle_line to operate as quickly as
 * possible.
 */
typedef struct {
    /* The current file_data dictionary.  Borrowed, owned by self->data. */
    PyObject * file_data;

    /* The disposition object for this frame. */
    PyObject * disposition;

    /* The FileTracer handling this frame, or None if it's Python. */
    PyObject * file_tracer;

    /* The line number of the last line recorded, for tracing arcs.
        -1 means there was no previous line, as when entering a code object.
    */
    int last_line;
} DataStackEntry;

/* A data stack is a dynamically allocated vector of DataStackEntry's. */
typedef struct {
    int depth;      /* The index of the last-used entry in stack. */
    int alloc;      /* number of entries allocated at stack. */
    /* The file data at each level, or NULL if not recording. */
    DataStackEntry * stack;
} DataStack;

/* The CTracer type. */

typedef struct {
    PyObject_HEAD

    /* Python objects manipulated directly by the Collector class. */
    PyObject * should_trace;
    PyObject * check_include;
    PyObject * warn;
    PyObject * concur_id_func;
    PyObject * data;
    PyObject * plugin_data;
    PyObject * should_trace_cache;
    PyObject * arcs;

    /* Has the tracer been started? */
    int started;
    /* Are we tracing arcs, or just lines? */
    int tracing_arcs;

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

    /* The current file's data stack entry, copied from the stack. */
    DataStackEntry cur_entry;

    /* The parent frame for the last exception event, to fix missing returns. */
    PyFrameObject * last_exc_back;
    int last_exc_firstlineno;

#if COLLECT_STATS
    struct {
        unsigned int calls;
        unsigned int lines;
        unsigned int returns;
        unsigned int exceptions;
        unsigned int others;
        unsigned int new_files;
        unsigned int missed_returns;
        unsigned int stack_reallocs;
        unsigned int errors;
    } stats;
#endif /* COLLECT_STATS */
} CTracer;


#define STACK_DELTA    100

static int
DataStack_init(CTracer *self, DataStack *pdata_stack)
{
    pdata_stack->depth = -1;
    pdata_stack->stack = NULL;
    pdata_stack->alloc = 0;
    return RET_OK;
}

static void
DataStack_dealloc(CTracer *self, DataStack *pdata_stack)
{
    PyMem_Free(pdata_stack->stack);
}

static int
DataStack_grow(CTracer *self, DataStack *pdata_stack)
{
    pdata_stack->depth++;
    if (pdata_stack->depth >= pdata_stack->alloc) {
        STATS( self->stats.stack_reallocs++; )
        /* We've outgrown our data_stack array: make it bigger. */
        int bigger = pdata_stack->alloc + STACK_DELTA;
        DataStackEntry * bigger_data_stack = PyMem_Realloc(pdata_stack->stack, bigger * sizeof(DataStackEntry));
        if (bigger_data_stack == NULL) {
            PyErr_NoMemory();
            pdata_stack->depth--;
            return RET_ERROR;
        }
        pdata_stack->stack = bigger_data_stack;
        pdata_stack->alloc = bigger;
    }
    return RET_OK;
}


static void CTracer_disable_plugin(CTracer *self, PyObject * disposition);

static int
CTracer_init(CTracer *self, PyObject *args_unused, PyObject *kwds_unused)
{
    int ret = RET_ERROR;
    PyObject * weakref = NULL;

    if (DataStack_init(self, &self->data_stack) < 0) {
        goto error;
    }

    weakref = PyImport_ImportModule("weakref");
    if (weakref == NULL) {
        goto error;
    }
    self->data_stack_index = PyObject_CallMethod(weakref, "WeakKeyDictionary", NULL);
    Py_XDECREF(weakref);

    if (self->data_stack_index == NULL) {
        goto error;
    }

    self->pdata_stack = &self->data_stack;

    self->cur_entry.last_line = -1;

    ret = RET_OK;
    goto ok;

error:
    STATS( self->stats.errors++; )

ok:
    return ret;
}

static void
CTracer_dealloc(CTracer *self)
{
    int i;

    if (self->started) {
        PyEval_SetTrace(NULL, NULL);
    }

    Py_XDECREF(self->should_trace);
    Py_XDECREF(self->check_include);
    Py_XDECREF(self->warn);
    Py_XDECREF(self->concur_id_func);
    Py_XDECREF(self->data);
    Py_XDECREF(self->plugin_data);
    Py_XDECREF(self->should_trace_cache);

    DataStack_dealloc(self, &self->data_stack);
    if (self->data_stacks) {
        for (i = 0; i < self->data_stacks_used; i++) {
            DataStack_dealloc(self, self->data_stacks + i);
        }
        PyMem_Free(self->data_stacks);
    }

    Py_XDECREF(self->data_stack_index);

    Py_TYPE(self)->tp_free((PyObject*)self);
}

#if TRACE_LOG
static const char *
indent(int n)
{
    static const char * spaces =
        "                                                                    "
        "                                                                    "
        "                                                                    "
        "                                                                    "
        ;
    return spaces + strlen(spaces) - n*2;
}

static int logging = 0;
/* Set these constants to be a file substring and line number to start logging. */
static const char * start_file = "tests/views";
static int start_line = 27;

static void
showlog(int depth, int lineno, PyObject * filename, const char * msg)
{
    if (logging) {
        printf("%s%3d ", indent(depth), depth);
        if (lineno) {
            printf("%4d", lineno);
        }
        else {
            printf("    ");
        }
        if (filename) {
            PyObject *ascii = MyText_AS_BYTES(filename);
            printf(" %s", MyBytes_AS_STRING(ascii));
            Py_DECREF(ascii);
        }
        if (msg) {
            printf(" %s", msg);
        }
        printf("\n");
    }
}

#define SHOWLOG(a,b,c,d)    showlog(a,b,c,d)
#else
#define SHOWLOG(a,b,c,d)
#endif /* TRACE_LOG */

#if WHAT_LOG
static const char * what_sym[] = {"CALL", "EXC ", "LINE", "RET "};
#endif

/* Record a pair of integers in self->cur_entry.file_data. */
static int
CTracer_record_pair(CTracer *self, int l1, int l2)
{
    int ret = RET_ERROR;

    PyObject * t = NULL;

    t = Py_BuildValue("(ii)", l1, l2);
    if (t == NULL) {
        goto error;
    }

    if (PyDict_SetItem(self->cur_entry.file_data, t, Py_None) < 0) {
        goto error;
    }

    ret = RET_OK;

error:
    Py_XDECREF(t);

    return ret;
}

/* Set self->pdata_stack to the proper data_stack to use. */
static int
CTracer_set_pdata_stack(CTracer *self)
{
    int ret = RET_ERROR;
    PyObject * co_obj = NULL;
    PyObject * stack_index = NULL;

    if (self->concur_id_func != Py_None) {
        int the_index = 0;

        co_obj = PyObject_CallObject(self->concur_id_func, NULL);
        if (co_obj == NULL) {
            goto error;
        }
        stack_index = PyObject_GetItem(self->data_stack_index, co_obj);
        if (stack_index == NULL) {
            /* PyObject_GetItem sets an exception if it didn't find the thing. */
            PyErr_Clear();

            /* A new concurrency object.  Make a new data stack. */
            the_index = self->data_stacks_used;
            stack_index = MyInt_FromInt(the_index);
            if (stack_index == NULL) {
                goto error;
            }
            if (PyObject_SetItem(self->data_stack_index, co_obj, stack_index) < 0) {
                goto error;
            }
            self->data_stacks_used++;
            if (self->data_stacks_used >= self->data_stacks_alloc) {
                int bigger = self->data_stacks_alloc + 10;
                DataStack * bigger_stacks = PyMem_Realloc(self->data_stacks, bigger * sizeof(DataStack));
                if (bigger_stacks == NULL) {
                    PyErr_NoMemory();
                    goto error;
                }
                self->data_stacks = bigger_stacks;
                self->data_stacks_alloc = bigger;
            }
            DataStack_init(self, &self->data_stacks[the_index]);
        }
        else {
            if (pyint_as_int(stack_index, &the_index) < 0) {
                goto error;
            }
        }

        self->pdata_stack = &self->data_stacks[the_index];
    }
    else {
        self->pdata_stack = &self->data_stack;
    }

    ret = RET_OK;

error:

    Py_XDECREF(co_obj);
    Py_XDECREF(stack_index);

    return ret;
}

/*
 * Parts of the trace function.
 */

static int
CTracer_check_missing_return(CTracer *self, PyFrameObject *frame)
{
    int ret = RET_ERROR;

    if (self->last_exc_back) {
        if (frame == self->last_exc_back) {
            /* Looks like someone forgot to send a return event. We'll clear
               the exception state and do the RETURN code here.  Notice that the
               frame we have in hand here is not the correct frame for the RETURN,
               that frame is gone.  Our handling for RETURN doesn't need the
               actual frame, but we do log it, so that will look a little off if
               you're looking at the detailed log.

               If someday we need to examine the frame when doing RETURN, then
               we'll need to keep more of the missed frame's state.
            */
            STATS( self->stats.missed_returns++; )
            if (CTracer_set_pdata_stack(self) < 0) {
                goto error;
            }
            if (self->pdata_stack->depth >= 0) {
                if (self->tracing_arcs && self->cur_entry.file_data) {
                    if (CTracer_record_pair(self, self->cur_entry.last_line, -self->last_exc_firstlineno) < 0) {
                        goto error;
                    }
                }
                SHOWLOG(self->pdata_stack->depth, frame->f_lineno, frame->f_code->co_filename, "missedreturn");
                self->cur_entry = self->pdata_stack->stack[self->pdata_stack->depth];
                self->pdata_stack->depth--;
            }
        }
        self->last_exc_back = NULL;
    }

    ret = RET_OK;

error:

    return ret;
}

static int
CTracer_handle_call(CTracer *self, PyFrameObject *frame)
{
    int ret = RET_ERROR;
    int ret2;

    /* Owned references that we clean up at the very end of the function. */
    PyObject * tracename = NULL;
    PyObject * disposition = NULL;
    PyObject * disp_trace = NULL;
    PyObject * file_tracer = NULL;
    PyObject * plugin = NULL;
    PyObject * plugin_name = NULL;
    PyObject * has_dynamic_filename = NULL;

    /* Borrowed references. */
    PyObject * filename = NULL;


    STATS( self->stats.calls++; )
    /* Grow the stack. */
    if (CTracer_set_pdata_stack(self) < 0) {
        goto error;
    }
    if (DataStack_grow(self, self->pdata_stack) < 0) {
        goto error;
    }

    /* Push the current state on the stack. */
    self->pdata_stack->stack[self->pdata_stack->depth] = self->cur_entry;

    /* Check if we should trace this line. */
    filename = frame->f_code->co_filename;
    disposition = PyDict_GetItem(self->should_trace_cache, filename);
    if (disposition == NULL) {
        if (PyErr_Occurred()) {
            goto error;
        }
        STATS( self->stats.new_files++; )
        /* We've never considered this file before. */
        /* Ask should_trace about it. */
        disposition = PyObject_CallFunctionObjArgs(self->should_trace, filename, frame, NULL);
        if (disposition == NULL) {
            /* An error occurred inside should_trace. */
            goto error;
        }
        if (PyDict_SetItem(self->should_trace_cache, filename, disposition) < 0) {
            goto error;
        }
    }
    else {
        Py_INCREF(disposition);
    }

    disp_trace = PyObject_GetAttrString(disposition, "trace");
    if (disp_trace == NULL) {
        goto error;
    }

    if (disp_trace == Py_True) {
        /* If tracename is a string, then we're supposed to trace. */
        tracename = PyObject_GetAttrString(disposition, "source_filename");
        if (tracename == NULL) {
            goto error;
        }
        file_tracer = PyObject_GetAttrString(disposition, "file_tracer");
        if (file_tracer == NULL) {
            goto error;
        }
        if (file_tracer != Py_None) {
            plugin = PyObject_GetAttrString(file_tracer, "_coverage_plugin");
            if (plugin == NULL) {
                goto error;
            }
            plugin_name = PyObject_GetAttrString(plugin, "_coverage_plugin_name");
            if (plugin_name == NULL) {
                goto error;
            }
        }
        has_dynamic_filename = PyObject_GetAttrString(disposition, "has_dynamic_filename");
        if (has_dynamic_filename == NULL) {
            goto error;
        }
        if (has_dynamic_filename == Py_True) {
            PyObject * next_tracename = NULL;
            next_tracename = PyObject_CallMethod(
                file_tracer, "dynamic_source_filename",
                "OO", tracename, frame
                );
            if (next_tracename == NULL) {
                /* An exception from the function. Alert the user with a
                 * warning and a traceback.
                 */
                CTracer_disable_plugin(self, disposition);
                /* Because we handled the error, goto ok. */
                goto ok;
            }
            Py_DECREF(tracename);
            tracename = next_tracename;

            if (tracename != Py_None) {
                /* Check the dynamic source filename against the include rules. */
                PyObject * included = NULL;
                included = PyDict_GetItem(self->should_trace_cache, tracename);
                if (included == NULL) {
                    if (PyErr_Occurred()) {
                        goto error;
                    }
                    STATS( self->stats.new_files++; )
                    included = PyObject_CallFunctionObjArgs(self->check_include, tracename, frame, NULL);
                    if (included == NULL) {
                        goto error;
                    }
                    if (PyDict_SetItem(self->should_trace_cache, tracename, included) < 0) {
                        goto error;
                    }
                }
                if (included != Py_True) {
                    Py_DECREF(tracename);
                    tracename = Py_None;
                    Py_INCREF(tracename);
                }
            }
        }
    }
    else {
        tracename = Py_None;
        Py_INCREF(tracename);
    }

    if (tracename != Py_None) {
        PyObject * file_data = PyDict_GetItem(self->data, tracename);

        if (file_data == NULL) {
            if (PyErr_Occurred()) {
                goto error;
            }
            file_data = PyDict_New();
            if (file_data == NULL) {
                goto error;
            }
            ret2 = PyDict_SetItem(self->data, tracename, file_data);
            Py_DECREF(file_data);
            if (ret2 < 0) {
                goto error;
            }

            /* If the disposition mentions a plugin, record that. */
            if (file_tracer != Py_None) {
                ret2 = PyDict_SetItem(self->plugin_data, tracename, plugin_name);
                if (ret2 < 0) {
                    goto error;
                }
            }
        }

        self->cur_entry.file_data = file_data;
        self->cur_entry.file_tracer = file_tracer;

        /* Make the frame right in case settrace(gettrace()) happens. */
        Py_INCREF(self);
        frame->f_trace = (PyObject*)self;
        SHOWLOG(self->pdata_stack->depth, frame->f_lineno, filename, "traced");
    }
    else {
        self->cur_entry.file_data = NULL;
        self->cur_entry.file_tracer = Py_None;
        SHOWLOG(self->pdata_stack->depth, frame->f_lineno, filename, "skipped");
    }

<<<<<<< local
    self->cur_entry.disposition = disposition;
    self->cur_entry.last_line = -1;
=======
    /* A call event is really a "start frame" event, and can happen for
     * re-entering a generator also.  f_lasti is -1 for a true call, and a
     * real byte offset for a generator re-entry.
     */
    self->cur_entry.last_line = (frame->f_lasti < 0) ? -1 : frame->f_lineno;
>>>>>>> other

ok:
    ret = RET_OK;

error:
    Py_XDECREF(tracename);
    Py_XDECREF(disposition);
    Py_XDECREF(disp_trace);
    Py_XDECREF(file_tracer);
    Py_XDECREF(plugin);
    Py_XDECREF(plugin_name);
    Py_XDECREF(has_dynamic_filename);

    return ret;
}


static void
CTracer_disable_plugin(CTracer *self, PyObject * disposition)
{
    PyObject * file_tracer = NULL;
    PyObject * plugin = NULL;
    PyObject * plugin_name = NULL;
    PyObject * msg = NULL;
    PyObject * ignored = NULL;

    file_tracer = PyObject_GetAttrString(disposition, "file_tracer");
    if (file_tracer == NULL) {
        goto error;
    }
    if (file_tracer == Py_None) {
        /* This shouldn't happen... */
        goto ok;
    }
    plugin = PyObject_GetAttrString(file_tracer, "_coverage_plugin");
    if (plugin == NULL) {
        goto error;
    }
    plugin_name = PyObject_GetAttrString(plugin, "_coverage_plugin_name");
    if (plugin_name == NULL) {
        goto error;
    }
    msg = MyText_FromFormat(
        "Disabling plugin '%s' due to an exception:",
        MyText_AsString(plugin_name)
        );
    if (msg == NULL) {
        goto error;
    }
    ignored = PyObject_CallFunctionObjArgs(self->warn, msg, NULL);
    if (ignored == NULL) {
        goto error;
    }

    PyErr_Print();

    /* Disable the plugin for future files, and stop tracing this file. */
    if (PyObject_SetAttrString(plugin, "_coverage_enabled", Py_False) < 0) {
        goto error;
    }
    if (PyObject_SetAttrString(disposition, "trace", Py_False) < 0) {
        goto error;
    }

    goto ok;

error:
    /* This function doesn't return a status, so if an error happens, print it,
     * but don't interrupt the flow. */
    /* PySys_WriteStderr is nicer, but is not in the public API. */
    fprintf(stderr, "Error occurred while disabling plugin:\n");
    PyErr_Print();

ok:
    Py_XDECREF(file_tracer);
    Py_XDECREF(plugin);
    Py_XDECREF(plugin_name);
    Py_XDECREF(msg);
    Py_XDECREF(ignored);
}


static int
CTracer_unpack_pair(CTracer *self, PyObject *pair, int *p_one, int *p_two)
{
    int ret = RET_ERROR;
    int the_int;
    PyObject * pyint = NULL;
    int index;

    if (!PyTuple_Check(pair) || PyTuple_Size(pair) != 2) {
        PyErr_SetString(
            PyExc_TypeError,
            "line_number_range must return 2-tuple"
            );
        goto error;
    }

    for (index = 0; index < 2; index++) {
        pyint = PyTuple_GetItem(pair, index);
        if (pyint == NULL) {
            goto error;
        }
        if (pyint_as_int(pyint, &the_int) < 0) {
            goto error;
        }
        *(index == 0 ? p_one : p_two) = the_int;
    }

    ret = RET_OK;

error:
    return ret;
}

static int
CTracer_handle_line(CTracer *self, PyFrameObject *frame)
{
    int ret = RET_ERROR;
    int ret2;

    STATS( self->stats.lines++; )
    if (self->pdata_stack->depth >= 0) {
        SHOWLOG(self->pdata_stack->depth, frame->f_lineno, frame->f_code->co_filename, "line");
        if (self->cur_entry.file_data) {
            int lineno_from, lineno_to;

            /* We're tracing in this frame: record something. */
            if (self->cur_entry.file_tracer != Py_None) {
                PyObject * from_to = NULL;
                from_to = PyObject_CallMethod(self->cur_entry.file_tracer, "line_number_range", "O", frame);
                if (from_to == NULL) {
                    goto error;
                }
                ret2 = CTracer_unpack_pair(self, from_to, &lineno_from, &lineno_to);
                Py_DECREF(from_to);
                if (ret2 < 0) {
                    CTracer_disable_plugin(self, self->cur_entry.disposition);
                    goto ok;
                }
            }
            else {
                lineno_from = lineno_to = frame->f_lineno;
            }

            if (lineno_from != -1) {
                for (; lineno_from <= lineno_to; lineno_from++) {
                    if (self->tracing_arcs) {
                        /* Tracing arcs: key is (last_line,this_line). */
                        if (CTracer_record_pair(self, self->cur_entry.last_line, lineno_from) < 0) {
                            goto error;
                        }
                    }
                    else {
                        /* Tracing lines: key is simply this_line. */
                        PyObject * this_line = MyInt_FromInt(lineno_from);
                        if (this_line == NULL) {
                            goto error;
                        }

                        ret2 = PyDict_SetItem(self->cur_entry.file_data, this_line, Py_None);
                        Py_DECREF(this_line);
                        if (ret2 < 0) {
                            goto error;
                        }
                    }

                    self->cur_entry.last_line = lineno_from;
                }
            }
        }
    }

ok:
    ret = RET_OK;

error:

    return ret;
}

static int
CTracer_handle_return(CTracer *self, PyFrameObject *frame)
{
    int ret = RET_ERROR;

    STATS( self->stats.returns++; )
    /* A near-copy of this code is above in the missing-return handler. */
    if (CTracer_set_pdata_stack(self) < 0) {
        goto error;
    }
    if (self->pdata_stack->depth >= 0) {
        if (self->tracing_arcs && self->cur_entry.file_data) {
            /* Need to distinguish between RETURN_VALUE and YIELD_VALUE. */
            int bytecode = MyText_AS_STRING(frame->f_code->co_code)[frame->f_lasti];
            if (bytecode != YIELD_VALUE) {
                int first = frame->f_code->co_firstlineno;
                if (CTracer_record_pair(self, self->cur_entry.last_line, -first) < 0) {
                    goto error;
                }
            }
        }

        SHOWLOG(self->pdata_stack->depth, frame->f_lineno, frame->f_code->co_filename, "return");
        self->cur_entry = self->pdata_stack->stack[self->pdata_stack->depth];
        self->pdata_stack->depth--;
    }

    ret = RET_OK;

error:

    return ret;
}

static int
CTracer_handle_exception(CTracer *self, PyFrameObject *frame)
{
    /* Some code (Python 2.3, and pyexpat anywhere) fires an exception event
        without a return event.  To detect that, we'll keep a copy of the
        parent frame for an exception event.  If the next event is in that
        frame, then we must have returned without a return event.  We can
        synthesize the missing event then.

        Python itself fixed this problem in 2.4.  Pyexpat still has the bug.
        I've reported the problem with pyexpat as http://bugs.python.org/issue6359 .
        If it gets fixed, this code should still work properly.  Maybe some day
        the bug will be fixed everywhere coverage.py is supported, and we can
        remove this missing-return detection.

        More about this fix: http://nedbatchelder.com/blog/200907/a_nasty_little_bug.html
    */
    STATS( self->stats.exceptions++; )
    self->last_exc_back = frame->f_back;
    self->last_exc_firstlineno = frame->f_code->co_firstlineno;

    return RET_OK;
}

/*
 * The Trace Function
 */
static int
CTracer_trace(CTracer *self, PyFrameObject *frame, int what, PyObject *arg_unused)
{
    int ret = RET_ERROR;

    #if WHAT_LOG || TRACE_LOG
    PyObject * ascii = NULL;
    #endif

    #if WHAT_LOG
    if (what <= sizeof(what_sym)/sizeof(const char *)) {
        ascii = MyText_AS_BYTES(frame->f_code->co_filename);
        printf("trace: %s @ %s %d\n", what_sym[what], MyBytes_AS_STRING(ascii), frame->f_lineno);
        Py_DECREF(ascii);
    }
    #endif

    #if TRACE_LOG
    ascii = MyText_AS_BYTES(frame->f_code->co_filename);
    if (strstr(MyBytes_AS_STRING(ascii), start_file) && frame->f_lineno == start_line) {
        logging = 1;
    }
    Py_DECREF(ascii);
    #endif

    /* See below for details on missing-return detection. */
    if (CTracer_check_missing_return(self, frame) < 0) {
        goto error;
    }

    switch (what) {
    case PyTrace_CALL:
        if (CTracer_handle_call(self, frame) < 0) {
            goto error;
        }
        break;

    case PyTrace_RETURN:
        if (CTracer_handle_return(self, frame) < 0) {
            goto error;
        }
        break;

    case PyTrace_LINE:
        if (CTracer_handle_line(self, frame) < 0) {
            goto error;
        }
        break;

    case PyTrace_EXCEPTION:
        if (CTracer_handle_exception(self, frame) < 0) {
            goto error;
        }
        break;

    default:
        STATS( self->stats.others++; )
        break;
    }

    ret = RET_OK;
    goto cleanup;

error:
    STATS( self->stats.errors++; )

cleanup:
    return ret;
}


/*
 * Python has two ways to set the trace function: sys.settrace(fn), which
 * takes a Python callable, and PyEval_SetTrace(func, obj), which takes
 * a C function and a Python object.  The way these work together is that
 * sys.settrace(pyfn) calls PyEval_SetTrace(builtin_func, pyfn), using the
 * Python callable as the object in PyEval_SetTrace.  So sys.gettrace()
 * simply returns the Python object used as the second argument to
 * PyEval_SetTrace.  So sys.gettrace() will return our self parameter, which
 * means it must be callable to be used in sys.settrace().
 *
 * So we make our self callable, equivalent to invoking our trace function.
 *
 * To help with the process of replaying stored frames, this function has an
 * optional keyword argument:
 *
 *      def CTracer_call(frame, event, arg, lineno=0)
 *
 * If provided, the lineno argument is used as the line number, and the
 * frame's f_lineno member is ignored.
 */
static PyObject *
CTracer_call(CTracer *self, PyObject *args, PyObject *kwds)
{
    PyFrameObject *frame;
    PyObject *what_str;
    PyObject *arg;
    int lineno = 0;
    int what;
    int orig_lineno;
    PyObject *ret = NULL;

    static char *what_names[] = {
        "call", "exception", "line", "return",
        "c_call", "c_exception", "c_return",
        NULL
        };

    #if WHAT_LOG
    printf("pytrace\n");
    #endif

    static char *kwlist[] = {"frame", "event", "arg", "lineno", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O!O!O|i:Tracer_call", kwlist,
            &PyFrame_Type, &frame, &MyText_Type, &what_str, &arg, &lineno)) {
        goto done;
    }

    /* In Python, the what argument is a string, we need to find an int
       for the C function. */
    for (what = 0; what_names[what]; what++) {
        PyObject *ascii = MyText_AS_BYTES(what_str);
        int should_break = !strcmp(MyBytes_AS_STRING(ascii), what_names[what]);
        Py_DECREF(ascii);
        if (should_break) {
            break;
        }
    }

    /* Save off the frame's lineno, and use the forced one, if provided. */
    orig_lineno = frame->f_lineno;
    if (lineno > 0) {
        frame->f_lineno = lineno;
    }

    /* Invoke the C function, and return ourselves. */
    if (CTracer_trace(self, frame, what, arg) == RET_OK) {
        Py_INCREF(self);
        ret = (PyObject *)self;
    }

    /* Clean up. */
    frame->f_lineno = orig_lineno;

done:
    return ret;
}

static PyObject *
CTracer_start(CTracer *self, PyObject *args_unused)
{
    PyEval_SetTrace((Py_tracefunc)CTracer_trace, (PyObject*)self);
    self->started = 1;
    self->tracing_arcs = self->arcs && PyObject_IsTrue(self->arcs);
    self->cur_entry.last_line = -1;

    /* start() returns a trace function usable with sys.settrace() */
    Py_INCREF(self);
    return (PyObject *)self;
}

static PyObject *
CTracer_stop(CTracer *self, PyObject *args_unused)
{
    if (self->started) {
        PyEval_SetTrace(NULL, NULL);
        self->started = 0;
    }

    Py_RETURN_NONE;
}

static PyObject *
CTracer_get_stats(CTracer *self)
{
#if COLLECT_STATS
    return Py_BuildValue(
        "{sI,sI,sI,sI,sI,sI,sI,sI,si,sI}",
        "calls", self->stats.calls,
        "lines", self->stats.lines,
        "returns", self->stats.returns,
        "exceptions", self->stats.exceptions,
        "others", self->stats.others,
        "new_files", self->stats.new_files,
        "missed_returns", self->stats.missed_returns,
        "stack_reallocs", self->stats.stack_reallocs,
        "stack_alloc", self->pdata_stack->alloc,
        "errors", self->stats.errors
        );
#else
    Py_RETURN_NONE;
#endif /* COLLECT_STATS */
}

static PyMemberDef
CTracer_members[] = {
    { "should_trace",       T_OBJECT, offsetof(CTracer, should_trace), 0,
            PyDoc_STR("Function indicating whether to trace a file.") },

    { "check_include",      T_OBJECT, offsetof(CTracer, check_include), 0,
            PyDoc_STR("Function indicating whether to include a file.") },

    { "warn",               T_OBJECT, offsetof(CTracer, warn), 0,
            PyDoc_STR("Function for issuing warnings.") },

    { "concur_id_func",     T_OBJECT, offsetof(CTracer, concur_id_func), 0,
            PyDoc_STR("Function for determining concurrency context") },

    { "data",               T_OBJECT, offsetof(CTracer, data), 0,
            PyDoc_STR("The raw dictionary of trace data.") },

    { "plugin_data",        T_OBJECT, offsetof(CTracer, plugin_data), 0,
            PyDoc_STR("Mapping from filename to plugin name.") },

    { "should_trace_cache", T_OBJECT, offsetof(CTracer, should_trace_cache), 0,
            PyDoc_STR("Dictionary caching should_trace results.") },

    { "arcs",               T_OBJECT, offsetof(CTracer, arcs), 0,
            PyDoc_STR("Should we trace arcs, or just lines?") },

    { NULL }
};

static PyMethodDef
CTracer_methods[] = {
    { "start",      (PyCFunction) CTracer_start,        METH_VARARGS,
            PyDoc_STR("Start the tracer") },

    { "stop",       (PyCFunction) CTracer_stop,         METH_VARARGS,
            PyDoc_STR("Stop the tracer") },

    { "get_stats",  (PyCFunction) CTracer_get_stats,    METH_VARARGS,
            PyDoc_STR("Get statistics about the tracing") },

    { NULL }
};

static PyTypeObject
CTracerType = {
    MyType_HEAD_INIT
    "coverage.CTracer",        /*tp_name*/
    sizeof(CTracer),           /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)CTracer_dealloc, /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    (ternaryfunc)CTracer_call, /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
    "CTracer objects",         /* tp_doc */
    0,                         /* tp_traverse */
    0,                         /* tp_clear */
    0,                         /* tp_richcompare */
    0,                         /* tp_weaklistoffset */
    0,                         /* tp_iter */
    0,                         /* tp_iternext */
    CTracer_methods,           /* tp_methods */
    CTracer_members,           /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)CTracer_init,    /* tp_init */
    0,                         /* tp_alloc */
    0,                         /* tp_new */
};

/* Module definition */

#define MODULE_DOC PyDoc_STR("Fast coverage tracer.")

#if PY_MAJOR_VERSION >= 3

static PyModuleDef
moduledef = {
    PyModuleDef_HEAD_INIT,
    "coverage.tracer",
    MODULE_DOC,
    -1,
    NULL,       /* methods */
    NULL,
    NULL,       /* traverse */
    NULL,       /* clear */
    NULL
};


PyObject *
PyInit_tracer(void)
{
    PyObject * mod = PyModule_Create(&moduledef);
    if (mod == NULL) {
        return NULL;
    }

    CTracerType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&CTracerType) < 0) {
        Py_DECREF(mod);
        return NULL;
    }

    Py_INCREF(&CTracerType);
    if (PyModule_AddObject(mod, "CTracer", (PyObject *)&CTracerType) < 0) {
        Py_DECREF(mod);
        Py_DECREF(&CTracerType);
        return NULL;
    }

    return mod;
}

#else

void
inittracer(void)
{
    PyObject * mod;

    mod = Py_InitModule3("coverage.tracer", NULL, MODULE_DOC);
    if (mod == NULL) {
        return;
    }

    CTracerType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&CTracerType) < 0) {
        return;
    }

    Py_INCREF(&CTracerType);
    PyModule_AddObject(mod, "CTracer", (PyObject *)&CTracerType);
}

#endif /* Py3k */
