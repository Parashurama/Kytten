#! /usr/bin/env python
# *-* coding: UTF-8 *-*

# kytten/scrollable.py
# Copyrighted (C) 2009 by Conrad "Lynx" Wong
# Copyrighted (C) 2013 by "Parashurama"
from __future__ import unicode_literals, print_function, absolute_import, division
from .compat import *
import pyglet
from pyglet import gl

from .base import Virtual, CVars, minvalue, maxvalue
from .dialog import DialogEventManager
from .frame import Wrapper, GetRelativePoint, ANCHOR_CENTER
from .scrollbar import HScrollbar, VScrollbar
from .widgets import Widget, ScrollableAssert

SCROLLBAR_PADDING = 5

class ScrollableGroup(pyglet.graphics.Group):
    '''
    We restrict what's shown within a Scrollable by performing a scissor
    test.
    '''
    def __init__(self, x, y, width, height, parent=None):
        '''Create a new ScrollableGroup

        @param x X coordinate of lower left corner
        @param y Y coordinate of lower left corner
        @param width Width of scissored region
        @param height Height of scissored region
        @param parent Parent group
        '''
        pyglet.graphics.Group.__init__(self, parent)
        self.x, self.y, self.width, self.height = x, y, width, height
        self._scale = 1.0
        self.was_scissor_enabled = False

    def set_scale(self, scale):
        self._scale = float(scale)

    def set_state(self):
        '''
        Enables a scissor test on our region
        '''
        gl.glPushAttrib(gl.GL_ENABLE_BIT | gl.GL_TRANSFORM_BIT |
                        gl.GL_CURRENT_BIT)
        self.was_scissor_enabled = gl.glIsEnabled(gl.GL_SCISSOR_TEST)
        gl.glEnable(gl.GL_SCISSOR_TEST)
        gl.glScissor(int(self.x), int(self.y),
                     int(self.width), int(self.height))

        if self._scale != 1.0:
            gl.glPushMatrix(gl.GL_MODELVIEW_MATRIX)
            gl.glScalef(self._scale,self._scale,1.0)

    def unset_state(self):
        '''
        Disables the scissor test
        '''
        if self._scale != 1.0:
            gl.glPopMatrix(gl.GL_MODELVIEW_MATRIX)

        if not self.was_scissor_enabled:
            gl.glDisable(gl.GL_SCISSOR_TEST)
        gl.glPopAttrib()

class Scrollable(Wrapper, ScrollableAssert):
    '''
    Wraps a layout or widget and limits it to a maximum, or fixed, size.
    If the layout exceeds the viewable limits then it is truncated and
    scrollbars will be displayed so the user can pan around.
    '''
    def __init__(self, content=None, width=None, height=None,
                 is_fixed_size=False, always_show_scrollbars=False, name=None, child_anchor=ANCHOR_CENTER):
        '''
        Creates a new Scrollable.

        @param content The layout or Widget to be scrolled
        @param width Maximum width, or None
        @param height Maximum height, or None
        @param is_fixed_size True if we should always be at maximum size;
                             otherwise we shrink to match our content
        @param always_show_scrollbars True if we should always show scrollbars
        '''
        if is_fixed_size:
            assert width is not None and height is not None
        Wrapper.__init__(self, content, name=name)
        self.max_width = width
        self.max_height = height
        self.is_fixed_size = is_fixed_size
        self.always_show_scrollbars = always_show_scrollbars
        self.hscrollbar = None
        self.vscrollbar = None
        self.ct_view_width = 0
        self.ct_view_height = 0
        self.content_x = 0
        self.content_y = 0
        self.hscrollbar_height = 0
        self.vscrollbar_width = 0
        self.child_anchor = child_anchor
        self.scale = 1.0

        # We emulate some aspects of Dialog here.  We cannot just inherit
        # from Dialog because pyglet event handling won't allow keyword
        # arguments to be passed through.
        self.theme = None
        self.batch = None
        self.root_group = None
        self.panel_group = None
        self.bg_group = None
        self.fg_group = None
        self.highlight_group = None
        self.needs_layout = False

    def _get_controls(self):
        '''
        We represent ourself as a Control to the Dialog, but we pass through
        the events we receive from Dialog.
        '''
        base_controls = Wrapper._get_controls(self)
        controls = []
        our_left = self.content_x
        our_right = our_left + self.ct_view_width
        our_bottom = self.content_y
        our_top = our_bottom + self.ct_view_height
        for control, left, right, top, bottom in base_controls:
            controls.append((control,
                             max(left, our_left),
                             min(right, our_right),
                             min(top, our_top),
                             max(bottom, our_bottom)))
        if self.hscrollbar is not None:
            controls += self.hscrollbar._get_controls()
        if self.vscrollbar is not None:
            controls += self.vscrollbar._get_controls()
        return controls

    def delete(self):
        '''
        Delete all graphical elements associated with the Scrollable
        '''
        Wrapper.delete(self)
        if self.hscrollbar is not None:
            self.hscrollbar.delete()
            self.hscrollbar = None
        if self.vscrollbar is not None:
            self.vscrollbar.delete()
            self.vscrollbar = None

    def teardown(self):
        Wrapper.teardown(self)
        self.root_group = None
        self.panel_group = None
        self.bg_group = None
        self.fg_group = None
        self.highlight_group = None

    def ensure_visible(self, control):
        '''
        Make sure a control is visible.
        '''
        offset_x = 0
        if self.hscrollbar:
            offset_x = self.hscrollbar.get(self.ct_view_width, self.content.width)

        offset_y = 0
        if self.vscrollbar:
            offset_y = self.content.height - self.ct_view_height -  self.vscrollbar.get(self.ct_view_height, self.content.height)

        control_left = control.x - self.content_x - offset_x
        control_right = control_left + control.width
        control_bottom = control.y - self.content_y + offset_y
        control_top = control_bottom + control.height

        if self.hscrollbar is not None:
            self.hscrollbar.ensure_visible(control_left, control_right, max(self.ct_view_width, self.content.width))

        if self.vscrollbar is not None:
            self.vscrollbar.ensure_visible(control_top, control_bottom, max(self.ct_view_height, self.content.height))

    def expand(self, width, height):
        if self.content.is_expandable(): #if self.Xscrollbar is None : self.Xscrollbar_dim is 0
            self.ct_view_width = width - self.vscrollbar_width
            self.ct_view_height = height - self.hscrollbar_height

            self.content.expand(max(self.ct_view_width, self.content.width),
                                max(self.ct_view_height, self.content.height))
        self.width, self.height = width, height

    def get_root(self):
        if self.saved_dialog is not None:
            return self.saved_dialog.get_root()
        else:
            return self

    def hit_test(self, x, y):
        '''
        We only intercept events for the content region, not for
        our scrollbars.  They can handle themselves!
        '''
        return x >= self.content_x and y >= self.content_y and \
               x < self.content_x + self.ct_view_width and \
               y < self.content_y + self.ct_view_height

    def is_expandable(self, dim=None):
        return True

    def layout(self, x, y):
        '''
        Reposition the Scrollable

        @param x X coordinate of lower left corner
        @param y Y coordinate of lower left corner
        '''
        self.x, self.y = x, y

        virtual_content = Virtual(width=self.ct_view_width, height=self.ct_view_height)

        if self.content is not None:
            cx, cy = GetRelativePoint(  self, self.child_anchor,
                                        virtual_content, None, (0,0))

        valign_anchor, halign_anchor = self.child_anchor

        # Work out the adjusted content width and height
        if self.hscrollbar is not None:
            self.hscrollbar.layout(x, y)
            if   valign_anchor == CVars.VALIGN_BOTTOM:
                cy += self.hscrollbar.height + SCROLLBAR_PADDING
            elif valign_anchor == CVars.VALIGN_CENTER:
                cy += self.hscrollbar.height//2 + SCROLLBAR_PADDING

        if self.vscrollbar is not None:

            if   halign_anchor == CVars.HALIGN_RIGHT:
                cx -= self.vscrollbar.width + SCROLLBAR_PADDING
            elif halign_anchor == CVars.HALIGN_CENTER:
                cx -= self.vscrollbar.width//2 + SCROLLBAR_PADDING

            self.vscrollbar.layout( self.x + self.width - self.vscrollbar.width,
                                    self.y + self.hscrollbar_height)

        # Work out the content layout
        self.content_x, self.content_y = cx, cy
        left = cx

        top = cy + self.ct_view_height - self.content.height*self.scale

        if self.hscrollbar is not None:
            left -= self.hscrollbar.get(self.ct_view_width,
                                        self.content.width*self.scale)
        if self.vscrollbar is not None:
            top += self.vscrollbar.get(self.ct_view_height,
                                       self.content.height*self.scale)

        # Set the scissor group
        self.root_group.x, self.root_group.y = cx, cy
        self.root_group.width = self.ct_view_width + 1
        self.root_group.height = self.ct_view_height + 1

        left/=self.scale
        top/=self.scale

        self.content.layout(int(left), int(top))

        self.needs_layout = False

    def on_update(self, dt):
        '''
        On updates, we redo the layout if scrollbars have changed position

        @param dt Time passed since last update event (in seconds)
        '''
        if self.needs_layout:
            width, height = self.width, self.height
            self.size(self.saved_dialog, self.scale)
            self.expand(width, height)
            self.layout(self.x, self.y)

    def set_needs_layout(self):
        self.needs_layout = True
        if self.saved_dialog is not None:
            self.saved_dialog.set_needs_layout()

    def set_wheel_hint(self, control):
        if self.saved_dialog is not None:
            self.saved_dialog.set_wheel_hint(control)

    def set_wheel_target(self, control):
        if self.saved_dialog is not None:
            self.saved_dialog.set_wheel_target(control)

    def set_scale(self, scale):
        self.scale = scale

    def size(self, dialog, scale):
        '''
        Recalculate the size of the Scrollable.

        @param dialog Dialog which contains us
        '''
        if dialog is None:
            return
        Widget.size(self, dialog, self.scale)

        if self.hscrollbar is not None:
            self.hscrollbar_height = dialog.theme['hscrollbar']['left']['image'].height + SCROLLBAR_PADDING
        else:
            self.hscrollbar_height = 0

        if self.hscrollbar is not None:
            self.vscrollbar_width = dialog.theme['vscrollbar']['up']['image'].width + SCROLLBAR_PADDING
        else:
            self.vscrollbar_width = 0

        if self.root_group is None: # do we need to re-clone dialog groups?
            self.theme = dialog.theme
            self.batch = dialog.batch
            self.root_group = ScrollableGroup(0, 0, self.width, self.height, parent=dialog.fg_group)
            self.panel_group = pyglet.graphics.OrderedGroup( 0, self.root_group)
            self.bg_group    = pyglet.graphics.OrderedGroup( 1, self.root_group)
            self.fg_group    = pyglet.graphics.OrderedGroup( 2, self.root_group)
            self.highlight_group = pyglet.graphics.OrderedGroup( 3, self.root_group)
            Wrapper.delete(self)  # force children to abandon old groups

        self.root_group.set_scale(self.scale)

        Wrapper.size(self, self, self.scale)  # all children are to use our groups


        if self.always_show_scrollbars or (self.max_width and self.width*self.scale > self.max_width):
            if self.hscrollbar is None:
                self.hscrollbar = HScrollbar(self.max_width)
        else:
            if self.hscrollbar is not None:
                self.hscrollbar.delete()
                self.hscrollbar = None

        if self.always_show_scrollbars or (self.max_height and self.height*self.scale > self.max_height):
            if self.vscrollbar is None:
                self.vscrollbar = VScrollbar(self.max_height)
        else:
            if self.vscrollbar is not None:
                self.vscrollbar.delete()
                self.vscrollbar = None

        self.ct_view_width  = minvalue(self.max_width, self.width*self.scale)
        self.ct_view_height = minvalue(self.max_height, self.height*self.scale)

        if self.is_fixed_size:
            self.width, self.height = self.max_width, self.max_height
            max_width, max_height = self.max_width, self.max_height
        else:
            self.width = max_width = minvalue(self.max_width, self.content.width*self.scale)
            self.height = max_height = minvalue(self.max_height, self.content.height*self.scale)

        if self.hscrollbar is not None:
            self.hscrollbar.size(dialog, scale)
            self.hscrollbar.set(self.ct_view_width, max(self.content.width*self.scale, max_width ))
            self.height += self.hscrollbar.height + SCROLLBAR_PADDING

        if self.vscrollbar is not None:
            self.vscrollbar.size(dialog, scale)
            self.vscrollbar.set(self.ct_view_height, max(self.content.height*self.scale, max_height))
            self.width += self.vscrollbar.width + SCROLLBAR_PADDING
            self.height = max(self.height, self.vscrollbar.height + self.hscrollbar_height )

