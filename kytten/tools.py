#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/tools.py
# Copyrighted (C) 2013 by "Parashurama"
from __future__ import unicode_literals, print_function, absolute_import, division
from .compat import *

def yield_single_value(iterator):
    for retvalue in iterator:
        for value in retvalue:
            yield value

if PY3:
    native_string = lambda x: x
else:
    native_string = tobytes

def wrapper(wrapper_func):
    def _internal_wrapper(iterator):
        def _internal(*args, **kwargs):
            return wrapper_func(iterator(*args, **kwargs))
        _internal.__name__ = native_string(iterator.__name__+'( wrapped({}) )'.format(wrapper_func.__name__))

        return _internal

    return _internal_wrapper

def patch_instance_method(obj, func_name):
    def _wrapper(new_func_obj):
        if not hasattr(obj, "_methods_stack"):
            obj._methods_stack={}
        if not func_name in obj._methods_stack:
            def _call_wrapper(self, *args, **kwargs):
                for func in obj._methods_stack[func_name]:
                    if func(*args, **kwargs) is True:
                        return True
            obj._methods_stack[func_name]=[getattr(obj, func_name, None)] if hasattr(obj, func_name) else []
            setattr(obj, func_name, MethodType(_call_wrapper, obj))

        obj._methods_stack[func_name].insert(0, MethodType(new_func_obj, obj))

        return new_func_obj

    return _wrapper

def overload_instance_method(obj, func_name):
    def _wrapper(new_func_obj):
        setattr(obj, func_name, MethodType(new_func_obj, obj))
        return new_func_obj

    return _wrapper

def minvalue(v0, v1):
    if v0 is None:
        return v1
    elif v1 is None:
        return v0
    else:
        return min(v0, v1)

def maxvalue(v0, v1):
    if v0 is None:
        return v1
    elif v1 is None:
        return v0
    else:
        return max(v0, v1)
