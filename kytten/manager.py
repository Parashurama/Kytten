#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/manager.py
# Copyrighted (C) 2013 by "Parashurama"

import weakref
import pyglet
from .glcontext import GuiInternalBuffer, GuiRenderContext
from .base import __int__, GetActiveDialogs, GetObjectfromName


def dummy(*args):
    return None

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

    def AddDialog(self,dialog):
        self._dialogs.add(dialog)

    def Render(self, kytten_buffered=True):

        if   self.is_buffered and kytten_buffered is True :
            self._render(kytten_buffered)
        elif kytten_buffered == 'bypass':
            self._render_from_buffer()
        else:
            self._render_unbuffered()

    def _render(self, fbo_allowed=True):
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
    current_page_id=-1

    PageReference={}
    PageDialogs={}

    @staticmethod
    def UpdateDisplay():
        if PageManager.current_page_id in PageManager.PageReference:
            PageManager.PageReference[ PageManager.current_page_id ]()
            return 1
        #else: raise AttributeError("Page {0} not in __root__".format(PageManager.current_page_id))


    @staticmethod
    def Display(page):
        if not page in PageManager.PageDialogs: raise AttributeError("Page {0} nor Regsitered".format(page))

        for dialog in GetActiveDialogs():
            if not dialog.name in PageManager.PageDialogs[page][0]+['draggable_items']:
                dialog.Hide()

        if page in PageManager.PageDialogs:
            try:
                for element in PageManager.PageDialogs[page][0]:
                    GetObjectfromName(element).Show()
            except AttributeError: raise AttributeError("Show: No Dialog named '{0}' in '{1}'".format(element,page) )

            try:
                for element in PageManager.PageDialogs[page][1]:
                    GetObjectfromName(element).Hide()
            except AttributeError: raise AttributeError("Hide: No Dialog named '{0}' in '{1}'".format(element,page) )


    @staticmethod
    def RegisterPage(page, to_show=[], to_hide=[], function=(dummy, ())):
        PageManager.PageDialogs[page]=( to_show, to_hide, function)


    @staticmethod
    def next_page(*args):
        PageManager.current_page_id+=1
        if not PageManager.UpdateDisplay():
            PageManager.current_page_id-=1

    @staticmethod
    def prev_page(*args):

        PageManager.current_page_id-=1
        if not PageManager.UpdateDisplay():
            PageManager.current_page_id+=1

    @staticmethod
    def goto_page(page):
        PageManager.current_page_id=page
        PageManager.UpdateDisplay()
