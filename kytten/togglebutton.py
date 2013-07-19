#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/toggle_button.py
# Copyrighted (C) 2013 by "Parashurama"

from .button import Button, ImageButton

class ToggleGroup:
    def __init__(self):
        self.members=[]

    def unselect_members(self):
        for member in self.members:
            member.unselect()

    def add(self,member):
        self.members.append(member)

class ToggleButton(Button):
    def __init__(self, text="", toggle=None, name=None, on_click=None, on_gain_hover=None, on_lose_hover=None, disabled=False):
        Button.__init__(self, text=text, name=name, on_click=on_click, on_gain_hover=on_gain_hover, on_lose_hover=on_lose_hover, disabled=disabled)

        if isinstance( toggle, ToggleGroup):
            self.toggling_group = toggle
            self.toggling_group.add(self)

        else: self.toggling_group=None

    def select(self):
        self.is_pressed = True

        # Delete the button to force it to be redrawn
        self.delete()
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def unselect(self):
        self.is_pressed = False

        # Delete the button to force it to be redrawn
        self.delete()
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def on_mouse_press(self, x, y, button, modifiers):

        if self.is_disabled(): return

        if self.toggling_group:
            self.toggling_group.unselect_members()
            self.select()

            if self.on_click is not None:
                self.on_click(self)
        else:
            if self.is_pressed: # Button Down, Toggle it Off
                self.unselect()

            else :  # Button Up, Toggle it On
                self.select()
                if self.on_click is not None and self.hit_test(x, y):
                    self.on_click(self)

    def on_mouse_release(self, x, y, button, modifiers):
        pass

class ToggleImageButton(ImageButton, ToggleButton):
    def __init__(self, image=None, style=None, size=None, text="", toggle=None, name=None, on_click=None, on_gain_hover=None, on_lose_hover=None, disabled=False, square=True):
        ImageButton.__init__(self, image=image, style=style, size=size, text=text, name=name, on_click=on_click, on_gain_hover=on_gain_hover, on_lose_hover=on_lose_hover, disabled=disabled, square=square)

        if isinstance( toggle, ToggleGroup):
            self.toggling_group = toggle
            self.toggling_group.add(self)

        else: self.toggling_group=None

    def on_gain_highlight(self):
        if not self.is_pressed: self.image = self.hover_image
        Button.on_gain_highlight(self)

        self.delete()
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def on_lose_highlight(self):
        Button.on_lose_highlight(self)

        if not self.is_pressed:
            self.image = self.default_image

        self.delete()
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()
