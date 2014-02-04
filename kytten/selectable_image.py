#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/widgets.py
# Copyrighted (C) 2013 by "Parashurama"
from __future__ import unicode_literals, print_function

import pyglet

from .widgets import Control, Image
from .base import __int__
from .theme import DefaultTextureGraphicElement

class Selectable(Control, Image):

    def __init__(self, texture,
                       size=None,
                       step0=(None, None),
                       selection_color0=(1.0,1.0,1.0,0.5),
                       step1=(None, None),
                       selection_color1=(1.0,0.0,1.0,0.5),
                       step2=(None, None),
                       selection_color2=(1.0,1.0,0.0,0.5),
                       name=None, on_select=None):

        Image.__init__(self, texture, size, name=name, is_expandable=False)
        Control.__init__(self)
        self.start_position0=None
        self.current_position0=None
        self.start_position1=None
        self.current_position1=None
        self.start_position2=None
        self.current_position2=None

        self.step0=(step0[0] or 1, step0[1] or 1 )
        self.step1=(step1[0] or 1, step1[1] or 1 )
        self.step2=(step2[0] or 1, step2[1] or 1 )

        self.wasDragged=False
        self.selection0=None
        self.selection1=None
        self.selection2=None

        self.texture_sub_rect0=None
        self.texture_sub_rect1=None
        self.texture_sub_rect2=None
        self.rect2_info=None

        self.selection_color0 = selection_color0
        self.selection_color1 = selection_color1
        self.selection_color2 = selection_color2

        self.on_select = self._wrap_method(on_select)

    def on_mouse_press(self, x, y, button, *args):
        if button ==1:
            self.start_position0 = (int(x-self.x)/self.step0[0]*self.step0[0], int(y-self.y)/self.step0[1]*self.step0[1])
            self.current_position0 = None#self.start_position0

        elif button ==4:
            self.start_position1 = (int(x-self.x)/self.step1[0]*self.step1[0], int(y-self.y)/self.step1[1]*self.step1[1])
            self.current_position1 = None#self.start_position1

        elif button ==2:
            self.start_position2 = (int(x-self.x)/self.step2[0]*self.step2[0], int(y-self.y)/self.step2[1]*self.step2[1])
            self.current_position2 = None#self.start_position2

        if button in (1, 2, 4):
            self._force_refresh()

    def on_mouse_release(self, x, y, button, *args):
        if self.on_select is not None: self.on_select(self.texture_sub_rect0, self.texture_sub_rect1, self.texture_sub_rect2 )

    def on_mouse_drag(self, x, y, dx, dy, button, *args):

        if button ==1:
            self.current_position0 = (int(x-self.x)/self.step0[0]*self.step0[0], int(y-self.y)/self.step0[1]*self.step0[1])

        elif button ==4:
            self.current_position1 = (int(x-self.x)/self.step1[0]*self.step1[0], int(y-self.y)/self.step1[1]*self.step1[1])

        elif button ==2:
            self.current_position2 = (int(x-self.x)/self.step2[0]*self.step2[0], int(y-self.y)/self.step2[1]*self.step2[1])

        if button in (1, 2, 4):
            self._force_refresh()
            self.wasDragged=True

        return pyglet.event.EVENT_HANDLED

    def delete_selection0(self):
        if self.selection0 is not None:
            self.selection0.delete()
            self.selection0=None

    def delete_selection1(self):
        if self.selection1 is not None:
            self.selection1.delete()
            self.selection1=None

    def delete_selection2(self):
        if self.selection2 is not None:
            self.selection2.delete()
            self.selection2=None

    def delete(self):
        Image.delete(self)
        self.delete_selection0()
        self.delete_selection1()
        self.delete_selection2()

    def size(self, dialog):
        if self.start_position0 is not None and self.current_position0 is not None:

            x, y, width, height = self.calc_real_selection_rect0()
            self.delete_selection0()
            self.selection0 = DefaultTextureGraphicElement( texture=__int__.BlankTexture, color=self.selection_color0, size=(width, height), position=(x,y),  batch=dialog.batch,  group=dialog.fg_group)

        if self.start_position1 is not None and self.current_position1 is not None:

            x, y, width, height = self.calc_real_selection_rect1()
            self.delete_selection1()
            self.selection1 = DefaultTextureGraphicElement( texture=__int__.BlankTexture, color=self.selection_color1, size=(width, height), position=(x,y),  batch=dialog.batch,  group=dialog.fg_group)

        if self.start_position2 is not None and self.current_position2 is not None:

            x, y, width, height = self.calc_real_selection_rect2()
            self.delete_selection2()
            self.selection2 = DefaultTextureGraphicElement( texture=__int__.BlankTexture, color=self.selection_color2, size=(width, height), position=(x,y),  batch=dialog.batch,  group=dialog.fg_group)

        Image.size(self, dialog)

    def layout(self, x, y):
        Image.layout(self, x, y)

        if self.start_position0 is not None and self.current_position0 is not None:
            x, y, width, height = self.selection_rect0 = self.calc_real_selection_rect0()
            self.selection0.update(x, y, width, height)

            # Sub Texture
            x, y, X, Y = self.calc_sub_texture_rect0()
            self.texture_sub_rect0 = (self.texture,  width, height, x/self.texture.width, y/self.texture.height, X/self.texture.width, Y/self.texture.height)
        else: self.texture_sub_rect0 = None

        if self.start_position1 is not None and self.current_position1 is not None:
            x, y, width, height = self.selection_rect1 = self.calc_real_selection_rect1()
            self.selection1.update(x, y, width, height)

            # Sub Texture
            x, y, X, Y = self.calc_sub_texture_rect1()
            self.texture_sub_rect1 = (self.texture,  width, height, x/self.texture.width, y/self.texture.height, X/self.texture.width, Y/self.texture.height)
        else: self.texture_sub_rect1 = None

        if self.start_position2 is not None and self.current_position2 is not None and self.start_position0 is not None and self.current_position0 is not None:
            x, y, width, height = self.selection_rect2 = self.calc_real_selection_rect2()
            self.selection2.update(x, y, width, height)

            Ox, Oy, OX, OY = self.calc_sub_texture_rect0()
            Ocx = (Ox+ OX)/2.
            Ocy = (Oy+ OY)/2.

            x, y, X, Y = self.calc_sub_texture_rect2()

            self.texture_sub_rect2 = (x-Ocx, y-Ocy, X-Ocx, Y-Ocy)
        else: self.texture_sub_rect2 = None

        if self.wasDragged is True:
            if self.on_select is not None: self.on_select(self.texture_sub_rect0, self.texture_sub_rect1, self.texture_sub_rect2 )
            self.wasDragged=False

    def save_preset(self):
        return   (self.start_position0, self.current_position0,
                  self.start_position1, self.current_position1,
                  self.start_position2, self.current_position2)

    def load_preset(self, preset):
        self.start_position0 = preset[0]
        self.current_position0 = preset[1]
        self.start_position1 = preset[2]
        self.current_position1 = preset[3]
        self.start_position2 = preset[4]
        self.current_position2 = preset[5]
        self.wasDragged=True

        self._force_refresh()

        return preset

    def unselect(self):
        self.start_position0=None
        self.current_position0=None
        self.start_position1=None
        self.current_position1=None
        self.start_position2=None
        self.current_position2=None
        self.selection_rect0=None
        self.selection_rect1=None
        self.selection_rect2=None

        self._force_refresh()

    def calc_real_selection_rect0(self):

        x = min( self.start_position0[0]+self.x, self.current_position0[0]+self.x)
        X = max( self.start_position0[0]+self.x, self.current_position0[0]+self.x)

        y = min( self.start_position0[1]+self.y, self.current_position0[1]+self.y)
        Y = max( self.start_position0[1]+self.y, self.current_position0[1]+self.y)

        return (x, y, X-x+self.step0[0], Y-y+self.step0[1])

    def calc_real_selection_rect1(self):

        x = min( self.start_position1[0]+self.x, self.current_position1[0]+self.x)
        X = max( self.start_position1[0]+self.x, self.current_position1[0]+self.x)

        y = min( self.start_position1[1]+self.y, self.current_position1[1]+self.y)
        Y = max( self.start_position1[1]+self.y, self.current_position1[1]+self.y)

        return (x, y, X-x+self.step1[0], Y-y+self.step1[1])

    def calc_real_selection_rect2(self):

        x = min( self.start_position2[0]+self.x, self.current_position2[0]+self.x)
        X = max( self.start_position2[0]+self.x, self.current_position2[0]+self.x)

        y = min( self.start_position2[1]+self.y, self.current_position2[1]+self.y)
        Y = max( self.start_position2[1]+self.y, self.current_position2[1]+self.y)

        return (x, y, X-x+self.step2[0], Y-y+self.step2[1])

    def calc_sub_texture_rect0(self):

        x = float(min( self.start_position0[0], self.current_position0[0]))
        X = float(max( self.start_position0[0], self.current_position0[0]))

        y = float(min( self.start_position0[1], self.current_position0[1]))
        Y = float(max( self.start_position0[1], self.current_position0[1]))

        return (x, y, X+self.step0[0], Y+self.step0[1])

    def calc_sub_texture_rect1(self):

        x = float(min( self.start_position1[0], self.current_position1[0]))
        X = float(max( self.start_position1[0], self.current_position1[0]))

        y = float(min( self.start_position1[1], self.current_position1[1]))
        Y = float(max( self.start_position1[1], self.current_position1[1]))

        return (x, y, X+self.step1[0], Y+self.step1[1])

    def calc_sub_texture_rect2(self):

        x = float(min( self.start_position2[0], self.current_position2[0]))
        X = float(max( self.start_position2[0], self.current_position2[0]))

        y = float(min( self.start_position2[1], self.current_position2[1]))
        Y = float(max( self.start_position2[1], self.current_position2[1]))

        return (x, y, X+self.step2[0], Y+self.step2[1])
