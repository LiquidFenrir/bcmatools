/*----------------------------------------------------------------------------*/
/*--  LZSS coding for Nintendo GBA/DS                                       --*/
/*--  Copyright (C) 2011 CUE                                                --*/
/*--  Copyright (C) 2017 Dorkmaster Flek                                    --*/
/*--                                                                        --*/
/*--  This program is free software: you can redistribute it and/or modify  --*/
/*--  it under the terms of the GNU General Public License as published by  --*/
/*--  the Free Software Foundation, either version 3 of the License, or     --*/
/*--  (at your option) any later version.                                   --*/
/*--                                                                        --*/
/*--  This program is distributed in the hope that it will be useful,       --*/
/*--  but WITHOUT ANY WARRANTY; without even the implied warranty of        --*/
/*--  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the          --*/
/*--  GNU General Public License for more details.                          --*/
/*--                                                                        --*/
/*--  You should have received a copy of the GNU General Public License     --*/
/*--  along with this program. If not, see <http://www.gnu.org/licenses/>.  --*/
/*----------------------------------------------------------------------------*/

#include <Python.h>
#include "nlzss3.h"

#ifndef uint8_t
typedef unsigned char uint8_t;
#endif

static PyObject *pynlzss_error;

/* ----------------------------------------------------------------------------
 * module methods
 */

static PyObject *pynlzss_compress(PyObject *m, PyObject *args, PyObject *kw)
{
	static char *pynlzss_kwlist[] = {"buffer", NULL };
	char *outbuf = NULL, *buf = NULL;
	int insize = 0;
	Py_ssize_t outsize = 0;

	if (!PyArg_ParseTupleAndKeywords(args, kw, "y#", pynlzss_kwlist, &buf, &insize))
		return NULL;

	outbuf = LZSS_Compress(buf, insize, &outsize);

	if (!outbuf) {
		PyErr_SetString(pynlzss_error, "Failed to process LZSS file");
		return NULL;
	}

	PyObject *retval = PyBytes_FromStringAndSize(outbuf, outsize);
	PyMem_Free(outbuf);

	return retval;
}

static PyMethodDef pynlzss_methods[] = {
	{ "compress", (PyCFunction)pynlzss_compress,
	  METH_VARARGS | METH_KEYWORDS,
	  "Compress a bytes using the LZSS algorithm." },
	{ NULL, NULL, 0, NULL }
};

static struct PyModuleDef pynlzss = {
	PyModuleDef_HEAD_INIT,
	"nlzss3",      /* name of module */
	"",          /* module documentation, may be NULL */
	-1,          /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
	pynlzss_methods
};

PyMODINIT_FUNC PyInit_nlzss3(void)
{
    PyObject *m = PyModule_Create(&pynlzss);

    if (m == NULL)
        return m;

    pynlzss_error = PyErr_NewException("nlzss.error", NULL, NULL);
    Py_INCREF(pynlzss_error);
    PyModule_AddObject(m, "error", pynlzss_error);

    return m;
}
