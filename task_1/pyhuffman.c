/* SPDX-License-Identifier: Apache-2.0 */

/*
 * Copyright (C) 2025 Pavel Shago <pavel@shago.dev>
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "huffman.h"

static void free_table_capsule(PyObject *capsule) {
	void *ptr = PyCapsule_GetPointer(capsule, "HuffmanTable");
	if (ptr) {
		free(ptr);
	}
}

static PyObject *py_encode(PyObject *self, PyObject *args) {
	PyObject *py_input;
	if (!PyArg_ParseTuple(args, "U", &py_input)) return NULL;

	Py_ssize_t input_len;
	wchar_t const *input = PyUnicode_AsWideCharString(py_input, &input_len);
	if (!input) return NULL;

	struct eout result = encoder(input);
	PyMem_Free((void *)input);

	if (!result.m || result.size == 0) Py_RETURN_NONE;

	PyObject *py_bytes = PyBytes_FromStringAndSize((char const *)result.m,
	                                               (result.size + 7) / 8);
	PyObject *py_table =
	    PyCapsule_New(result.t, "HuffmanTable", free_table_capsule);

	return Py_BuildValue("(NOi)", py_bytes, py_table, result.size);
}

static PyObject *py_decode(PyObject *self, PyObject *args) {
	wchar_t const *buffer;
	Py_ssize_t buffer_size;
	PyObject *py_table_capsule;
	int bitlen;

	if (!PyArg_ParseTuple(args, "y#Oi", &buffer, &buffer_size,
	                      &py_table_capsule, &bitlen))
		return NULL;

	if (buffer_size == 0 || !buffer || !py_table_capsule) Py_RETURN_NONE;

	struct bitbuf *table =
	    PyCapsule_GetPointer(py_table_capsule, "HuffmanTable");

	if (!table) {
		PyErr_SetString(PyExc_RuntimeError,
		                "Invalid HuffmanTable capsule");
		return NULL;
	}

	struct eout encoded = {
	    .size = (size_t)bitlen,
	    .m = (uint8_t *)buffer,
	    .t = table,
	};

	wchar_t *decoded = decoder(encoded);
	PyObject *py_result = PyUnicode_FromWideChar(decoded, wcslen(decoded));
	free(decoded);

	return py_result;
}

static PyMethodDef HuffmanMethods[] = {
    {"encode", py_encode, METH_VARARGS, "Encode input using Huffman coding"},
    {"decode", py_decode, METH_VARARGS, "Decode Huffman coded input"},
    {NULL, NULL, 0, NULL}};

static struct PyModuleDef huffmanmodule = {PyModuleDef_HEAD_INIT, "huffman",
                                           NULL, -1, HuffmanMethods};

PyMODINIT_FUNC PyInit_huffman(void) {
	return PyModule_Create(&huffmanmodule);
}
