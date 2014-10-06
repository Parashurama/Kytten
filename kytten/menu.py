#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/menu.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong
# Copyrighted (C) 2013 by "Parashurama"
from __future__ import unicode_literals, print_function

import pyglet
import pyglet.window.key as key

from .base import string_to_unicode
from .widgets import Widget, Control
from .dialog import Dialog
from .frame import Frame
from .layout import GetRelativePoint, VerticalLayout
from .layout import ANCHOR_CENTER, ANCHOR_TOP_LEFT, ANCHOR_BOTTOM_LEFT
from .layout import HALIGN_CENTER
from .layout import VALIGN_TOP, VALIGN_CENTER, VALIGN_BOTTOM
from .override import KyttenLabel, KyttenEventDispatcher
from .scrollable import Scrollable
import inspect

class MenuOption(Control):
    '''
    MenuOption is a choice within a menu.  When selected, it inverts
    (inverted color against text-color background) to indicate that it
    has been chosen.
    '''
    def __init__(self, text="", anchor=ANCHOR_CENTER, menu=None,
                 disabled=False):
        Control.__init__(self, disabled=disabled)
        self.text = string_to_unicode(text)
        self.anchor = anchor
        self.menu = menu
        self.label = None
        self.background = None
        self.highlight = None
        self.is_selected = False
        self.is_multiline = menu.is_multiline
        self.label_width = menu.label_width

    def delete(self):
        if self.label is not None:
            self.label.delete()
            self.label = None

        if self.background is not None:
            self.background.delete()
            self.background = None

        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None

    def expand(self, width, height):
        self.width = width
        self.height = height

    def is_expandable(self):
        return True

    def layout(self, x, y):
        self.x, self.y = x, y

        if self.background is not None:
            self.background.update(x, y, self.width, self.height)

        if self.highlight is not None:
            self.highlight.update(x, y, self.width, self.height)

        font = self.label.document.get_font()
        #height = font.ascent - font.descent
        if not self.is_multiline:
            height = font.ascent - font.descent
        else:
            height = self.label.content_height  - font.descent

        x, y = GetRelativePoint(self, self.anchor,
                                Widget(self.label.content_width, height),
                                self.anchor, (0, 0))
        self.label.x = x
        if not self.is_multiline:
            self.label.y = y - font.descent
        else:
            self.label.y = y + self.height - font.ascent

    def on_gain_highlight(self):
        Control.on_gain_highlight(self)
        saved_dialog = self.scrollable_parent if self.scrollable_parent is not None else self.saved_dialog
        #self.size(saved_dialog)  # to set up the highlight


        if self.is_selected:
            path = ['menuoption', 'selection']
        else:
            path = ['menuoption']

        if self.highlight is None:
            if self.is_highlight():
                self.highlight =  self.saved_dialog.theme[path]['highlight']['image'].generate(
                    color = self.saved_dialog.theme[path]['highlight_color'],
                    batch = saved_dialog.batch,
                    group = saved_dialog.highlight_group)
                self.highlight.update(self.x, self.y, self.menu.width, self.height)

    def on_lose_highlight(self):
        Control.on_lose_highlight(self)

        if self.highlight is not None:
            self.highlight.delete()
            self.highlight = None

    def on_mouse_release(self, x, y, button, modifiers):
        if self.hit_test(x, y):
            self.menu.select(index=self.rid)#self.menu._options.index(self.text))
            return True

    def select(self):
        if self.is_disabled():
            return  # disabled options can't be selected

        self.is_selected = True

        if self.label is not None:
            self.label.delete()
            self.label = None

        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def size(self, dialog, scale):
        if dialog is None:
            return

        Control.size(self, dialog, scale)

        if self.is_selected:
            path = ['menuoption', 'selection']
        else:
            path = ['menuoption']

        if self.label is None:
            if self.is_disabled():
                color = dialog.theme[path]['disabled_color']
            else:
                color = dialog.theme[path]['text_color']
            self.label = KyttenLabel(self.text,
                color=color,
                font_name=dialog.theme[path]['font'],
                font_size=dialog.theme[path]['font_size'],
                batch=dialog.batch,
                group=dialog.fg_group,
                multiline = self.is_multiline,
                width = self.label_width)
            font = self.label.document.get_font()
            self.width = self.label.content_width
            #self.height = font.ascent - font.descent

            if not self.is_multiline:
                self.height = font.ascent - font.descent
            else:
                self.height = self.label.content_height  - font.descent

        if self.background is None:
            if self.is_selected:
                self.background = \
                    dialog.theme[path]['highlight']['image'].generate(
                        dialog.theme[path]['gui_color'],
                        dialog.batch,
                        dialog.bg_group)

        if self.highlight is None:
            if self.is_highlight():
                self.highlight = \
                    dialog.theme[path]['highlight']['image'].generate(
                        dialog.theme[path]['highlight_color'],
                        dialog.batch,
                        dialog.highlight_group)

    def unselect(self):
        self.is_selected = False

        if self.label is not None:
            self.label.delete()
            self.label = None

        if self.background is not None:
            self.background.delete()
            self.background = None

        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def teardown(self):
        self.menu = None
        Control.teardown(self)

class Menu(VerticalLayout):
    '''
    Menu is a VerticalLayout of MenuOptions.  Moving the mouse across
    MenuOptions highlights them; clicking one selects it and causes Menu
    to send an on_click event.
    '''
    def __init__(self, options=[], align=HALIGN_CENTER, padding=4, minwidth=0, minheight=0, is_multiline=False, label_width=0, name=None, on_select=None):
        self.align = align
        self.is_multiline=is_multiline
        self.label_width=label_width
        self.menu_options = []
        self.menu_options_dict = dict()

        self._make_options(options)

        self.on_select =  self._wrap_method(on_select)
        self.selected_index = None

        VerticalLayout.__init__(self, self.menu_options,
                                align=align, minwidth=minwidth, minheight=minwidth, padding=padding, name=name)

    def _make_options(self, options):

        for option in options:
            if option.startswith('-'):
                disabled = True
                option = option[1:]
            else:
                disabled = False

            menu_option=MenuOption(option,
                                       anchor=(VALIGN_CENTER, self.align),
                                       menu=self,
                                       disabled=disabled)

            self.menu_options.append(menu_option)
            self.menu_options_dict[option] = menu_option

        for rid, option in enumerate(self.menu_options):
            option.rid=rid

        self._options = [ option.text for option in self.menu_options ]

    def AddChoices(self,choices):
        self._make_options(choices)

        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def get_value(self):
        if self.selected_index is not None:
            return self.menu_options[self.selected_index].text
        else:
            return None

    def is_input(self):
        return True

    def select(self, text=None, index=None, no_trigger=False):
        if text is not None:

            if not (text in self.menu_options_dict):
                return

            if self.selected_index is not None:
                self.menu_options[self.selected_index].unselect()

            self.selected_index = self._options.index(text)

        elif index is not None:

            text = self.menu_options[index].text

            if self.selected_index is not None:
                self.menu_options[self.selected_index].unselect()

            self.selected_index = index

        else:
            raise ValueError('Must set either text or index to select')

        menu_option = self.menu_options[self.selected_index]
        menu_option.select()

        if self.on_select is not None and no_trigger is False:
            self.on_select(text, index)

    def unselect_choice(self):
        if self.selected_index is not None:
            self.menu_options[self.selected_index].unselect()
            self.selected_index=None

    def set_options(self, options):
        self.delete()
        self.selected_index = None
        self.menu_options = []
        self.menu_options_dict = dict()

        self._make_options(options)

        self.set_content(self.menu_options)

        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def Hide(self):
        VerticalLayout.Hide(self)
        self.unselect_choice()

    def teardown(self):
        self.on_select = None
        VerticalLayout.teardown(self)


class MenuList(Menu, KyttenEventDispatcher):

    def remove_choice(self, text=None, index=None):
        self.unselect_choice()

        if text is not None:
            if not (text in self.menu_options_dict):
                return

            menu_option = self.menu_options_dict.pop(text)
            self.menu_options.remove(menu_option)

        elif index is not None:
            menu_option = self.menu_options.pop(index)
            self.menu_options_dict.pop(menu_option.text)

        else:
            raise ValueError('Must set either text or index to remove')

        self.remove(menu_option)
        menu_option.teardown()

        for rid, option in enumerate(self.menu_options):
            option.rid=rid

        self._options = [ option.text for option in self.menu_options ]

        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def on_key_press(self, symbol, modifiers):
        index = self.selected_index
        last_index = len(self.menu_options)-1
        if   symbol == key.UP:   new_index = index-1 if index is not None else last_index
        elif symbol == key.DOWN: new_index = index+1 if index is not None else 0
        elif symbol == key.ENTER and index is not None: self.select(index=index) ; return pyglet.event.EVENT_HANDLED
        else: return pyglet.event.EVENT_UNHANDLED

        new_index = last_index if (new_index < 0) else (0 if new_index > last_index else new_index)
        self.select(index=new_index, no_trigger=True)
        if self.scrollable_parent is not None :#self.saved_dialog is not None:
            self.scrollable_parent.ensure_visible(self.menu_options[self.selected_index])

        return pyglet.event.EVENT_HANDLED
    '''
    def remove_choice(self, text=None, index=None):

        if not text in self.menu_options_dict:
            return

        menu_option = self.menu_options_dict[text]

        self.remove(menu_option)
        menu_option.teardown()

        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()
    '''

MenuList.register_event_type('on_key_press')


class Dropdown(Control):
    field = None
    label = None
    pulldown_menu = None
    def __init__(self, options=[], selected=None, fixed_width=0,
                 max_height=400, align=VALIGN_TOP, on_select=None,
                 disabled=False, name=None):
        assert options
        assert (selected in options) if selected else True
        Control.__init__(self, disabled=disabled, name=name)
        self.options = options
        self.selected = selected if selected is not None else  options[0]
        self.selected_index = options.index(selected) if selected is not None else 0

        self.on_select =  self._wrap_method(on_select)
        self.fixed_width = fixed_width
        self.max_height = max_height
        self.align = align

    def _delete_pulldown_menu(self):
        if self.pulldown_menu is not None:
            #self.pulldown_menu.window.remove_handlers(self.pulldown_menu)
            self.pulldown_menu.teardown()
            self.pulldown_menu = None

    def delete(self):
        if self.field is not None:
            self.field.delete()
            self.field = None

        if self.label is not None:
            self.label.delete()
            self.label = None

        self._delete_pulldown_menu()

    def get_value(self):
        return self.selected

    def get_index(self):
        return self.selected_index

    def is_input(self):
        return True

    def set_choice(self, choice=None):
        if choice is None: choice = self.options[0]
        assert choice in self.options, ("'{}' not in Menu choices".format(choice),self.options)

        self.selected = choice
        if self.label is not None:
            self.label.delete()
            self.label = None

        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def set_index(self, index):
        index = max(min(index, len(self.options)), 0)
        self.set_choice(self.options[index])

    def on_lose_focus(self):
        Control.on_lose_focus(self)
        # try to delete pulldown menu if it exists
        self._delete_pulldown_menu()

    def on_mouse_release(self, x, y, button, modifiers):
        if self.is_disabled() or not self.hit_test(x, y):
            return

        if self.pulldown_menu is not None:
            self._delete_pulldown_menu()  # if it's already up, close it
            return

        # Setup some callbacks for the dialog
        root = self.saved_dialog.get_root()

        def on_escape(dialog):
            self._delete_pulldown_menu()

        def on_select(dialog, choice, index):
            self.selected = choice
            self.selected_index = index

            if self.label is not None:
                self.label.delete()
                self.label = None

            if self.on_select is not None:
                self.on_select(choice, index)

            self._delete_pulldown_menu()

            if self.saved_dialog is not None:
                self.saved_dialog.set_needs_layout()

            return

        # We'll need the root window to get window size
        width, height = root.window.get_size()

        # Calculate the anchor point and location for the dialog
        if self.align == VALIGN_TOP:
            # Dropdown is at the top, pulldown appears below it
            anchor = ANCHOR_TOP_LEFT
            x = self.x
            y = -(height - self.y - 1)
        else:
            # Dropdown is at the bottom, pulldown appears above it
            anchor = ANCHOR_BOTTOM_LEFT
            x = self.x
            y = self.y + self.height + 1

        # Now to setup the dialog
        self.pulldown_menu = Dialog(
            Frame(
                Scrollable(Menu(options=self.options, on_select=on_select),
                           height=self.max_height),
                path=['dropdown', 'pulldown']
            ),
            window=root.window, batch=root.batch,
            group=root.root_group.parent, theme=root.theme,
            movable=False, anchor=anchor, offset=(x, y), always_on_top=True,
            on_escape=on_escape)

        #root.window.push_handlers(self.pulldown_menu)

    def layout(self, x, y):
        Control.layout(self, x, y)

        self.field.update(x, y, self.width, self.height)
        x, y, width, height = self.field.get_content_region()

        font = self.label.document.get_font()
        height = font.ascent - font.descent
        self.label.x = x
        self.label.y = y - font.descent

    def set_options(self, options, selected=None):
        self.delete()
        self.options = options
        self.selected = selected or self.options[0]

        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def size(self, dialog, scale):
        if dialog is None:
            return

        Control.size(self, dialog, scale)

        if self.is_disabled():
            color = dialog.theme['dropdown']['disabled_color']
        else:
            color = dialog.theme['dropdown']['gui_color']

        if self.field is None:
            self.field = dialog.theme['dropdown']['image'].generate(
                color,
                dialog.batch, dialog.bg_group)
        if self.label is None:
            self.label = KyttenLabel(self.selected,
                font_name=dialog.theme['dropdown']['font'],
                font_size=dialog.theme['dropdown']['font_size'],
                color=dialog.theme['dropdown']['text_color'],
                batch=dialog.batch, group=dialog.fg_group)
        font = self.label.document.get_font()
        height = font.ascent - font.descent
        self.width, self.height = self.field.get_needed_size(
            self.label.content_width, height)

        if self.fixed_width : self.width = max(self.fixed_width, self.width)


    def teardown(self):
        self.on_select = False
        self._delete_pulldown_menu()
        Control.teardown(self)
