/* C-based Tracer for Coverage. */

#include "Python.h"
#include "compile.h"        /* in 2.3, this wasn't part of Python.h */
#include "eval.h"           /* or this. */
#include "structmember.h"
#include "frameobject.h"

#undef WHAT_LOG     /* Define to log the WHAT params in the trace function. */
#undef TRACE_LOG    /* Define to log our bookkeeping. */

/* Py 2.x and 3.x compatibility */

#ifndef Py_TYPE
#define Py_TYPE(o)    (((PyObject*)(o))->ob_type)
#endif

#if PY_MAJOR_VERSION >= 3

#define MyText_Check(o)     PyUnicode_Check(o)
#define MyText_AS_STRING(o) FOOEY_DONT_KNOW_YET(o)
#define MyInt_FromLong(l)   PyLong_FromLong(l)

#define MyType_HEAD_INIT    PyVarObject_HEAD_INIT(NULL, 0)

#else

#define MyText_Check(o)     PyString_Check(o)
#define MyText_AS_STRING(o) PyString_AS_STRING(o)
#define MyInt_FromLong(l)   PyInt_FromLong(l)

#define MyType_HEAD_INIT    PyObject_HEAD_INIT(NULL)  0,

#endif /* Py3k */


/* The Tracer type. */

typedef struct {
    PyObject_HEAD
    PyObject * should_trace;
    PyObject * data;
    PyObject * should_trace_cache;
    PyObject * branch;
    int started;
    /* The index of the last-used entry in tracenames. */
    int depth;
    /* Filenames to record at each level, or NULL if not recording. */
    PyObject ** tracenames;     /* PyMem_Malloc'ed. */
    int tracenames_alloc;       /* number of entries at tracenames. */
    
    /* The parent frame for the last exception event, to fix missing returns. */
    PyFrameObject * last_exc_back;
} Tracer;

#define TRACENAMES_DELTA    100

static int
Tracer_init(Tracer *self, PyObject *args, PyObject *kwds)
{
    self->should_trace = NULL;
    self->data = NULL;
    self->should_trace_cache = NULL;
    self->started = 0;
    self->depth = -1;
    self->tracenames = PyMem_Malloc(TRACENAMES_DELTA*sizeof(PyObject *));
    if (self->tracenames == NULL) {
        return -1;
    }
    self->tracenames_alloc = TRACENAMES_DELTA;
    self->last_exc_back = NULL;
    return 0;
}

static void
Tracer_dealloc(Tracer *self)
{
    if (self->started) {
        PyEval_SetTrace(NULL, NULL);
    }

    Py_XDECREF(self->should_trace);
    Py_XDECREF(self->data);
    Py_XDECREF(self->should_trace_cache);

    while (self->depth >= 0) {
        Py_XDECREF(self->tracenames[self->depth]);
        self->depth--;
    }
    
    PyMem_Free(self->tracenames);

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
            printf(" %s", MyText_AS_STRING(filename));
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

static int
Tracer_trace(Tracer *self, PyFrameObject *frame, int what, PyObject *arg)
{
    PyObject * filename = NULL;
    PyObject * tracename = NULL;

    #if WHAT_LOG 
    if (what <= sizeof(what_sym)/sizeof(const char *)) {
        printf("trace: %s @ %s %d\n", what_sym[what], MyText_AS_STRING(frame->f_code->co_filename), frame->f_lineno);
    }
    #endif 

    #if TRACE_LOG
    if (strstr(MyText_AS_STRING(frame->f_code->co_filename), start_file) && frame->f_lineno == start_line) {
        logging = 1;
    }
    #endif

    /* See below for details on missing-return detection. */
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
            if (self->depth >= 0) {
                SHOWLOG(self->depth, frame->f_lineno, frame->f_code->co_filename, "missedreturn");
                Py_XDECREF(self->tracenames[self->depth]);
                self->depth--;
            }
        }
        self->last_exc_back = NULL;
    }
    

    switch (what) {
    case PyTrace_CALL:      /* 0 */
        self->depth++;
        if (self->depth >= self->tracenames_alloc) {
            /* We've outgrown our tracenames array: make it bigger. */
            int bigger = self->tracenames_alloc + TRACENAMES_DELTA;
            PyObject ** bigger_tracenames = PyMem_Realloc(self->tracenames, bigger * sizeof(PyObject *));
            if (bigger_tracenames == NULL) {
                self->depth--;
                return -1;
            }
            self->tracenames = bigger_tracenames;
            self->tracenames_alloc = bigger;
        }
        /* Check if we should trace this line. */
        filename = frame->f_code->co_filename;
        tracename = PyDict_GetItem(self->should_trace_cache, filename);
        if (tracename == NULL) {
            /* We've never considered this file before. */
            /* Ask should_trace about it. */
            PyObject * args = Py_BuildValue("(OO)", filename, frame);
            tracename = PyObject_Call(self->should_trace, args, NULL);
            Py_DECREF(args);
            if (tracename == NULL) {
                /* An error occurred inside should_trace. */
                return -1;
            }
            PyDict_SetItem(self->should_trace_cache, filename, tracename);
        }
        else {
            Py_INCREF(tracename);
        }

        /* If tracename is a string, then we're supposed to trace. */
        if (MyText_Check(tracename)) {
            self->tracenames[self->depth] = tracename;
            SHOWLOG(self->depth, frame->f_lineno, filename, "traced");
        }
        else {
            self->tracenames[self->depth] = NULL;
            Py_DECREF(tracename);
            SHOWLOG(self->depth, frame->f_lineno, filename, "skipped");
        }
        break;
    
    case PyTrace_RETURN:    /* 3 */
        /* A near-copy of this code is above in the missing-return handler. */
        if (self->depth >= 0) {
            SHOWLOG(self->depth, frame->f_lineno, frame->f_code->co_filename, "return");
            Py_XDECREF(self->tracenames[self->depth]);
            self->depth--;
        }
        break;
    
    case PyTrace_LINE:      /* 2 */
        if (self->depth >= 0) {
            SHOWLOG(self->depth, frame->f_lineno, frame->f_code->co_filename, "line");
            if (self->tracenames[self->depth]) {
                PyObject * t = PyTuple_New(2);
                tracename = self->tracenames[self->depth];
                Py_INCREF(tracename);
                PyTuple_SET_ITEM(t, 0, tracename);
                PyTuple_SET_ITEM(t, 1, MyInt_FromLong(frame->f_lineno));
                PyDict_SetItem(self->data, t, Py_None);
                Py_DECREF(t);
            }
        }
        break;
    
    case PyTrace_EXCEPTION:
        /* Some code (Python 2.3, and pyexpat anywhere) fires an exception event
           without a return event.  To detect that, we'll keep a copy of the
           parent frame for an exception event.  If the next event is in that
           frame, then we must have returned without a return event.  We can
           synthesize the missing event then.
           
           Python itself fixed this problem in 2.4.  Pyexpat still has the bug.
           I've reported the problem with pyexpat as http://bugs.python.org/issue6359 .
           If it gets fixed, this code should still work properly.  Maybe someday
           the bug will be fixed everywhere coverage.py is supported, and we can
           remove this missing-return detection.
           
           More about this fix: http://nedbatchelder.com/blog/200907/a_nasty_little_bug.html
        */
        self->last_exc_back = frame->f_back;
        break;
    }

    return 0;
}

static PyObject *
Tracer_start(Tracer *self, PyObject *args)
{
    PyEval_SetTrace((Py_tracefunc)Tracer_trace, (PyObject*)self);
    self->started = 1;
    return Py_BuildValue("");
}

static PyObject *
Tracer_stop(Tracer *self, PyObject *args)
{
    if (self->started) {
        PyEval_SetTrace(NULL, NULL);
        self->started = 0;
    }
    return Py_BuildValue("");
}

static PyMemberDef
Tracer_members[] = {
    { "should_trace",       T_OBJECT, offsetof(Tracer, should_trace), 0,
            PyDoc_STR("Function indicating whether to trace a file.") },

    { "data",               T_OBJECT, offsetof(Tracer, data), 0,
            PyDoc_STR("The raw dictionary of trace data.") },

    { "should_trace_cache", T_OBJECT, offsetof(Tracer, should_trace_cache), 0,
            PyDoc_STR("Dictionary caching should_trace results.") },

    { "branch",             T_OBJECT, offsetof(Tracer, branch), 0,
            PyDoc_STR("Should we trace branches?") },

    { NULL }
};

static PyMethodDef
Tracer_methods[] = {
    { "start",  (PyCFunction) Tracer_start, METH_VARARGS,
            PyDoc_STR("Start the tracer") },

    { "stop",   (PyCFunction) Tracer_stop,  METH_VARARGS,
            PyDoc_STR("Stop the tracer") },

    { NULL }
};

static PyTypeObject
TracerType = {
    MyType_HEAD_INIT
    "coverage.Tracer",         /*tp_name*/
    sizeof(Tracer),            /*tp_basicsize*/
    0,                         /*tp_itemsize*/
    (destructor)Tracer_dealloc, /*tp_dealloc*/
    0,                         /*tp_print*/
    0,                         /*tp_getattr*/
    0,                         /*tp_setattr*/
    0,                         /*tp_compare*/
    0,                         /*tp_repr*/
    0,                         /*tp_as_number*/
    0,                         /*tp_as_sequence*/
    0,                         /*tp_as_mapping*/
    0,                         /*tp_hash */
    0,                         /*tp_call*/
    0,                         /*tp_str*/
    0,                         /*tp_getattro*/
    0,                         /*tp_setattro*/
    0,                         /*tp_as_buffer*/
    Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
    "Tracer objects",          /* tp_doc */
    0,                         /* tp_traverse */
    0,                         /* tp_clear */
    0,                         /* tp_richcompare */
    0,                         /* tp_weaklistoffset */
    0,                         /* tp_iter */
    0,                         /* tp_iternext */
    Tracer_methods,            /* tp_methods */
    Tracer_members,            /* tp_members */
    0,                         /* tp_getset */
    0,                         /* tp_base */
    0,                         /* tp_dict */
    0,                         /* tp_descr_get */
    0,                         /* tp_descr_set */
    0,                         /* tp_dictoffset */
    (initproc)Tracer_init,     /* tp_init */
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
    
    TracerType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&TracerType) < 0) {
        Py_DECREF(mod);
        return NULL;
    }

    Py_INCREF(&TracerType);
    PyModule_AddObject(mod, "Tracer", (PyObject *)&TracerType);
    
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

    TracerType.tp_new = PyType_GenericNew;
    if (PyType_Ready(&TracerType) < 0) {
        return;
    }

    Py_INCREF(&TracerType);
    PyModule_AddObject(mod, "Tracer", (PyObject *)&TracerType);
}

#endif /* Py3k */
