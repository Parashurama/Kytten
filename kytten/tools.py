#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/tools.py
# Copyrighted (C) 2013 by "Parashurama"
from __future__ import unicode_literals, print_function

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
        return string if isinstance(string, unicode) else unicode(string,'utf-8')
    def string_to_bytes(string):
        return bytes(string)
    string_object = string_to_bytes
