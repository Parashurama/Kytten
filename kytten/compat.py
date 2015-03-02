#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/compat.py
# Copyrighted (C) 2015 by "Parashurama"
import sys
from types import MethodType as MethodType_
from future.utils import PY2, PY3
from future.utils import python_2_unicode_compatible, with_metaclass, iteritems, itervalues, exec_
from builtins import (bytes, str, open, super, range,
                      zip, round, input, pow, object)
basestring = (bytes, str)


def MethodType(func, obj):
    if   PY2:
        return MethodType_(func, obj, type(obj))
    elif PY3:
        return MethodType_(func, obj)

def tostring(string):
    if isinstance(string, bytes):
        return string.decode('utf-8')
    else:
        return str(string)

def tobytes(string):
    if isinstance(string, str):
        return string.encode('utf-8')
    elif isinstance(string, bytes):
        return string
    else:
        return str(string).encode('utf-8')

if PY3:
    def cmp(a, b):
        return -1 if (a < b) else ( 0 if (a == b) else 1 )
else:
    cmp=cmp


__all__ = [ "python_2_unicode_compatible", "with_metaclass", "iteritems", "itervalues", "MethodType", "tostring", "tobytes",
            "bytes", "str", "open", "super", "range", "basestring", "cmp",
            "zip", "round", "input", "pow", "object", "exec_", "PY3", "PY2"]
