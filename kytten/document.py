#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/document.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong
# Copyrighted (C) 2013 by "Parashurama"
from __future__ import unicode_literals, print_function

import pyglet

from .widgets import Control, Widget
from .scrollbar import VScrollbar
from .override import KyttenIncrementalTextLayout, KyttenTextLayout
from .base import string_to_unicode, iteritems, FLAGS
from .theme import UntexturedGraphicElement
from .tools import patch_instance_method

class KyttenDocumentError(Exception):pass

class Document(Control):
    '''
    Allows you to embed a document within the GUI, which includes a
    vertical scrollbar as needed.
    '''
    document=None
    content=None
    scrollbar=None
    needs_layout=False
    set_document_style=False
    scrollbar_to_ensure_visible=None
    def __init__(self, document, formatted=False, width=1000, height=5000, name=None,
                 is_fixed_size=False, always_show_scrollbar=False, text_color=None, font=None, font_size=None, group=None):
        '''
        Creates a new Document.
        '''
        Control.__init__(self, width=width, height=height, name=name, group=group)
        self.max_height = height
        self.content_width = width

        try:
            self.set_document(document) #document is a pyglet.text.document.AbstractDocument instance
        except TypeError:
            self.set_document(self.create_document(document, formatted)) # document is string type

        self.font = font
        self.text_color = text_color
        self.font_size = font_size
        self.link_reference={}
        self.content_width = width
        self.is_fixed_size = is_fixed_size
        self.always_show_scrollbar = always_show_scrollbar

    def create_document(self, text, formatted):
        text = string_to_unicode(text)

        if not formatted:                 document = pyglet.text.document.UnformattedDocument(text)
        elif 'attr' in formatted.lower(): document = pyglet.text.decode_attributed(text)
        elif 'html' in formatted.lower(): document = pyglet.text.decode_html(text)

        else: raise TypeError('Unrecognized formattage type')

        self._formatting = formatted

        return document

    def set_document(self, document):
        if not isinstance(document, pyglet.text.document.AbstractDocument):
            raise TypeError('Invalid document type. Require pyglet document instance')

        if self.document is not None:
            if self.content is not None:
                self.content.delete()
                self.content = None

            self.document.delete_text(0, len(self.document.text))

        if isinstance(document, pyglet.text.document.FormattedDocument):
            self.isFormatted = True
        else:
            self.isFormatted =False
        self.set_document_style = False

        self.document = document
        self.document_type = document.__class__

    def _do_set_document_style(self, attr, value):
        length = len(self.document.text)
        runs = [(start, end, doc_value) for start, end, doc_value in
                self.document.get_style_runs(attr).ranges(0, length)
                if doc_value is not None]
        if not runs:
            terminator = len(self.document.text)
        else:
            terminator = runs[0][0]
        self.document.set_style(0, terminator, {attr: value})

    def _get_controls(self):
        controls = []
        if self.scrollbar:
            controls += self.scrollbar._get_controls()
        controls += Control._get_controls(self)
        return controls

    def delete(self):
        Control.delete(self)
        if self.content is not None and (self.visible is False or FLAGS['force_delete'] is True):
            self.content.delete()
            self.content = None

        if self.scrollbar is not None:
            self.scrollbar.delete()
            self.scrollbar = None

    def _hide(self):
        self.visible=False
        self.delete()

    def teardown(self):
        Control.teardown(self)

        if self.document is not None:
            self.document.delete_text(0, len(self.document.text))
            self.document = None

    def do_set_document_style(self, dialog):
        self.set_document_style = True

        # Check the style runs to make sure we don't stamp on anything
        # set by the user
        self._do_set_document_style('color', self.text_color or dialog.theme['text_color'])
        self._do_set_document_style('font_name', self.font or dialog.theme['font'])
        self._do_set_document_style('font_size', self.font_size or dialog.theme['font_size'])

    def get_text(self):
        return self.document.text

    def layout(self, x, y):
        self.x, self.y = x, y

        if self.content is not None:
            self.content.begin_update()
            self.content.x = x
            self.content.y = y

            if self.scrollbar is not None:
                pos = self.scrollbar.get(self.max_height,self.content.content_height)

                if pos != -self.content.view_y:
                    #performance hack (was #self.content.view_y = -pos )
                    #bypass reflowing glyphes
                    pyglet.text.layout.ScrollableTextLayout._set_view_y(self.content, -pos)

                self.scrollbar.layout(x + self.content_width, y)

            self.content.end_update()


    def on_update(self, dt):
        '''
        On updates, we update the scrollbar and then set our view offset
        if it has changed.

        @param dt Time passed since last update event (in seconds)
        '''
        if self.scrollbar is not None:
            self.scrollbar.dispatch_event('on_update', dt)

        if self.needs_layout:
            self.needs_layout = False
            self.saved_dialog.set_needs_layout()

    def _force_refresh(self):
        '''
        Forces recreation of any graphic elements we have constructed.
        Overriden to avoid needlessly recreating pyglet text elements.
        '''
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def size(self, dialog, scale):
        if dialog is None:
            return

        Control.size(self, dialog, scale)
        if not self.set_document_style:
            # Set Document Style for unformatted Documment
            self.do_set_document_style(dialog)

        if self.content is None:
            self.content = KyttenIncrementalTextLayout( self.document,  self.content_width,
                                                        self.max_height, multiline=True,
                                                        batch=dialog.batch, group=dialog.fg_group)

        if self.is_fixed_size or (self.max_height and self.content.content_height > self.max_height):
            self.height = self.max_height
        else:
            self.height = self.content.content_height

        self.content.height = self.height

        if self.always_show_scrollbar or (self.max_height and self.content.content_height > self.max_height):
            if self.scrollbar is None:
                self.scrollbar = VScrollbar(self.max_height)
                #Hack: because self.scrollbar is dialog focus instead of document.
                #TODO: find another way to pass events to scrollbar.
                patch_instance_method(self.scrollbar, "on_mouse_press")(self.on_mouse_press_scrollbar)

            self.scrollbar.size(dialog, scale)
            self.scrollbar.set(self.max_height, self.content.content_height)

        elif self.scrollbar is not None and (self.max_height and self.content.content_height < self.max_height):
            self.scrollbar.delete()
            self.scrollbar = None

        if self.scrollbar is not None:
            self.width = self.content_width + self.scrollbar.width
            if self.scrollbar_to_ensure_visible is not None:
                self.scrollbar.ensure_visible(*self.scrollbar_to_ensure_visible)
                self.scrollbar_to_ensure_visible=None

        else:
            self.width = self.content_width

    def ensure_line_visible(self, line):
        if self.content is not None:

            line = self.content.lines[line]
            if self.scrollbar is not None:
                self.scrollbar.ensure_visible(line.y,line.y+line.ascent-line.descent, line.ascent-line.descent)
            else:
                self.scrollbar_to_ensure_visible = (line.y,line.y+line.ascent-line.descent, line.ascent-line.descent)
                self._force_refresh()

    def set_content_width(self, width):
        self.content_width = width
        if self.content is not None:
            self.content.width = width
        self._force_refresh()

    def set_text(self, text, formatted=False):

        if formatted != self.isFormatted or self.document is None:
            self.set_document(self.create_document(text, formatted))
        else:
            self.document.text = string_to_unicode(text)

        self._force_refresh()#self.saved_dialog.set_needs_layout()#


    def insert_text(self, start, text, formatted=False):

        if self.document is not None:

            text = string_to_unicode(text)

            if formatted is not False:

                doc = pyglet.text.decode_attributed(text)

                if self.visible is True:
                    self.content.begin_update()
                    self.document.insert_text(start, doc.text)
                    for attribute, runlist in iteritems(doc._style_runs):
                        for s, st, value in runlist:
                            self.document.set_style(start+s, start+st, {attribute:value})
                    self.content.end_update()
                else:
                    self.document.insert_text(start, doc.text)
                    for attribute, runlist in iteritems(doc._style_runs):
                        for s, st, value in runlist:
                            self.document.set_style(start+s, start+st, {attribute:value})

            else:
                self.document.insert_text(start, text)

            self.needs_layout = True

    def append_text(self, text, formatted=False):
        '''
        Append Text to the end of the document
        '''
        self.insert_text(len(self.document.text), text, formatted)

    def set_links(self, link_reference):
        self.link_reference.update(link_reference)

    def on_mouse_press(self, x, y, *args):
        line = self.content.get_line_from_point(x, y)
        position = self.content.get_position_on_line(line, x)
        CALLBACK = self.document.get_style('link',position)

        if CALLBACK:
            try:
                CALLBACK_FUNC = self.link_reference[CALLBACK]
            except KeyError:
                raise KyttenDocumentError("In Formatted Document '{}' link reference '{}' is Invalid!".format(self.name, CALLBACK))
            else:
                if not hasattr(CALLBACK_FUNC, '__iter__'):
                    CALLBACK_FUNC()
                else:
                    for callback_func in CALLBACK_FUNC:
                        callback_func()

    def on_mouse_press_scrollbar(self, scrollbar, x, y, *args):
        self.on_mouse_press(x, y, *args)

    def on_gain_focus(self):
        Control.on_gain_focus(self)
        if self.scrollbar is not None and self.saved_dialog is not None:
            self.saved_dialog.set_focus(self.scrollbar)

    def on_lose_highlight(self):
        Control.on_lose_highlight(self)

        if self.scrollbar is not None and self.saved_dialog is not None:
            self.saved_dialog.set_focus(None)

    def hit_test(self, x, y):
        '''
        True if the given point lies within our area.

        @param x X coordinate of point
        @param y Y coordinate of point
        @returns True if the point is within our area
        '''
        if self.scrollbar is not None:
            return x >= self.x and x < self.x + self.width - self.scrollbar.width and \
                   y >= self.y and y < self.y + self.height
        else:
            return x >= self.x and x < self.x + self.width and \
                   y >= self.y and y < self.y + self.height

class RichText(Widget):
    content=None
    document=None
    background=None
    set_document_style = False
    def __init__(self, document, formatted=False, width=None, clamp_height=False, name=None, text_style={}, background_color=None, group=None):
        '''
        Creates a new RichText Widget.
        '''
        Widget.__init__(self, name=name, group=group)
        self.background_color=background_color
        self.content_width = width
        self.clamp_height = clamp_height
        self.text_style = text_style

        try:
            self.set_document(document) #document is a pyglet.text.document.AbstractDocument instance
        except TypeError:
            self.set_document(self.create_document(document, formatted)) # document is string type


    def create_document(self, text, formatted):
        text = string_to_unicode(text)

        if not formatted:                 document = pyglet.text.document.UnformattedDocument(text)
        elif 'attr' in formatted.lower(): document = pyglet.text.decode_attributed(text)
        elif 'html' in formatted.lower(): document = pyglet.text.decode_html(text)

        else: raise TypeError('Unrecognized formattage type')

        self._formatting = formatted

        return document

    def set_document(self, document):
        if not isinstance(document, pyglet.text.document.AbstractDocument):
            raise TypeError('Invalid document type. Require pyglet document instance')

        if self.document is not None:
            if self.content is not None:
                self.content.delete()
                self.content = None

            self.document.delete_text(0, len(self.document.text))

        if isinstance(document, pyglet.text.document.FormattedDocument):
            self.isFormatted = True
        else:
            self.isFormatted =False
        self.set_document_style = False

        self.document = document
        self.document_type = document.__class__

    def _force_refresh(self):
        '''
        Forces recreation of any graphic elements we have constructed.
        Overriden to avoid needlessly recreating pyglet text elements.
        '''
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def do_set_document_style(self, dialog):
        self.set_document_style = True

        # Check the style runs to make sure we don't stamp on anything
        # set by the user
        color     = self.text_style.get('color', None)
        font      = self.text_style.get('font', None)
        font_size = self.text_style.get('font_size', None)

        self._do_set_document_style('color', color or dialog.theme['text_color'])
        self._do_set_document_style('font_name', font or dialog.theme['font'])
        self._do_set_document_style('font_size', font_size or dialog.theme['font_size'])

    def _do_set_document_style(self, attr, value):
        length = len(self.document.text)
        runs = [(start, end, doc_value) for start, end, doc_value in
                self.document.get_style_runs(attr).ranges(0, length)
                if doc_value is not None]
        if not runs:
            terminator = len(self.document.text)
        else:
            terminator = runs[0][0]
        self.document.set_style(0, terminator, {attr: value})

    def layout(self, x, y):
        self.x, self.y = x, y

        if self.content is not None:
            self.content.begin_update()
            self.content.x = x
            self.content.y = y
            self.content.end_update()

        if self.background is not None:
            width = self.content.width if self.content.width is not None else self.width
            height = self.content.height if self.content.height is not None else self.height
            self.background.update(x, y, width, height)

    def size(self, dialog, scale):
        if dialog is None:
            return

        Widget.size(self, dialog, scale)
        if not self.set_document_style:
            # Set Document Style for unformatted Documment
            self.do_set_document_style(dialog)

        if self.content is None:
            clamp_height = self.clamp_height if self.clamp_height is not False else None
            self.content = KyttenTextLayout(self.document, self.content_width, clamp_height, multiline=self.content_width is not None,
                                            clamp_height = self.clamp_height, batch=dialog.batch, group=dialog.fg_group, wrap_lines=True)

        if self.background is None and self.background_color is not None:
            self.background = UntexturedGraphicElement( color=self.background_color,
                                                        batch=dialog.batch,
                                                        group=dialog.bg_group)

        self.height = self.content.height or self.content.content_height
        self.width = self.content.width or self.content.content_width

    def set_content_width(self, width):
        self.content_width = width
        if self.content is not None:
            self.content.width = width
        self._force_refresh()

    def set_text(self, text, formatted=False):

        if formatted != self.isFormatted or self.document is None:
            self.set_document(self.create_document(text, formatted))
        else:
            self.document.text = string_to_unicode(text)

        self._force_refresh()

    def delete(self):
        Widget.delete(self)
        if self.content is not None and (self.visible is False or FLAGS['force_delete'] is True):
            self.content.delete()
            self.content = None

        if self.background is not None:
            self.background.delete()
            self.background=None

    def _hide(self):
        self.visible=False
        self.delete()

    def teardown(self):
        Widget.teardown(self)

        if self.document is not None:
            self.document.delete_text(0, len(self.document.text))
            self.document = None

    def get_text(self):
        return self.document.text

    def check_text_height(self, text, font, max_width):
        def _gen_wrap(glyphs):
            if glyphs:
                for i, glyph in enumerate(glyphs[:-1]):
                    yield i, glyph.advance

                yield i+1, glyphs[-1].width

        width=0
        for i, glyph_width in _gen_wrap(font.get_glyphs(text)):
            width+=glyph_width
            if width >= max_width:
                width -=glyph_width
                return True, i

        return False, 0
