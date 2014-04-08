#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/manager.py
# Copyrighted (C) 2013 by "Parashurama"
from __future__ import unicode_literals, print_function

import weakref
import pyglet
from .glcontext import GuiInternalBuffer, GuiRenderContext
from .base import __int__, GetActiveDialogs, GetObjectfromName
from .dialog import PatchWindowsEventHandler

def dummy(*args):
    return None


event_dispatcher_events_override = set(['on_mouse_press','on_mouse_release','on_mouse_motion','on_mouse_drag','on_mouse_scroll',
                                    'on_key_press','on_key_release'])

class GuiManager(pyglet.graphics.Batch):
    def __init__(self, window, isBuffered=True):
        pyglet.graphics.Batch.__init__(self)
        self.parent_window=window
        self.is_buffered=isBuffered
        self.force_refresh=False

        self.backgroup = pyglet.graphics.OrderedGroup(0)
        self.foregroup = pyglet.graphics.OrderedGroup(1)
        self._buffer   = GuiInternalBuffer(window.width,window.height)
        self._dialogs  = weakref.WeakSet()
        self._window_size = (window.width,window.height)

        def on_main_window_resize(width, height):
            self._buffer.recreate_texture((width, height))
            self._window_size = (width, height)
            for dialog in self._dialogs:
                dialog.to_refresh=True
                if dialog.screen is not None:
                    dialog.screen.width = width
                    dialog.screen.height = height

        window.push_handlers(on_resize=on_main_window_resize)

        PatchWindowsEventHandler(window)

    def AddDialog(self,dialog):
        self._dialogs.add(dialog)

    def Render(self, kytten_buffered=True):

        if   self.is_buffered and kytten_buffered is True :
            self._render_buffered()
        elif kytten_buffered == 'bypass':
            self._render_from_buffer()
        else:
            self._render_unbuffered()

    def _render_buffered(self):
        with GuiRenderContext(*self._window_size):
            if self._update_gui() or self.force_refresh is True:

                self.force_refresh=False
                with self._buffer:
                    self.draw()

                for dialog in self._dialogs: dialog.to_refresh=False

            self._buffer.render()

    def _render_unbuffered(self):
        with GuiRenderContext(*self._window_size):
            self._update_gui()
            for dialog in self._dialogs: dialog.to_refresh=False
            self.draw()

    def _render_from_buffer(self):
        with GuiRenderContext(*self._window_size):
            self.force_refresh= True
            self._buffer.render()

    def _update_gui(self):
        to_refresh=False
        for dialog in self._dialogs:
            dialog.on_update(0.016)
            if dialog.to_refresh: to_refresh=True

        return to_refresh



class PageManager:
    _current_page_id=-1

    PageReference={}
    PageDialogs={}

    @staticmethod
    def _update_display():
        page = PageManager._current_page_id

        if not page in PageManager.PageDialogs:
            print(AttributeError("Page {0} not Registered".format(page)))
            return False # Page does not exists

        WidgetsToShow, WidgetsToHide, constructor, callback = PageManager.PageDialogs[page]

        if constructor is not None: constructor()

        for dialog in GetActiveDialogs():
            if not dialog.name in WidgetsToShow+['DRAGGABLE']:
                dialog.Hide()

        if page in PageManager.PageDialogs:
            try:
                for element in WidgetsToShow:
                    GetObjectfromName(element).Show()
            except AttributeError: raise AttributeError("Show: No Dialog named '{0}' in '{1}'".format(element,page) )

            try:
                for element in WidgetsToHide:
                    GetObjectfromName(element).Hide()
            except AttributeError: raise AttributeError("Hide: No Dialog named '{0}' in '{1}'".format(element,page) )

        if callback is not None: callback()

        PageManager.PageDialogs[page] = WidgetsToShow, WidgetsToHide, None, callback #discard constructor once done

        return True # Page does exists

    @staticmethod
    def RegisterPage(page, to_show=[], to_hide=[], constructor=None, callback=None):
        PageManager.PageDialogs[page]=( to_show, to_hide, constructor, callback)


    @staticmethod
    def next_page(*args):
        PageManager._current_page_id+=1
        if not PageManager._update_display():
            PageManager._current_page_id-=1

    @staticmethod
    def prev_page(*args):

        PageManager._current_page_id-=1
        if not PageManager._update_display():
            PageManager._current_page_id+=1

    @staticmethod
    def goto_page(page):
        PageManager._current_page_id=page
        PageManager._update_display()
