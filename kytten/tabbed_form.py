#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/tabbed_form.py
# Copyrighted (C) 2013 by "Parashurama"

from __future__ import unicode_literals, print_function, absolute_import, division
from .compat import *

from .button import Button, ButtonStyle, ImageButton
from .togglebutton import ToggleImageButton, ToggleGroup
from .layout import VerticalLayout, HorizontalLayout, HALIGN_LEFT, VALIGN_TOP, ANCHOR_TOP_LEFT
from .widgets import Image
from .scrollable import Scrollable

class TabEntry(object):
    button=None

    def __init__(self, image, content, text=""):
        if   isinstance(image, Image):
            self.button = ToggleImageButton(image, text=text)
        elif isinstance(image, ButtonStyle):
            self.button = ToggleImageButton(style=image, text=text)
        else:
            raise TypeError("")
        self.content=content


class TabbedForm(VerticalLayout):

    def __init__(self, content, width, height, name=None, group=None):
        self._tab_id=-1
        self._tabs = []
        self._content_tabs = []
        self._buttons = HorizontalLayout([], padding=0, align=VALIGN_TOP)
        self._toggle_group = ToggleGroup()
        self._current_tab = None

        for tab in content:
            self.AddTab(tab)

        self._current_tab = self._content_tabs[0]
        self._tab_area = Scrollable(self._current_tab, width, height, is_fixed_size=True, child_anchor=ANCHOR_TOP_LEFT)
        VerticalLayout.__init__(self, [self._buttons, self._tab_area], name=name, group=group, align=HALIGN_LEFT, padding=3)


    def AddTab(self, tab):
        self._tab_id+=1
        btn = tab.button
        btn.tid=self._tab_id
        btn.on_click= btn._wrap_method(self.on_click_tab_button)
        btn.set_toggling_group(self._toggle_group)

        self._buttons.add(btn)
        self._content_tabs.append(tab.content)

    def GetTab(self, tab_index):
        return self._content_tabs[tab_index]

    def on_click_tab_button(self, btn):
        self._tab_area.Hide()
        self._current_tab = self._content_tabs[btn.tid]
        self._tab_area.Show()
        self._tab_area.set_content(self._current_tab)


    def teardown(self):
        for btn in self._buttons:
            btn.on_click=None

        VerticalLayout.teardown(self)
