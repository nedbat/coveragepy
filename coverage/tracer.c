// C-based Tracer for coverage.py

#include "Python.h"
#include "compile.h"        // in 2.3, this wasn't part of Python.h
#include "eval.h"           // or this.
#include "structmember.h"
#include "frameobject.h"

#define DEBUG 1

#if DEBUG
#define IFDEBUG(x)      x
#else
#define IFDEBUG(x)
#endif

// The Tracer type.

typedef struct {
    PyObject_HEAD
    PyObject * should_trace;
    PyObject * data;
    PyObject * should_trace_cache;
    int started;
    // The index of the last-used entry in tracenames.
    int depth;
    // Filenames to record at each level, or NULL if not recording.
    PyObject * tracenames[300];
} Tracer;

static int
Tracer_init(Tracer *self, PyObject *args, PyObject *kwds)
{
    self->should_trace = NULL;
    self->data = NULL;
    self->should_trace_cache = NULL;
    self->started = 0;
    self->depth = -1;
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

    self->ob_type->tp_free((PyObject*)self);
}

static int
Tracer_trace(Tracer *self, PyFrameObject *frame, int what, PyObject *arg)
{
    PyObject * filename = NULL;
    PyObject * tracename = NULL;

    // printf("trace: %d @ %d\n", what, frame->f_lineno);
    
    switch (what) {
    case PyTrace_CALL:      // 0
        self->depth++;
        if (self->depth > sizeof(self->tracenames)/sizeof(self->tracenames[0])) {
            PyErr_SetString(PyExc_RuntimeError, "Tracer stack overflow");
            return -1;
        }
        // Check if we should trace this line.
        filename = frame->f_code->co_filename;
        tracename = PyDict_GetItem(self->should_trace_cache, filename);
        if (tracename == NULL) {
            // We've never considered this file before.  Ask should_trace about it.
            PyObject * args = Py_BuildValue("(O)", filename);
            tracename = PyObject_Call(self->should_trace, args, NULL);
            Py_DECREF(args);
            if (tracename == NULL) {
                // An error occurred inside should_trace.
                return -1;
            }
            PyDict_SetItem(self->should_trace_cache, filename, tracename);
        }
        else {
            Py_INCREF(tracename);
        }

        // If tracename is a string, then we're supposed to trace.
        self->tracenames[self->depth] = PyString_Check(tracename) ? tracename : NULL;
        break;
    
    case PyTrace_RETURN:    // 3
        if (self->depth >= 0) {
            Py_XDECREF(self->tracenames[self->depth]);
            self->depth--;
        }
        break;
    
    case PyTrace_LINE:      // 2
        if (self->depth >= 0) {
            if (self->tracenames[self->depth]) {
                PyObject * t = PyTuple_New(2);
                tracename = self->tracenames[self->depth];
                Py_INCREF(tracename);
                PyTuple_SetItem(t, 0, tracename);
                PyTuple_SetItem(t, 1, PyInt_FromLong(frame->f_lineno));
                Py_INCREF(Py_None);
                PyDict_SetItem(self->data, t, Py_None);
                Py_DECREF(t);
            }
        }
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
    { "should_trace",       T_OBJECT, offsetof(Tracer, should_trace), 0,        "Function indicating whether to trace a file." },
    { "data",               T_OBJECT, offsetof(Tracer, data), 0,                "The raw dictionary of trace data." },
    { "should_trace_cache", T_OBJECT, offsetof(Tracer, should_trace_cache), 0,  "Dictionary caching should_trace results." },
    { NULL }
};

static PyMethodDef
Tracer_methods[] = {
    { "start",  (PyCFunction) Tracer_start, METH_VARARGS, "Start the tracer" },
    { "stop",   (PyCFunction) Tracer_stop,  METH_VARARGS, "Stop the tracer" },
    { NULL }
};

static PyTypeObject
TracerType = {
    PyObject_HEAD_INIT(NULL)
    0,                         /*ob_size*/
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

// Module definition

void
inittracer(void)
{
    PyObject* mod;

    mod = Py_InitModule3("coverage.tracer", NULL, "Fast coverage tracer.");
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
