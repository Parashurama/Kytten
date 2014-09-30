#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/tools.py
# Copyrighted (C) 2013 by "Parashurama"
from __future__ import unicode_literals, print_function
from types import MethodType

def yield_single_value(iterator):
    for retvalue in iterator:
        for value in retvalue:
            yield value

def wrapper(wrapper_func):
    def _internal_wrapper(iterator):
        def _internal(*args, **kwargs):
            return wrapper_func(iterator(*args, **kwargs))
        _internal.__name__ = string_object(iterator.__name__+'( wrapped({}) )'.format(wrapper_func.__name__))

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
            setattr(obj, func_name, MethodType(_call_wrapper, obj, type(obj)))

        obj._methods_stack[func_name].insert(0, MethodType(new_func_obj, obj, type(obj)))

        return new_func_obj

    return _wrapper

def overload_instance_method(obj, func_name):
    def _wrapper(new_func_obj):
        setattr(obj, func_name, MethodType(new_func_obj, obj, type(obj)))
        return new_func_obj

    return _wrapper

import sys
if sys.version >= '3':
    xrange = range

    def iteritems(obj):
        return obj.items()
    def string_to_unicode(string):
        return string
    def string_to_bytes(string):
        return bytes(string, 'utf-8')
    string_object = string_to_unicode
else:
    xrange = xrange

    def iteritems(obj):
        return obj.iteritems()
    def string_to_unicode(string):
        return string if isinstance(string, unicode) else string.decode('utf-8')
    def string_to_bytes(string):
        return string.encode('utf-8') if isinstance(string, unicode) else bytes(string)
    string_object = string_to_bytes
