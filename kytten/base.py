#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/base.py
# Copyrighted (C) 2013 by "Parashurama"
from __future__ import unicode_literals, print_function

import weakref

FLAGS={'force_delete':False}

class InvalidWidgetNameError(Exception):
    pass

class internals:
    id=-1
    objects_by_name = weakref.WeakValueDictionary() #dict()
    objects_by_id   = weakref.WeakValueDictionary() #dict()
    extant_dialog_list = weakref.WeakSet()
    display_groups_refs= {}

class CVars:
    pass

class gc:
    objects_by_id = internals.objects_by_id
    objects_by_name = internals.objects_by_name

def GenId(obj):
    internals.id+=1
    internals.objects_by_id[internals.id]=obj
    return internals.id

def ReferenceName(obj,Name):
    if not Name in internals.objects_by_name:
        internals.objects_by_name[Name]=obj
    else: raise InvalidWidgetNameError("ReferenceName: Object name '{}' already in use!".format(Name))

def DereferenceName(Name):
    if Name in internals.objects_by_name:
        del internals.objects_by_name[Name]

    else: raise InvalidWidgetNameError("DereferenceName: Object name '%s' not found!" %(Name))

def GetObjectfromId(id):
    try: return internals.objects_by_id[id]
    except KeyError: raise InvalidWidgetNameError("GetObjectfromId: No Object for id '{0}'".format(id))

def GetObjectfromName(Name):
    try: return internals.objects_by_name[Name]
    except KeyError: raise InvalidWidgetNameError("GetObjectfromName: No Object named '{0}'".format(Name))

def ReferenceDialog(dialog):
    internals.extant_dialog_list.add(dialog)

def DereferenceDialog(dialog):
    internals.extant_dialog_list.remove(dialog)
    #select first dialog in iteration and force_refresh
    try: next(iter(internals.extant_dialog_list)).to_refresh = True
    except StopIteration:pass

def GetActiveDialogs():
    return internals.extant_dialog_list

def ActionOnAllDialogs(exceptions, function, *args):
    if not isinstance(exceptions, (tuple, list)):
        exceptions=(exceptions,)

    for dialog in list(internals.extant_dialog_list):
        if not dialog in exceptions:
            getattr(dialog,function)(*args)

class Log:
    logging_bool=False
    @staticmethod
    def isLogging():
        return Log.logging_bool

class DisplayGroup:
    def __init__(self, name=None, members=None):
        self.name=name

        if self.name is not None:
            ReferenceName(self,self.name)
            internals.display_groups_refs[name]=self

        if members: self.members=weakref.WeakSet(members)
        else: self.members=weakref.WeakSet()

    def __iter__(self,*args):
        return iter(self.members)

    def add(self,member):
        self.members.add(member)

    def remove(self,member):
        self.members.remove(member)

    def ToggleVisibilityGroup(self):
        for member in self.members:
            member.ToggleVisibility()

    def ShowGroup(self):
        for member in self.members:
            member.Show()

    def HideGroup(self):
        for member in self.members:
            member.Hide()

    Show = ShowGroup
    Hide = HideGroup

def ShowGroups(*groups):
    for group in groups:
        internals.display_groups_refs[group].Show()

def HideGroups(*groups):
    for group in groups:
        internals.display_groups_refs[group].Hide()

class Virtual(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

from .tools import yield_single_value, wrapper, string_to_unicode, iteritems, xrange, minvalue, maxvalue
