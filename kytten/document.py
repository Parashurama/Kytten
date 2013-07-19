#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/document.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong
# Copyrighted (C) 2013 by "Parashurama"

import pyglet

from .widgets import Control
from .scrollbar import VScrollbar
from .override import KyttenIncrementalTextLayout
from .base import string_to_unicode

class Document(Control):
    """
    Allows you to embed a document within the GUI, which includes a
    vertical scrollbar as needed.
    """
    def __init__(self, document, formatted=False, width=1000, height=5000, name=None,
                 is_fixed_size=False, always_show_scrollbar=False, text_color=None, font=None, font_size=None, group = None):
        """
        Creates a new Document.
        """
        Control.__init__(self, width=width, height=height, name=name, group=group)
        self.max_height = height
        self.content_width = width
        self.document =None

        if isinstance(document, basestring):
            self.set_document(self.create_document(document, formatted))
        else:
            self.set_document(document)

        self.content = None
        self.content_width = width
        self.text_color = text_color
        self.font_size = font_size
        self.font = font
        self.scrollbar = None
        self.scrollbar_to_ensure_visible=None
        self.set_document_style = False
        self.is_fixed_size = is_fixed_size
        self.always_show_scrollbar = always_show_scrollbar
        self.needs_layout = False
        self.link_reference={}

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
        if self.content is not None and self.visible is False:
            self.content.delete()
            self.content = None

        if self.scrollbar is not None:
            self.scrollbar.delete()
            self.scrollbar = None

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
        """
        On updates, we update the scrollbar and then set our view offset
        if it has changed.

        @param dt Time passed since last update event (in seconds)
        """
        if self.scrollbar is not None:
            self.scrollbar.dispatch_event('on_update', dt)

        if self.needs_layout:
            self.needs_layout = False
            self.saved_dialog.set_needs_layout()

    def size(self, dialog):
        if dialog is None:
            return

        Control.size(self, dialog)

        if not self.set_document_style:
            # Set Document Styloe for unformatted Documment
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
            self.scrollbar.size(dialog)
            self.scrollbar.set(self.max_height, self.content.content_height)

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
                if self.saved_dialog is not None:
                    self.saved_dialog.set_needs_layout()

    def set_content_width(self, width):
        self.content_width = width
        if self.content is not None:
            self.content.width = width
        self.needs_layout = True

    def set_text(self, text, formatted=False):

        if self.visible:

            if formatted != self.isFormatted or self.document is None:
                self.set_document(self.create_document(text, formatted))
            else:
                self.document.text = string_to_unicode(text)

            self.needs_layout = True

        else: print("Hidden Document cannot be modified")

    def insert_text(self, start, text, formatted=False):
        if self.visible:
            if self.document:

                text = string_to_unicode(text)

                if formatted is not False:

                    doc = pyglet.text.decode_attributed(text)

                    self.content.begin_update()
                    self.document.insert_text(start, doc.text)
                    for attribute, runlist in doc._style_runs.iteritems():
                        for s, st, value in runlist:
                            self.document.set_style(start+s, start+st, {attribute:value})
                    self.content.end_update()

                else:
                    self.document.insert_text(start, text)

                self.needs_layout = True


        else: print("Hidden Document cannot be modified")

    def append_text(self, text, formatted=False):
        self.insert_text(len(self.document.text), text, formatted)

    def set_links(self, link_reference):
        self.link_reference=link_reference

    def on_mouse_press(self, x, y, *args):

        line = self.content.get_line_from_point(x, y)
        position = self.content.get_position_on_line(line, x)
        CALLBACK = self.document.get_style('link',position)
        if CALLBACK:
            CALLBACK_FUNC = self.link_reference[CALLBACK]
            if not hasattr(CALLBACK_FUNC, '__iter__'):
                CALLBACK_FUNC()
            else:
                for callback_func in CALLBACK_FUNC:
                    callback_func()

    def hit_test(self, x, y):
        """
        True if the given point lies within our area.

        @param x X coordinate of point
        @param y Y coordinate of point
        @returns True if the point is within our area
        """
        if self.scrollbar is not None:
            return x >= self.x and x < self.x + self.width - self.scrollbar.width and \
                   y >= self.y and y < self.y + self.height
        else:
            return x >= self.x and x < self.x + self.width and \
                   y >= self.y and y < self.y + self.height
