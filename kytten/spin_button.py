#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/spin_button.py
# Copyrighted (C) 2013 by "Parashurama"

import pyglet

from .button import Button
from .widgets import Control, Label
from .layout import VALIGN_CENTER, HALIGN_CENTER, VerticalLayout, HorizontalLayout

class SpinControlGroup(object):
    def __init__(self, value=None, min=0.0, max=100.0, step=1.0, credit=10, text_style=None):

        if value is None: self.value=(max-min)/2+min
        else: self.value=value

        self.text_style = text_style
        self.min_value=min
        self.max_value=max
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
                    member.northarrow.disable()

        else:
            for member in self.members.keys():
                if not member.isMax:
                    member.northarrow.enable()

    def add(self, member):#Store SpinCTRL initial value
        if not member in self.members:
            self.members[member]=member.value

    def ResetAll(self):
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

    def size(self, dialog):
        '''
        Sizes the Button.  If necessary, creates the graphic elements.

        @param dialog Dialog which contains the Button
        '''
        if dialog is None:
            return
        Control.size(self, dialog)

        if self.is_pressed:
            if self.direction == 'north': path = ['spinbutton2', 'downnortharrow']
            else: path = ['spinbutton2', 'downsoutharrow']
        else:
            if self.direction == 'north': path = ['spinbutton2', 'upnortharrow']
            else: path = ['spinbutton2', 'upsoutharrow']

        if self.is_disabled():
            color = dialog.theme[path]['disabled_color']
        else:
            color = dialog.theme[path]['gui_color']

        if self.button is None:
            self.button = dialog.theme[path]['image'].generate(
                color,
                dialog.batch, dialog.bg_group)

        if self.highlight is None and self.is_highlight():
            self.highlight = dialog.theme[path]['highlight']['image'].\
                generate(dialog.theme[path]['highlight_color'],
                         dialog.batch,
                         dialog.bg_group)

        self.width, self.height = 8, 7 #self.button.get_needed_size( 0, 0)

class SpinControl(HorizontalLayout, Control):
    def __init__(self, name=None, value=None, min=0.0, max=100.0, step=1.0, on_spin=None, ctrlgroup=None, disabled=False, style=None):

        self.control_group=ctrlgroup
        if ctrlgroup:
            self.value     = self.control_group.value
            self.min_value = self.control_group.min_value
            self.max_value = self.control_group.max_value
            self.step      = self.control_group.step
            self.text_style=self.control_group.text_style
            self.control_group.add(self)
        else:
            if value is None: self.value=(max-min)/2+min
            else: self.value=value

            self.min_value=min
            self.max_value=max
            self.step=step
            self.text_style = text_style

        self.isMin=False
        self.isMax=False

        self.northarrow = SpinButton('north', on_click= self.increment)
        self.southarrow = SpinButton('south', on_click= self.decrement)
        self.label = Label(str(self.value).rjust(2, ' '), style =self.text_style )

        HorizontalLayout.__init__(self, [VerticalLayout([self.northarrow,self.southarrow], align=HALIGN_CENTER, padding=3),
                                                self.label
                                                ], align=VALIGN_CENTER, padding=6, name=name )

        if on_spin: self.set_handler('on_spin',on_spin)

    def increment(self, *args):
        if not self.isMax:
            self.value+=self.step
            if self.control_group:
                self.control_group.check_total(self)
                self.check_bound_value(False)
            else:
                self.check_bound_value(True)

            self.label.set_text(str(self.value).rjust(2, ' ') )
            self.dispatch_event('on_spin', self)

    def decrement(self, *args):
        if not self.isMin:
            self.value-=self.step
            if self.control_group:
                self.control_group.check_total(self)
                self.check_bound_value(False)
            else:
                self.check_bound_value(True)

            self.label.set_text(str(self.value).rjust(2, ' ') )
            self.dispatch_event('on_spin', self)

    def disable_south(self):
        self.southarrow.disable()
    def disable_north(self):
        self.northarrow.disable()

    def check_bound_value(self, control_group):
        if self.value >= self.max_value:
            self.value = self.max_value
            self.isMax=True

        elif self.value <= self.min_value:
            self.value = self.min_value
            self.isMin=True
        else:
            self.isMin=False
            self.isMax=False

    def on_spin(self, *args):
        return pyglet.event.EVENT_HANDLED

    def set_value(self, value):
        self.value=value

        if self.control_group:
            self.control_group.check_total(self)
            self.check_bound_value(False)
        else:
            self.check_bound_value(True)

        self.label.set_text(str(self.value).rjust(2, ' ') )
        self.dispatch_event('on_spin', self)

SpinControl.register_event_type('on_spin')
