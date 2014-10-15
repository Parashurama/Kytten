#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/input.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong
# Copyrighted (C) 2013 by "Parashurama"
from __future__ import unicode_literals, print_function
import re

import pyglet
import pyglet.window.key as key
from .widgets import Control
from .override import KyttenIncrementalTextLayout, KyttenCaret, KyttenLabel
from .base import string_to_unicode
from . import pyperclip

class Input(Control):
    '''
    A text input field.
    '''
    document_style_set = False
    text_layout = None
    caret = None
    field = None
    highlight = None
    restricted = None
    def __init__(self, text="", length=20, max_length=None, padding=0,
                 on_input=None, name=None, disabled=False, restricted=None, group=None):
        Control.__init__(self, name=name, disabled=disabled, group=group)
        self.text = string_to_unicode(text)
        self.length = int(length)
        self.max_length = int(max_length) if max_length is not None else None
        self.padding = int(padding)
        self.on_input = self._wrap_method(on_input)
        self.document = pyglet.text.document.UnformattedDocument(text)
        self.label = None
        self.restricted = set(restricted) if restricted is not None else self.restricted

    def delete(self):
        Control.delete(self)
        if self.caret is not None:
            self.caret.delete()
            self.caret = None

        if self.text_layout is not None and not self.is_focus():
            self.document.remove_handlers(self.text_layout)
            self.text_layout.delete()
            self.text_layout = None

        if self.label is not None:
            self.label.delete()
            self.label = None

        if self.field is not None:
            self.field.delete()
            self.field = None

        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None

    def _force_refresh(self):
        '''
        Forces recreation of any graphic elements we have constructed.
        Overriden to avoid needlessly recreating pyglet text elements.
        '''
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def disable(self):
        Control.disable(self)
        self.document_style_set = False

    def enable(self):
        Control.enable(self)
        self.document_style_set = False

    def get_text(self):
        return self.document.text

    def get_value(self):
        return self.get_text()

    def is_focusable(self):
        return True

    def is_input(self):
        return True

    def layout(self, x, y):
        self.x, self.y = x, y
        self.field.update(x, y, self.width, self.height)
        if self.highlight is not None:
            self.highlight.update(x, y, self.width, self.height)

        x, y, width, height = self.field.get_content_region()
        if self.is_focus():
            self.text_layout.begin_update()
            self.text_layout.x = x + self.padding
            self.text_layout.y = y + self.padding
            self.text_layout.end_update()

        else:  # Transform Text input in Label if not focus
            # Adjust the text for font's descent
            descent = self.document.get_font().descent
            self.label.begin_update()
            self.label.x = x + self.padding
            self.label.y = y + self.padding - descent
            self.label.end_update()

    def on_gain_highlight(self):
        Control.on_gain_highlight(self)
        self.set_highlight()

    def on_gain_focus(self):
        Control.on_gain_focus(self)
        Control._force_refresh(self) # needs full refresh to create label and input as needed

    def on_key_press(self, symbol, modifiers):

        if self.text_layout is not None:
            if   symbol == key.C and (modifiers & key.MOD_CTRL):
                pyperclip.copy(self.text_layout.get_selection_text())
                return pyglet.event.EVENT_HANDLED

            elif symbol == key.V and (modifiers & key.MOD_CTRL):
                clipboad_content = pyperclip.paste()
                if clipboad_content is not None:
                    self.on_text(clipboad_content)
                    self._force_refresh()
                    return pyglet.event.EVENT_HANDLED

            elif symbol == key.X and (modifiers & key.MOD_CTRL):
                pyperclip.copy(self.text_layout.get_selection_text())
                start, end = self.text_layout.get_selection()
                self.document.delete_text(start, end )
                self.text_layout.set_selection(start,start)
                self.caret.mark = self.caret.position = start
                self._force_refresh()
                return pyglet.event.EVENT_HANDLED

            elif symbol == key.A and (modifiers & key.MOD_CTRL):
                self.text_layout.select_all()
                self._force_refresh()
                return pyglet.event.EVENT_HANDLED

    def on_lose_focus(self):
        Control.on_lose_focus(self)
        Control._force_refresh(self) # needs full refresh to create label and input as needed

        if self.on_input is not None:
            if self.name is not None:
                self.on_input(self.name, self.get_text())
            else:
                self.on_input(self.get_text())

    def on_lose_highlight(self):
        Control.on_lose_highlight(self)
        self.remove_highlight()

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if not self.is_disabled() and self.caret is not None:
            return self.caret.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_press(self, x, y, button, modifiers):
        if not self.is_disabled() and self.caret is not None:
            return self.caret.on_mouse_press(x, y, button, modifiers)

    def on_text(self, text):

        if not self.is_disabled() and self.caret is not None:

            if self.restricted is not None:
                if not text in self.restricted:
                    if len(text)>1:
                        text = ''.join(char for char in text if char in self.restricted)
                    else:
                        return pyglet.event.EVENT_HANDLED

            self.text_layout.begin_update()

            self.caret.on_text(text)
            if self.max_length and len(self.document.text) > self.max_length:
                self.document.delete_text(self.max_length, len(self.document.text))

            self.text_layout.end_update()

            return pyglet.event.EVENT_HANDLED

    def on_text_motion(self, motion):
        if not self.is_disabled() and self.caret is not None:
            return self.caret.on_text_motion(motion)

    def on_text_motion_select(self, motion):
        if not self.is_disabled() and self.caret is not None:
            return self.caret.on_text_motion_select(motion)

    def remove_highlight(self):
        if not self.is_highlight() and not self.is_focus():
            if self.highlight is not None:
                self.highlight.delete()
                self.highlight = None

    def set_highlight(self):
        saved_dialog = self.scrollable_parent if self.scrollable_parent is not None else self.saved_dialog
        path = ['input', 'highlight']
        if self.highlight is None:
            self.highlight = self.saved_dialog.theme[path]['image'].generate(
                color=self.saved_dialog.theme[path]['highlight_color'],
                batch=saved_dialog.batch,
                group=saved_dialog.highlight_group)
            self.highlight.update(self.x, self.y, self.width, self.height)

    def set_text(self, text):
        self.document.text = string_to_unicode(text)
        if self.caret is not None:
            self.caret.mark = self.caret.position = len(self.document.text)
        elif self.label  is not None:
            self.label.text = text

        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def size(self, dialog, scale):
        if dialog is None:
            return

        Control.size(self, dialog, scale)

        if self.is_disabled():
            color = dialog.theme['input']['disabled_color']
        else:
            color = dialog.theme['input']['text_color']

        # We set the style once.  We shouldn't have to do so again because
        # it's an UnformattedDocument.
        if not self.document_style_set:
            self.document.set_style(0, len(self.document.text),
                                    dict(color=color,
                                         font_name=dialog.theme['font'],
                                         font_size=dialog.theme['font_size']))
            self.document_style_set = True

        # Calculate the needed size based on the font size
        font = self.document.get_font(0)
        height = font.ascent - font.descent
        glyphs = font.get_glyphs('A_')
        width = max([x.width for x in glyphs])
        needed_width = self.length * width + 2 * self.padding
        needed_height = height + 2 * self.padding

        if self.is_focus():
            if self.text_layout is None:
                self.text_layout = KyttenIncrementalTextLayout( self.document, needed_width, needed_height,
                                                                multiline=False,
                                                                batch=dialog.batch, group=dialog.fg_group)
                assert self.caret is None
            assert self.label is None
            if self.caret is None:
                self.caret = KyttenCaret( self.text_layout, color=dialog.theme['input']['gui_color'][0:3])
                self.caret.visible = True
                self.caret.mark = self.caret.position = 0

        else: # Transform Text input in Label if not focus
            if self.label is None:
                self.label = KyttenLabel(self.document.text[:get_text_slice(font, self.document.text, needed_width-self.padding*2)],
                                              font_size=self.document.styles['font_size'],
                                              font_name=self.document.styles['font_name'],
                                              multiline=False,
                                              width=self.width-self.padding*2,
                                              color=color,
                                              batch=dialog.batch,
                                              group=dialog.fg_group)

            assert self.text_layout is None and self.caret is None

        if self.field is None:
            if self.is_disabled():
                color = dialog.theme['input']['disabled_color']
            else:
                color = dialog.theme['input']['gui_color']

            self.field = dialog.theme['input']['image'].generate(color=color, batch=dialog.batch, group=dialog.bg_group)

        if self.highlight is None and self.is_highlight():
            self.set_highlight()

        self.width, self.height = self.field.get_needed_size(needed_width, needed_height)

    def teardown(self):
        self.on_input = False
        Control.teardown(self)

        if self.text_layout is not None:
            self.document.remove_handlers(self.text_layout)
            self.text_layout.delete()
            self.text_layout = None
            self.document=None

class MultilineInput(Input):

    def __init__(self, text="", width=200, height = 100, padding=0,
                 on_input=None, on_tabulation=None, auto_complete=None, name=None, disabled=False, group=None):

        Control.__init__(self, name=name, disabled=disabled, group=group)
        self.text = string_to_unicode(text)
        self.content_width = width
        self.content_height = height

        self.padding = padding
        self.on_input = self._wrap_method(on_input)
        self.document = pyglet.text.document.UnformattedDocument(self.text)

        self._auto_complete_func = self._wrap_method(auto_complete)
        self._tabulation_func   = self._wrap_method(on_tabulation)

    def set_text(self, text):
        self.document.text = string_to_unicode(text)
        if self.caret:
            self.caret.mark = self.caret.position = len(self.document.text)

        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def on_text(self, text):
        if not self.is_disabled() and self.caret is not None:
            self.caret.on_text(text)
            if self._auto_complete_func is not None:
                self.get_auto_complete()
            return pyglet.event.EVENT_HANDLED

    def on_text_motion(self, motion):
        if not self.is_disabled() and self.caret is not None:
            self.caret.on_text_motion(motion)
            if self._auto_complete_func is not None:
                if motion == key.MOTION_BACKSPACE:
                    self.get_auto_complete()
                else:
                    self.get_auto_complete(False)

            return pyglet.event.EVENT_HANDLED
        return pyglet.event.EVENT_HANDLED

    _last_word_re = re.compile(r'(\w+)\Z')

    def get_auto_complete(self, autocomplete=True):
        #caret.py line 462
        if self.caret is not None:
            pos = self.caret._position
            text = self.caret._layout.document.text
            match = self._last_word_re.search(text, 0, pos)

            if not match or not autocomplete:
                return self._auto_complete_func(None, (0,0))

            word = text[ match.start(): match.end()]
            line = self.caret._layout.get_line_from_position(match.start())
            position = x, y = self.caret._layout.get_point_from_position(match.start(), line)

            self._auto_complete_func(word, position)

    def on_auto_complete(self, word):
        if self.caret is not None:
            pos = self.caret._position
            text = self.caret._layout.document.text
            match = self._last_word_re.search(text, 0, pos)
            if match is not None:
                old_word = match.group(1)
                self.caret.on_text(word[len(old_word):])

    def on_key_press(self, symbol, modifiers):
        if symbol == key.TAB and self._tabulation_func is not None:
            return self._tabulation_func()
        return Input.on_key_press(self, symbol, modifiers)

    def on_gain_focus(self):
        Input.on_gain_focus(self)
        if self.saved_dialog is not None:
            self.saved_dialog.set_wheel_target(self)

    def on_lose_focus(self):
        Control.on_lose_focus(self)

        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()
            self.saved_dialog.release_wheel_target()

        if self.text_layout is not None:
            self.text_layout.set_selection(0,0)

        if self.caret is not None:
            self.caret.delete()
            self.caret=None

        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None

        if self.on_input is not None:
            self.on_input(self.get_text())

    def on_mouse_scroll(self, x, y, scroll_x, scroll_y):
        if self.caret is not None and self.hit_test(x, y):
            self.caret.on_mouse_scroll(x, y, scroll_x, scroll_y)
            return pyglet.event.EVENT_HANDLED

    def delete(self):
        Control.delete(self)
        if self.caret is not None:
            self.caret.delete()
            self.caret = None

        if self.text_layout is not None and not self.visible:
            self.document.remove_handlers(self.text_layout)
            self.text_layout.delete()
            self.text_layout = None

        if self.field is not None:
            self.field.delete()
            self.field = None

        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None

    def layout(self, x, y):
        self.x, self.y = x, y
        self.field.update(x, y, self.width, self.height)
        if self.highlight is not None:
            self.highlight.update(x, y, self.width, self.height)

        x, y, width, height = self.field.get_content_region()

        self.text_layout.begin_update()
        self.text_layout.x = x + self.padding
        self.text_layout.y = y + self.padding
        self.text_layout.end_update()

    def size(self, dialog, scale):
        if dialog is None:
            return
        Control.size(self, dialog, scale)

        if self.is_disabled():
            color = dialog.theme['input']['disabled_color']
        else:
            color = dialog.theme['input']['text_color']

        # We set the style once.  We shouldn't have to do so again because
        # it's an UnformattedDocument.
        if not self.document_style_set:
            self.document.set_style(0, len(self.document.text),
                                    dict(color=color,
                                         font_name=dialog.theme['font'],
                                         font_size=dialog.theme['font_size']))
            self.document_style_set = True

        if self.text_layout is None:
            self.text_layout = KyttenIncrementalTextLayout( self.document, self.content_width,
                                                            self.content_height, multiline=True,
                                                            batch=dialog.batch, group=dialog.fg_group)
            assert self.caret is None

        if self.caret is None and self.is_focus():
            self.caret = KyttenCaret(
                self.text_layout,
                batch=dialog.batch,
                color=dialog.theme['input']['gui_color'][0:3])

            self.caret.visible = True
            self.caret.mark = 0
            self.caret.position = len(self.document.text)

        if self.field is None:
            if self.is_disabled():
                color = dialog.theme['input']['disabled_color']
            else:
                color = dialog.theme['input']['gui_color']
            self.field = dialog.theme['input']['image'].generate(
                color=color,
                batch=dialog.batch,
                group=dialog.bg_group)

        if self.highlight is None and self.is_highlight():
            self.set_highlight()

        self.width, self.height = self.field.get_needed_size(self.content_width, self.content_height)


MultilineInput.register_event_type('on_auto_complete')


def get_text_slice(font, text, max_width):
    width = 0
    for i, g in enumerate(font.get_glyphs(text)):
        if width >= max_width:
            return i-1
        width += g.advance # glyph advance is glyph width + trailing space
    return None # full slice
