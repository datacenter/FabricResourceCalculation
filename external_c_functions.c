#include <Python.h>
#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

#define uint32 unsigned int
#define uint16 unsigned short
#define ushort unsigned short

#define NUM_USHORT_BITS (8 * sizeof(ushort))
#define MAX_USHORT_BIT (1 << (NUM_USHORT_BITS - 1))
#define MAX_PORT_EXPAND (8*sizeof(ushort) * 2)


static PyObject *expand_port_range(PyObject *self, PyObject *args) {
    int a;
    int b;

    if (!PyArg_ParseTuple(args, "ii", &a, &b)) {
        return Py_BuildValue("s", "Invalid number of arguments");
    }
    return Py_BuildValue("i", expand_port_range_c(a, b));

}

static PyObject *check_model(PyObject *self) {

    return Py_BuildValue("i", check_model_c());

}

static char expand_port_range_docs[] =
    "expand_port_range( ): return number of counts based on port range\n";

static char check_model_docs[] =
    "check_model( ): check if is Miller or Donner\n";

static PyMethodDef external_c_functions[] = {
    {"expand_port_range", (PyCFunction)expand_port_range, METH_VARARGS, expand_port_range_docs},
    {"check_model", (PyCFunction)check_model, METH_NOARGS, check_model_docs},
    {NULL}
};

void initexternal_c_functions(void)
{
    Py_InitModule3("external_c_functions", external_c_functions,
                   "External C Functions");
}

int expand_port_range_c (int lo_port, int hi_port, ushort *ports, ushort *masks)
{
    int count = 0;
    uint32 port, mask;
    uint32 hi_bit = 0x0001;     /* Current bit position of hi_port */
    uint32 lo_bit = 0x0001;     /* Current bit position of lo_port */

    /*
     * Initialize port register with upper boundary. turning all
     * consecutive low-order 1 bits into don't-cares.  For example,
     * 01100111 becomes 01100xxx
     */
    port = hi_port;
    mask = 0xFFFF;
    while ((hi_bit <= MAX_USHORT_BIT) && (port & hi_bit)) {
        port &= ~hi_bit;
        mask &= ~hi_bit;
        hi_bit <<= 1;
    }

    /*
     * Now iterate until we pass the lower boundary.  At each iteration,
     * we turn all consecutive low-order zeros into don't-cares, and
     * the following 1 into a 0.  Example: 001100xx -> 0010xxxx
     */
    while (port >= lo_port)
    {
        if ((ports != NULL) && (masks != NULL))
        {
            ports[count] = port;
            masks[count] = mask;
        }
        count++;

        while ((hi_bit <= MAX_USHORT_BIT) && (port & hi_bit) == 0)
        {
            mask &= ~hi_bit;
            hi_bit <<= 1;
        }

        if (hi_bit > MAX_USHORT_BIT)
        {
	    break;
	    }
        port &= ~hi_bit;
    }

    /*
     * We've passed the lower boundary.  Start working from the lower
     * boundary, and move upward.  First, turn all consecutive low-order
     * 0 bits into don't-cares.  Example: 00011000 -> 00011xxx
     */
    port = lo_port;
    mask = 0xFFFF;
    while ((lo_bit <= hi_bit) && (port & lo_bit) == 0)
    {
        mask &= ~lo_bit;
        lo_bit <<= 1;
    }

    /*
     * Finally, iterate until we reach the point we stopped before.  At
     * each iteration, we turn all consecutive low-order ones into don't-
     * cares, and the following 0 into a 1.  Example: 001011xx -> 0011xxxx
     */
    while (lo_bit < hi_bit)
    {
        if ((ports != NULL) && (masks != NULL))
        {
            ports[count] = port;
            masks[count] = mask;
        }
        count++;

        while ((lo_bit < hi_bit) && (port & lo_bit))
        {
            port &= ~lo_bit;
            mask &= ~lo_bit;
            lo_bit <<= 1;
        }
        port |= lo_bit;
    }
    return count;
}

int check_model_c (void){
    return 1;
}

