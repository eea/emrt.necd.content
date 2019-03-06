#include <Python.h>


static PyObject *
flatten_json_flatten(PyObject *self, PyObject *args)
{

    char *str_json;

    if(!PyArg_ParseTuple(args, "s", &str_json)) {
        return NULL;
    };

    int len_str_json = strlen(str_json);

    char *out = malloc(len_str_json);

    int idx;
    int level = 0;
    int insert = 0;
    for (idx = 0; idx < len_str_json; idx++) {
      char chr = str_json[idx];
      if (chr == '[') {
        level++;
      }

      if (level != 2 || (chr != '[' && chr != ']')) {
        out[insert] = chr;
        insert++;
      }

      if (chr == ']') {
        level--;
      }
    }
    out[insert] = '\0';

    PyObject *result = Py_BuildValue("s", out);
    free(out);

    return result;
};


static PyMethodDef FlattenJSONMethods[] = {
    {
        "flatten", flatten_json_flatten, METH_VARARGS,
        "Flatten json"
    },
    { NULL, NULL, 0, NULL }
};

PyMODINIT_FUNC
initflatten_json(void) {
    (void) Py_InitModule("flatten_json", FlattenJSONMethods);
}
