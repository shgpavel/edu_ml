/* SPDX-License-Identifier: Apache-2.0 */

/*
 * Copyright (C) 2025 Pavel Shago <pavel@shago.dev>
 */

#define PY_SSIZE_T_CLEAN
#include <Python.h>

#include "huffman.h"

static PyObject *py_encode(PyObject *self, PyObject *args) {
	PyObject *py_input;
	if (!PyArg_ParseTuple(args, "U", &py_input)) return NULL;

	Py_ssize_t input_len;
	wchar_t const *input = PyUnicode_AsWideCharString(py_input, &input_len);

	if (!input) return NULL;

	struct eout result = encoder(input);

	PyMem_Free((void *)input);

	PyObject *py_bytes = PyBytes_FromStringAndSize((char const *)result.r,
	                                               (result.size + 7) / 8);
	PyObject *py_tree = PyCapsule_New(result.m, "HuffmanTree", NULL);

	return Py_BuildValue("(NO)", py_bytes, py_tree);
}

// return Py_BuildValue("NOn", py_bytes, py_tree);

static PyObject *py_decode(PyObject *self, PyObject *args) {
	const char *buffer;
	Py_ssize_t buffer_size;
	PyObject *py_tree_capsule;

	if (!PyArg_ParseTuple(args, "y#O", &buffer, &buffer_size,
	                      &py_tree_capsule))
		return NULL;

	struct huffman_el *tree =
	    PyCapsule_GetPointer(py_tree_capsule, "HuffmanTree");

	struct eout encoded = {
	    .size = buffer_size * 8, .r = (uint8_t *)buffer, .m = tree};

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
