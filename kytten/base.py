#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/base.py
# Copyrighted (C) 2013 by "Parashurama"

import weakref

class InvalidWidgetNameError(Exception):
    pass

class __int__:
    id=-1

    __guiobjects_by_Name__=weakref.WeakValueDictionary() #dict()
    __guiobjects_by_Id__= weakref.WeakValueDictionary() #dict()
    #__guiobjects_to_set__=[]
    __ListOfExtantDialog__=weakref.WeakSet()
    __clipboard_content__ = None

class CVars:
    pass

def GenId(obj):
    __int__.id+=1

    __int__.__guiobjects_by_Id__[__int__.id]=obj#weakref.ref(obj)
    #__int__.__guiobjects_to_set__.append(obj)

    return __int__.id

def ReferenceName(obj,Name):
    if not Name in __int__.__guiobjects_by_Name__:
        __int__.__guiobjects_by_Name__[Name]=obj
    else: raise InvalidWidgetNameError("ReferenceName: Object name '{}' already in use!".format(Name))

def DereferenceName(Name):
    if Name in __int__.__guiobjects_by_Name__:
        del __int__.__guiobjects_by_Name__[Name]

    else: raise InvalidWidgetNameError("DereferenceName: Object name '%s' not found!" %(Name))

def GetObjectfromId(id):
    try: return __int__.__guiobjects_by_Id__[id]
    except KeyError: raise InvalidWidgetNameError("GetObjectfromId: No Object for id '{0}'".format(id))

def GetObjectfromName(Name):
    try: return __int__.__guiobjects_by_Name__[Name]
    except KeyError: raise InvalidWidgetNameError("GetObjectfromName: No Object named '{0}'".format(Name))

def ReferenceDialog(dialog):
    __int__.__ListOfExtantDialog__.add(dialog)

def DereferenceDialog(dialog):
    __int__.__ListOfExtantDialog__.remove(dialog)
    #select first dialog in iteration and force_refresh
    next(iter(__int__.__ListOfExtantDialog__)).to_refresh = True

def GetActiveDialogs():
    return __int__.__ListOfExtantDialog__

def ActionOnAllDialogs(exceptions, function, *args):
    if not isinstance(exceptions, tuple) or not isinstance(exceptions, list):
        exceptions=(exceptions,)

    for dialog in list(__int__.__ListOfExtantDialog__):
        if not dialog in exceptions:
            getattr(dialog,function)(*args)


DisplayGroupReference= dict()

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
            DisplayGroupReference[name]=self

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

def ShowGroups(*groups):
    for group in groups:
        #if not isinstance(group, DisplayGroup) : raise TypeError("DsiplayGroup %s Invalide"  % (groy
        DisplayGroupReference[group].Show()

def HideGroups(*groups):
    for group in groups:
        DisplayGroupReference[group].Hide()

class Virtual(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

from .tools import yield_single_value, wrapper, string_to_unicode
