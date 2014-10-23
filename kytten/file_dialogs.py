#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/file_dialogs.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong
from __future__ import unicode_literals, print_function

import glob
import os
import pyglet
from pyglet import gl

from .button import Button
from .dialog import Dialog, DIALOG_NO_CREATE_FRAME
from .frame import Frame, SectionHeader
from .layout import VerticalLayout, HorizontalLayout
from .layout import ANCHOR_CENTER, HALIGN_LEFT, VALIGN_BOTTOM, HALIGN_CENTER
from .menu import Menu, Dropdown
from .scrollable import Scrollable
from .text_input import Input
from .widgets import Label

def cmp_to_key(mycmp):
    'Convert a cmp= function into a key= function'
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K

class FileLoadDialog(Dialog):
    select_button=None
    cancel_button=None
    def __init__(self, path=os.getcwd(), extensions=[], title="Select File",
                 width=540, height=300, on_select=None, **kwargs):
        self.path = path
        self.extensions = extensions
        self.title = title
        self.on_select = self._wrap_method(on_select)
        self.selected_file = None
        self._set_files()

        if on_select is None:
            # Set up buttons to be shown in our contents only if on_select is not set
            self.select_button = Button("Select", on_click=kwargs.get('on_enter', None))
            self.cancel_button = Button("Cancel", on_click=kwargs.get('on_escape', None))

        def on_parent_menu_select(menu, choice, choice_index=None):
            self._select_file(self.parents_dict[choice])

        def on_menu_select(menu, choice, choice_index=None):
            self._select_file(self.files_dict[choice])

        self.dropdown = Dropdown(options=self.parents,
                                 selected=self.parents[-1],
                                 align=VALIGN_BOTTOM,
                                 on_select=on_parent_menu_select)
        self.menu = Menu(options=self.files, align=HALIGN_LEFT,
                         on_select=on_menu_select)
        self.scrollable = Scrollable(
            VerticalLayout([self.dropdown, self.menu], align=HALIGN_LEFT),
            width=width, height=height)

        content = self._get_content()
        Dialog.__init__(self, content, flags=DIALOG_NO_CREATE_FRAME, **kwargs)

    def _get_content(self):
        return Frame(
            VerticalLayout([
                SectionHeader(self.title),
                self.scrollable,
                HorizontalLayout([
                    self.select_button, None, self.cancel_button
                ]),
            ], align=HALIGN_CENTER, padding=15)
        )

    def _select_file(self, filename):
        if os.path.isdir(filename):
            self.path = filename
            self._set_files()
            self.dropdown.set_options(self.parents,
                                      selected=self.parents[-1])
            self.menu.set_options(self.files)
        else:
            self.selected_file = filename
            if self.on_select is not None and self.on_select(filename, None):
                self.teardown()

    def _set_files(self):
        # Once we have a new path, update our files
        filenames = glob.glob(os.path.join(self.path, '*'))

        # First, a list of directories
        self.parents = []
        self.parents_dict = {}
        path = self.path
        index = 1
        while 1:
            name = "%d %s" % (index, os.path.basename(path) or path)
            self.parents_dict[name] = path
            self.parents.append(name)
            index += 1
            path, child = os.path.split(path)
            if not child:
                break
        self.parents.reverse()

        files = [("%s (dir)" % os.path.basename(x), x) for x in filenames
                 if os.path.isdir(x)]

        # Now add the files that match the extensions
        if self.extensions:
            for filename in filenames:
                if os.path.isfile(filename):
                    ext = os.path.splitext(filename)[1]
                    if ext in self.extensions:
                        files.append((os.path.basename(filename), filename))
        else:
            files.extend([(os.path.basename(x), x) for x in filenames
                          if os.path.isfile(x)])

        self.selected_file = None
        self.files_dict = dict(files)
        self.files = list(self.files_dict.keys())

        def dir_sort(x, y):
            if x.endswith(' (dir)') and y.endswith(' (dir)'):
                if x > y:
                    return 1
                elif x < y:
                    return -1
                else:
                    return 0
            elif x.endswith(' (dir)'):
                return -1
            elif y.endswith(' (dir)'):
                return 1
            else:
                if x > y:
                    return 1
                elif x < y:
                    return -1
                else:
                    return 0
        self.files.sort(key=cmp_to_key(dir_sort))

    def get(self):
        return self.selected_file

    def size(self, dialog, scale):
        Dialog.size(self, dialog, scale)

    def teardown(self):
        self.on_select = None
        Dialog.teardown(self)

class FileSaveDialog(FileLoadDialog):
    def __init__(self, *args, **kwargs):
        self.text_input = Input()

        # Set up buttons to be shown in our contents
        def on_save(btn):
            self._do_select()
        self.save_button = Button("Save", on_click=on_save)

        def on_cancel(btn):
            self._do_cancel()
        self.cancel_button = Button("Cancel", on_click=on_cancel)

        FileLoadDialog.__init__(self, *args, **kwargs)

        # Setup our event handlers
        def on_enter(dialog):
            self._do_select()
        self.on_enter = on_enter

        self.real_on_select = self.on_select
        def on_select(filename, index):
            self.text_input.set_text(filename)
        self.on_select = on_select

    def _do_cancel(self):
        if self.on_escape is not None:
            self.on_escape(self)
        else:
            self.delete()
            self.window.remove_handlers(self)

    def _do_select(self):
        filename = self.text_input.get_text()
        path, base = os.path.split(filename)
        if not base:
            filename = None
        elif not path:
            filename = os.path.join(self.path, filename)
        if self.real_on_select is not None:
            if self.real_on_select(filename):
                self.teardown()

    def _get_content(self):
        return Frame(
            VerticalLayout([
                SectionHeader(self.title),
                self.scrollable,
                Label("Filename:"),
                self.text_input,
                HorizontalLayout([
                    self.save_button, None, self.cancel_button
                ]),
            ], align=HALIGN_LEFT)
        )

class DirectorySelectDialog(FileLoadDialog):
    def __init__(self, *args, **kwargs):
        self.text_input = Input()

        # Set up buttons to be shown in our contents
        def on_select_button(btn):
            self._do_select()
        self.select_button = Button("Select", on_click=on_select_button)

        def on_cancel_button(btn):
            self._do_cancel()
        self.cancel_button = Button("Cancel", on_click=on_cancel_button)

        FileLoadDialog.__init__(self, *args, **kwargs)

        # Setup our event handlers
        def on_enter(dialog):
            self._do_select()
        self.on_enter = on_enter

        self.real_on_select = self.on_select
        def on_select(filename):
            self.text_input.set_text(filename)
        self.on_select = on_select

        def on_parent_menu_select(choice, choice_index):
            self.text_input.set_text(self.parents_dict[choice])
            self._do_open()

        def on_menu_select(choice, choice_index=None):
            if choice in self.files_dict:
                self._select_file(self.files_dict[choice])
            else:
                self._select_file(self.files_dict['-'+choice])

        self.dropdown.on_select = on_parent_menu_select
        self.menu.on_select = on_menu_select
    def _do_cancel(self):
        if self.on_escape is not None:
            self.on_escape(self)
        else:
            self.delete()
            self.window.remove_handlers(self)

    def _do_open(self):
        filename = self.text_input.get_text()
        if os.path.isdir(filename):
            self.path = filename
            self._set_files()
            self.dropdown.set_options(self.parents,
                                      selected=self.parents[-1])
            self.menu.set_options(self.files)

    def _do_select(self):
        filename = self.text_input.get_text()
        path, base = os.path.split(filename)
        if not base:
            filename = None
        elif not path:
            filename = os.path.join(self.path, filename)
        if self.real_on_select is not None:
            if self.real_on_select(filename):
                self.teardown()


    def _get_content(self):
        return Frame(
            VerticalLayout([
                SectionHeader(self.title),
                self.scrollable,
                Label("Directory:"),
                self.text_input,
                HorizontalLayout([
                    self.select_button, None, self.cancel_button
                ]),
            ], align=HALIGN_LEFT)
        )

    def _select_file(self, filename):
        if not os.path.isdir(filename):
            return  # we accept only directories!

        if self.selected_file == filename:
            if filename != self.path:
                self._do_open()
            else:
                self._do_select()
        else:
            self.selected_file = filename
            if self.on_select is not None:
                self.on_select(filename)

    def _set_files(self):
        # Once we have a new path, update our files
        filenames = glob.glob(os.path.join(self.path, '*'))

        # First, a list of directories
        self.parents = []
        self.parents_dict = {}
        path = self.path
        index = 1
        while 1:
            name = "%d %s" % (index, os.path.basename(path) or path)
            self.parents_dict[name] = path
            self.parents.append(name)
            index += 1
            path, child = os.path.split(path)
            if not child:
                break
        self.parents.reverse()

        files = [('(this dir)', self.path)] + \
                [("%s (dir)" % os.path.basename(x), x) for x in filenames
                 if os.path.isdir(x)]
        # Now add the files that match the extensions
        if self.extensions:
            for filename in filenames:
                if os.path.isfile(filename):
                    ext = os.path.splitext(filename)[1]
                    if ext in self.extensions:
                        files.append(('%s' % os.path.basename(filename),
                                      filename))
        else:
            files.extend([('-%s' % os.path.basename(x), x) for x in filenames
                          if os.path.isfile(x)])

        self.selected_file = None
        self.files_dict = dict(files)
        self.files = list(self.files_dict.keys())

        def dir_sort(x, y):
            if x == '(this dir)':
                return -1
            elif x.endswith(' (dir)') and y.endswith(' (dir)'):
                if x > y:
                    return 1
                elif x < y:
                    return -1
                else:
                    return 0
            elif x.endswith(' (dir)') and y != '(this dir)':
                return -1
            elif y.endswith(' (dir)'):
                return 1
            else:
                if x > y:
                    return 1
                elif x < y:
                    return -1
                else:
                    return 0
        self.files.sort(key=cmp_to_key(dir_sort))
