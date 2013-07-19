#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/tools.py
# Copyrighted (C) 2013 by "Parashurama"


def yield_single_value(iterator):
    for retvalue in iterator:
        for value in retvalue:
            yield value

def wrapper(wrapper_func):
    def _internal_wrapper(iterator):
        def _internal(*args, **kwargs):
            return wrapper_func(iterator(*args, **kwargs))

        _internal.__name__ = iterator.__name__+'( wrapped({}) )'.format(wrapper_func.__name__)

        return _internal

    return _internal_wrapper

def string_to_unicode(string):
    return string if isinstance(string, unicode) else unicode(string,'utf-8')
