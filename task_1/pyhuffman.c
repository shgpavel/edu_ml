/* SPDX-License-Identifier: Apache-2.0 */

/*
 * Copyright (C) 2025 Pavel Shago <pavel@shago.dev>
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include "huffman.h"

static PyObject *py_encode(PyObject* self, PyObject* args) {
	void *a;
	if (!PyArg_ParseTuple(args, "ii", &a, &b))
		return NULL;
	struct eout result = encoder(a);
	return PyLong_FromLong(result);
}

static PyObject *py_decode(PyObject* self, PyObject* args) {
	int a, b;
	if (!PyArg_ParseTuple(args, "ii", &a, &b))
		return NULL;
	int result = add(a, b);
	return PyLong_FromLong(result);
}

static PyMethodDef HuffmanMethods[] = {
	{"encode", py_encode, METH_VARARGS, "huffman encoder"},
	{NULL, NULL, 0, NULL}
};

static struct PyModuleDef huffmanmodule = {PyModuleDef_HEAD_INIT, "huffman",
                                           NULL, -1, HuffmanMethods};

PyMODINIT_FUNC PyInit_huffman(void) {
    return PyModule_Create(&huffmanmodule);
}
