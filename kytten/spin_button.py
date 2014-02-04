#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/spin_button.py
# Copyrighted (C) 2013 by "Parashurama"
from __future__ import unicode_literals, print_function

import pyglet

from .button import Button
from .widgets import Control, Label
from .layout import VALIGN_CENTER, HALIGN_CENTER, VerticalLayout, HorizontalLayout

class SpinControlGroup(object):
    def __init__(self, value=None, minv=0.0, maxv=100.0, step=1.0, credit=10, text_style={}):

        if value is None: self.value=(maxv-minv)/2+minv
        else: self.value=value

        self.text_style = text_style
        self.min_value=minv
        self.max_value=maxv
        self.step=step
        self.initial_credit=credit
        self.remaining_credit=credit
        self.members={}
        self.members_list=[]

    def check_total(self, current_member):
        self.remaining_credit = self.initial_credit - sum( ( member.value-initial_value for initial_value, member in zip(self.members.values(), self.members.keys() ) ) )

        if  self.remaining_credit <= 0:
            for member in self.members.keys():
                if not member.isMax:
                    member._northarrow.disable()

        else:
            for member in self.members.keys():
                if not member.isMax:
                    member._northarrow.enable()

    def add(self, member):#Store SpinCTRL initial value
        if not member in self.members:
            self.members[member]=member.value

    def set_credit(self, credit):
        self.initial_credit = int(credit)
        self.reset()

    def reset(self):
        self.remaining_credit=self.initial_credit

        for member in self.members:
            member.set_value(self.members[member])

class SpinButton(Button):
    '''
    A simple text-labeled button.
    '''
    def __init__(self, direction,  text="", name=None, on_click=None, disabled=False):
        self.direction=direction

        Button.__init__(self, name=name, on_click=on_click, disabled=disabled)

    def layout(self, x, y):
        '''
        Places the Button.

        @param x X coordinate of lower left corner
        @param y Y coordinate of lower left corner
        '''
        Control.layout(self, x, y)
        self.button.update(self.x, self.y, self.width, self.height)
        if self.highlight is not None:
            self.highlight.update(self.x, self.y, self.width, self.height)
        x, y, width, height = self.button.get_content_region()

    def size(self, dialog, scale):
        '''
        Sizes the Button.  If necessary, creates the graphic elements.

        @param dialog Dialog which contains the Button
        '''
        if dialog is None:
            return
        Control.size(self, dialog, scale)

        if self.is_pressed:
            if self.direction == 'north': path = ['spinbutton', 'downnortharrow']
            else: path = ['spinbutton', 'downsoutharrow']
        else:
            if self.direction == 'north': path = ['spinbutton', 'upnortharrow']
            else: path = ['spinbutton', 'upsoutharrow']

        if self.is_disabled():
            color = dialog.theme[path]['disabled_color']
        else:
            color = dialog.theme[path]['gui_color']

        if self.button is None:
            self.button = dialog.theme[path]['image'].generate(
                color,
                dialog.batch, dialog.bg_group)

        if self.highlight is None and self.is_highlight():
            self.highlight = dialog.theme[path]['highlight']['image'].generate(
                    dialog.theme[path]['highlight_color'],
                    dialog.batch,
                    dialog.highlight_group)

        self.width, self.height = 8, 7 #self.button.get_needed_size( 0, 0)

    def on_gain_highlight(self):
        '''
        If mouse hovers the button, display highlight
        '''
        Control.on_gain_highlight(self)

        saved_dialog = self.scrollable_parent if self.scrollable_parent is not None else self.saved_dialog

        if self.is_pressed:
            if self.direction == 'north': path = ['spinbutton', 'downnortharrow']
            else: path = ['spinbutton', 'downsoutharrow']
        else:
            if self.direction == 'north': path = ['spinbutton', 'upnortharrow']
            else: path = ['spinbutton', 'upsoutharrow']

        if self.highlight is None and self.is_highlight():
            self.highlight = self.saved_dialog.theme[path]['highlight']['image'].generate(
                color=self.saved_dialog.theme[path]['highlight_color'],
                batch=saved_dialog.batch,
                group=saved_dialog.highlight_group)
            self.highlight.update(self.x, self.y, self.width, self.height)

class SpinControl(HorizontalLayout, Control):
    def __init__(self, name=None, value=None, minv=0.0, maxv=100.0, step=1.0, on_spin=None, ctrlgroup=None, disabled=False, text_style={}, style=None):

        self.control_group=ctrlgroup
        if ctrlgroup:
            self.value     = self.control_group.value
            self.min_value = self.control_group.min_value
            self.max_value = self.control_group.max_value
            self.step      = self.control_group.step
            self.text_style=self.control_group.text_style
            self.control_group.add(self)
        else:
            if value is None: self.value=(maxv-minv)/2+minv
            else: self.value=value

            self.min_value=minv
            self.max_value=maxv
            self.step=step
            self.text_style = text_style

        self.isMin=False
        self.isMax=False

        self._northarrow = SpinButton('north', on_click= self._increment)
        self._southarrow = SpinButton('south', on_click= self._decrement)
        self.label = Label(str(self.value).rjust(2), style =self.text_style )

        HorizontalLayout.__init__(self, [VerticalLayout([self._northarrow,self._southarrow], align=HALIGN_CENTER, padding=3),
                                         self.label
                                        ], align=VALIGN_CENTER, padding=6, name=name )

        self.on_spin_func = self._wrap_method(on_spin)

    def set_value(self, value):
        self.value=value

        self._update()

    def _increment(self, btn):
        if not self.isMax:
            self.value+=self.step

            self._update()

    def _decrement(self, btn):
        if not self.isMin:
            self.value-=self.step

            self._update()

    def _update(self):

        if self.control_group:
            self.control_group.check_total(self)
            self._check_bound_value(False)
        else:
            self._check_bound_value(True)

        self.label.set_text(str(self.value).rjust(2) )

        if self.on_spin_func is not None:
            self.on_spin_func(self.value)

    def _check_bound_value(self, control_group):
        if self.value >= self.max_value:
            self.value = self.max_value
            self.isMax=True

        elif self.value <= self.min_value:
            self.value = self.min_value
            self.isMin=True
        else:
            self.isMin=False
            self.isMax=False



